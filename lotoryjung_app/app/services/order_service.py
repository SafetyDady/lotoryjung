"""
Order service for handling lottery orders
"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import datetime, date
import pytz

from app import db
from app.models import Order, OrderItem, Rule, BlockedNumber, NumberTotal, AuditLog
from app.utils.number_utils import (
    normalize_number, canonicalize_tote, validate_number_format,
    calculate_payout, generate_order_number, calculate_lottery_period,
    generate_batch_id, parse_amount
)

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class OrderValidationError(Exception):
    """Custom exception for order validation errors"""
    pass

class OrderService:
    """Service class for order operations"""
    
    @staticmethod
    def validate_order_item(field: str, number: str, amount: str, batch_id: str) -> Dict:
        """
        Validate a single order item
        
        Args:
            field: Field type (2_top, 2_bottom, 3_top, tote)
            number: Number to buy
            amount: Amount to buy
            batch_id: Current batch ID
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Validate number format
        is_valid, error_msg = validate_number_format(number, field)
        if not is_valid:
            errors.append(error_msg)
            return {'valid': False, 'errors': errors}
        
        # Normalize number
        number_norm = normalize_number(number, field)
        
        # Parse amount
        buy_amount = parse_amount(amount)
        if buy_amount is None:
            errors.append("จำนวนเงินไม่ถูกต้อง")
            return {'valid': False, 'errors': errors}
        
        if buy_amount <= 0:
            errors.append("จำนวนเงินต้องมากกว่า 0")
            return {'valid': False, 'errors': errors}
        
        # Check if number is blocked
        blocked = BlockedNumber.query.filter_by(
            field=field,
            number_norm=number_norm,
            is_active=True
        ).first()
        
        if blocked:
            errors.append(f"เลข {number_norm} ในประเภท {field} ถูกอั้น: {blocked.reason or 'ไม่ระบุเหตุผล'}")
            return {'valid': False, 'errors': errors, 'is_blocked': True}
        
        # Get payout rate
        payout_rule = Rule.query.filter_by(
            rule_type='payout',
            field=field,
            is_active=True
        ).first()
        
        if not payout_rule:
            errors.append(f"ไม่พบอัตราจ่ายสำหรับประเภท {field}")
            return {'valid': False, 'errors': errors}
        
        payout_rate = float(payout_rule.value)
        potential_payout = calculate_payout(buy_amount, payout_rate)
        
        # Check limit
        limit_exceeded, current_total, limit_amount = OrderService._check_limit(
            field, number_norm, buy_amount, batch_id
        )
        
        if limit_exceeded:
            errors.append(f"เลข {number_norm} เกินลิมิต: ปัจจุบัน {current_total:,.2f} + {buy_amount:,.2f} > {limit_amount:,.2f}")
            return {'valid': False, 'errors': errors, 'limit_exceeded': True}
        
        return {
            'valid': True,
            'errors': [],
            'number_norm': number_norm,
            'buy_amount': buy_amount,
            'payout_rate': payout_rate,
            'potential_payout': potential_payout,
            'current_total': current_total,
            'limit_amount': limit_amount
        }
    
    @staticmethod
    def _check_limit(field: str, number_norm: str, additional_amount: float, batch_id: str) -> Tuple[bool, float, float]:
        """
        Check if adding amount would exceed limit
        
        Returns:
            Tuple of (limit_exceeded, current_total, limit_amount)
        """
        # Get current total
        number_total = NumberTotal.query.filter_by(
            batch_id=batch_id,
            field=field,
            number_norm=number_norm
        ).first()
        
        current_total = float(number_total.total_amount) if number_total else 0.0
        
        # Get limit
        limit_rule = Rule.query.filter_by(
            rule_type='limit',
            field=field,
            number_norm=number_norm,  # Specific number limit
            is_active=True
        ).first()
        
        if not limit_rule:
            # Get default limit for field
            limit_rule = Rule.query.filter_by(
                rule_type='limit',
                field=field,
                number_norm=None,  # Default field limit
                is_active=True
            ).first()
        
        if not limit_rule:
            # No limit set
            return False, current_total, float('inf')
        
        limit_amount = float(limit_rule.value)
        new_total = current_total + additional_amount
        
        return new_total > limit_amount, current_total, limit_amount
    
    @staticmethod
    def create_order(user_id: int, items: List[Dict], customer_name: str = None, notes: str = None) -> Order:
        """
        Create a new order
        
        Args:
            user_id: User ID
            items: List of order items
            customer_name: Optional customer name
            notes: Optional notes
        
        Returns:
            Created Order object
        """
        # Calculate lottery period and batch ID
        lottery_period = calculate_lottery_period()
        batch_id = generate_batch_id(lottery_period)
        
        # Validate all items first
        validated_items = []
        total_amount = Decimal('0')
        
        for item in items:
            validation = OrderService.validate_order_item(
                item['field'], item['number'], item['amount'], batch_id
            )
            
            if not validation['valid']:
                raise OrderValidationError(f"รายการ {item['field']}:{item['number']} - {', '.join(validation['errors'])}")
            
            validated_items.append({
                'field': item['field'],
                'number_input': item['number'],
                'number_norm': validation['number_norm'],
                'buy_amount': Decimal(str(validation['buy_amount'])),
                'payout_rate': Decimal(str(validation['payout_rate'])),
                'potential_payout': Decimal(str(validation['potential_payout'])),
                'is_blocked': validation.get('is_blocked', False)
            })
            
            total_amount += Decimal(str(validation['buy_amount']))
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=user_id,
            customer_name=customer_name,
            total_amount=total_amount,
            lottery_period=lottery_period,
            batch_id=batch_id,
            notes=notes,
            status='pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in validated_items:
            order_item = OrderItem(
                order_id=order.id,
                field=item_data['field'],
                number_input=item_data['number_input'],
                number_norm=item_data['number_norm'],
                buy_amount=item_data['buy_amount'],
                payout_rate=item_data['payout_rate'],
                potential_payout=item_data['potential_payout'],
                is_blocked=item_data['is_blocked']
            )
            db.session.add(order_item)
            
            # Update number totals
            OrderService._update_number_total(
                batch_id, item_data['field'], item_data['number_norm'], 
                float(item_data['buy_amount'])
            )
        
        db.session.commit()
        
        # Log order creation
        audit_log = AuditLog(
            user_id=user_id,
            action='create_order',
            resource='order',
            resource_id=str(order.id),
            details={
                'order_number': order.order_number,
                'total_amount': float(total_amount),
                'items_count': len(validated_items)
            }
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return order
    
    @staticmethod
    def _update_number_total(batch_id: str, field: str, number_norm: str, amount: float):
        """Update number total for limit tracking"""
        number_total = NumberTotal.query.filter_by(
            batch_id=batch_id,
            field=field,
            number_norm=number_norm
        ).first()
        
        if number_total:
            number_total.total_amount += Decimal(str(amount))
            number_total.order_count += 1
            number_total.last_updated = datetime.now(BANGKOK_TZ)
        else:
            number_total = NumberTotal(
                batch_id=batch_id,
                field=field,
                number_norm=number_norm,
                total_amount=Decimal(str(amount)),
                order_count=1
            )
            db.session.add(number_total)
    
    @staticmethod
    def cancel_order(order_id: int, user_id: int, reason: str = None) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            user_id: User ID (for authorization)
            reason: Cancellation reason
        
        Returns:
            True if successful
        """
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            raise OrderValidationError("ไม่พบรายการสั่งซื้อ")
        
        if order.status != 'pending':
            raise OrderValidationError("ไม่สามารถยกเลิกรายการที่ไม่ใช่สถานะรอดำเนินการได้")
        
        # Update order status
        order.status = 'cancelled'
        order.notes = f"{order.notes or ''}\nยกเลิก: {reason or 'ไม่ระบุเหตุผล'}"
        
        # Reverse number totals
        for item in order.items:
            OrderService._reverse_number_total(
                order.batch_id, item.field, item.number_norm, float(item.buy_amount)
            )
        
        db.session.commit()
        
        # Log cancellation
        audit_log = AuditLog(
            user_id=user_id,
            action='cancel_order',
            resource='order',
            resource_id=str(order.id),
            details={
                'order_number': order.order_number,
                'reason': reason
            }
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return True
    
    @staticmethod
    def _reverse_number_total(batch_id: str, field: str, number_norm: str, amount: float):
        """Reverse number total when cancelling order"""
        number_total = NumberTotal.query.filter_by(
            batch_id=batch_id,
            field=field,
            number_norm=number_norm
        ).first()
        
        if number_total:
            number_total.total_amount -= Decimal(str(amount))
            number_total.order_count -= 1
            number_total.last_updated = datetime.now(BANGKOK_TZ)
            
            # Remove if total becomes zero
            if number_total.total_amount <= 0:
                db.session.delete(number_total)
    
    @staticmethod
    def get_current_batch_id() -> str:
        """Get current batch ID"""
        lottery_period = calculate_lottery_period()
        return generate_batch_id(lottery_period)
    
    @staticmethod
    def get_number_summary(batch_id: str, field: str = None) -> List[Dict]:
        """
        Get number summary for current batch
        
        Args:
            batch_id: Batch ID
            field: Optional field filter
        
        Returns:
            List of number summaries
        """
        query = NumberTotal.query.filter_by(batch_id=batch_id)
        
        if field:
            query = query.filter_by(field=field)
        
        totals = query.order_by(NumberTotal.field, NumberTotal.number_norm).all()
        
        return [
            {
                'field': total.field,
                'number': total.number_norm,
                'total_amount': float(total.total_amount),
                'order_count': total.order_count,
                'last_updated': total.last_updated
            }
            for total in totals
        ]

