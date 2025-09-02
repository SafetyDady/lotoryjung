"""
Individual Number Limits Management Service
Handles individual number limits, default group limits, and payout rate calculation
"""

from app.models import Rule, NumberTotal, OrderItem, BlockedNumber, db
from sqlalchemy import func
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

class LimitService:
    """Service for managing individual number limits and payout calculations"""
    
    @staticmethod
    def get_default_group_limits() -> Dict[str, Decimal]:
        """Get default limits for each field group"""
        limits = {}
        
        # Query default limits (rule_type='default_limit', number_norm=NULL)
        rules = Rule.query.filter(
            Rule.rule_type == 'default_limit',
            Rule.number_norm.is_(None),
            Rule.is_active == True
        ).all()
        
        for rule in rules:
            limits[rule.field] = rule.value
            
        # Set system default limits if not found
        system_defaults = {
            '2_top': Decimal('700.00'),
            '2_bottom': Decimal('600.00'),
            '3_top': Decimal('500.00'),
            'tote': Decimal('400.00')
        }
        
        for field, default_value in system_defaults.items():
            if field not in limits:
                limits[field] = default_value
                
        return limits
    
    @staticmethod
    def get_individual_limit(field: str, number_norm: str) -> Decimal:
        """Get limit for specific number, fallback to default group limit"""
        # Try to find individual limit first
        individual_rule = Rule.query.filter(
            Rule.rule_type == 'number_limit',
            Rule.field == field,
            Rule.number_norm == number_norm,
            Rule.is_active == True
        ).first()
        
        if individual_rule:
            return individual_rule.value
        
        # Fallback to default group limit
        default_limits = LimitService.get_default_group_limits()
        return default_limits.get(field, Decimal('0'))
    
    @staticmethod
    def set_individual_limit(field: str, number_norm: str, limit_amount: Decimal) -> bool:
        """Set limit for specific number"""
        try:
            # Find existing rule or create new
            rule = Rule.query.filter(
                Rule.rule_type == 'number_limit',
                Rule.field == field,
                Rule.number_norm == number_norm
            ).first()
            
            if rule:
                rule.value = limit_amount
                rule.is_active = True
            else:
                rule = Rule(
                    rule_type='number_limit',
                    field=field,
                    number_norm=number_norm,
                    value=limit_amount,
                    is_active=True
                )
                db.session.add(rule)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error setting individual limit: {e}")
            return False
    
    @staticmethod
    def set_default_group_limit(field: str, limit_amount: Decimal) -> bool:
        """Set default limit for entire field group"""
        try:
            # Find existing rule or create new
            rule = Rule.query.filter(
                Rule.rule_type == 'default_limit',
                Rule.field == field,
                Rule.number_norm.is_(None)
            ).first()
            
            if rule:
                rule.value = limit_amount
            else:
                rule = Rule(
                    rule_type='default_limit',
                    field=field,
                    number_norm=None,
                    value=limit_amount,
                    is_active=True
                )
                db.session.add(rule)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error setting default limit: {e}")
            return False
    
    @staticmethod
    def get_current_usage(field: str, number_norm: str, batch_id: str = None) -> Decimal:
        """Get current usage for specific number"""
        if not batch_id:
            batch_id = LimitService._get_current_batch_id()
        
        total = NumberTotal.query.filter(
            NumberTotal.batch_id == batch_id,
            NumberTotal.field == field,
            NumberTotal.number_norm == number_norm
        ).first()
        
        return total.total_amount if total else Decimal('0')
    
    @staticmethod
    def is_blocked_number(field: str, number_norm: str) -> bool:
        """Check if number is blocked (Step 1 in validation flow)"""
        blocked = BlockedNumber.query.filter(
            BlockedNumber.field == field,
            BlockedNumber.number_norm == number_norm,
            BlockedNumber.is_active == True
        ).first()
        
        return blocked is not None
    
    @staticmethod
    def exceeds_limit(field: str, number_norm: str, buy_amount: Decimal, batch_id: str = None) -> bool:
        """Check if purchase would exceed limit (Step 2 in validation flow)"""
        current_usage = LimitService.get_current_usage(field, number_norm, batch_id)
        limit = LimitService.get_individual_limit(field, number_norm)
        
        return (current_usage + buy_amount) > limit
    
    @staticmethod
    def calculate_payout_rate(field: str, number_norm: str, buy_amount: Decimal, batch_id: str = None) -> float:
        """
        Calculate payout rate based on validation flow:
        Step 1: Check blocked numbers (if blocked → 0.5)
        Step 2: Check limits (if exceeded → 0.5, else → 1.0)
        """
        # Step 1: Check blocked first (highest priority)
        if LimitService.is_blocked_number(field, number_norm):
            return 0.5
        
        # Step 2: Check limit only if not blocked
        if LimitService.exceeds_limit(field, number_norm, buy_amount, batch_id):
            return 0.5
        
        return 1.0  # Normal rate
    
    @staticmethod
    def validate_order_item(field: str, number_norm: str, buy_amount: Decimal, batch_id: str = None) -> Dict:
        """
        Comprehensive validation for order item
        Returns: {
            'is_valid': bool,
            'payout_rate': float,
            'reason': str,
            'current_usage': Decimal,
            'limit': Decimal,
            'is_blocked': bool
        }
        """
        current_usage = LimitService.get_current_usage(field, number_norm, batch_id)
        limit = LimitService.get_individual_limit(field, number_norm)
        is_blocked = LimitService.is_blocked_number(field, number_norm)
        
        result = {
            'is_valid': True,
            'payout_rate': 1.0,
            'reason': 'ปกติ',
            'current_usage': current_usage,
            'limit': limit,
            'is_blocked': is_blocked
        }
        
        if is_blocked:
            result.update({
                'payout_rate': 0.5,
                'reason': 'เลขอั้น - จ่ายครึ่งเดียว'
            })
        elif (current_usage + buy_amount) > limit:
            result.update({
                'payout_rate': 0.5,
                'reason': f'เกินขีดจำกัด {limit:,.0f} บาท - จ่ายครึ่งเดียว'
            })
        
        return result
    
    @staticmethod
    def get_limits_dashboard_data(batch_id: str = None) -> Dict:
        """Get dashboard data for limits overview"""
        if not batch_id:
            batch_id = LimitService._get_current_batch_id()
        
        default_limits = LimitService.get_default_group_limits()
        
        # Get usage summary by field
        dashboard_data = {}
        for field in ['2_top', '2_bottom', '3_top', 'tote']:
            totals = NumberTotal.query.filter(
                NumberTotal.batch_id == batch_id,
                NumberTotal.field == field
            ).all()
            
            total_usage = sum(t.total_amount for t in totals)
            numbers_count = len(totals)
            over_limit_count = 0
            
            # Count numbers over their individual limits
            for total in totals:
                limit = LimitService.get_individual_limit(field, total.number_norm)
                if total.total_amount > limit:
                    over_limit_count += 1
            
            # Get default limit for this field
            limit_amount = default_limits.get(field, Decimal('0'))
            
            # Calculate percentages
            usage_percent = 0
            remaining_amount = limit_amount - total_usage
            
            if limit_amount > 0:
                usage_percent = float((total_usage / limit_amount) * 100)
            
            # Determine status
            status = 'safe'
            if usage_percent >= 90:
                status = 'danger'
            elif usage_percent >= 75:
                status = 'warning'
            elif usage_percent >= 50:
                status = 'info'
            
            dashboard_data[field] = {
                'field_name': LimitService._get_field_display_name(field),
                'limit_amount': limit_amount,
                'used_amount': total_usage,
                'remaining_amount': remaining_amount,
                'usage_percent': round(usage_percent, 1),
                'order_count': sum(t.order_count for t in totals),
                'number_count': numbers_count,
                'over_limit_count': over_limit_count,
                'status': status,
                'is_exceeded': total_usage > limit_amount
            }
        
        return dashboard_data
    
    @staticmethod
    def get_individual_limits_list(field: str = None) -> List[Dict]:
        """Get list of individual number limits"""
        query = Rule.query.filter(
            Rule.rule_type == 'number_limit',
            Rule.is_active == True
        )
        
        if field:
            query = query.filter(Rule.field == field)
        
        rules = query.all()
        
        result = []
        for rule in rules:
            result.append({
                'field': rule.field,
                'number_norm': rule.number_norm,
                'limit': rule.value,
                'created_at': rule.created_at
            })
        
        return result
    
    @staticmethod
    def _get_field_display_name(field: str) -> str:
        """Get display name for field"""
        names = {
            '2_top': '2 ตัวบน',
            '2_bottom': '2 ตัวล่าง',
            '3_top': '3 ตัวบน',
            'tote': 'โต๊ด'
        }
        return names.get(field, field)
    
    @staticmethod
    def _get_current_batch_id() -> str:
        """Get current active batch ID"""
        from datetime import date
        return date.today().strftime('%Y%m%d')
