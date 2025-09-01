"""
Rule Engine for lottery number processing and validation
"""

from typing import List, Dict, Tuple, Optional, Any
from decimal import Decimal
from datetime import datetime
import pytz

from app import db
from app.models import Rule, BlockedNumber, NumberTotal, Order, OrderItem
from app.utils.number_utils import normalize_number, canonicalize_tote
from app.services.rule_service import RuleService

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class RuleEngineError(Exception):
    """Custom exception for rule engine errors"""
    pass

class RuleEngine:
    """Core rule engine for lottery number processing"""
    
    def __init__(self):
        self.rules_cache = {}
        self.blocked_cache = {}
        self.cache_timestamp = None
        self.cache_ttl = 300  # 5 minutes
    
    def _refresh_cache(self):
        """Refresh rules cache if needed"""
        now = datetime.now()
        
        if (self.cache_timestamp is None or 
            (now - self.cache_timestamp).seconds > self.cache_ttl):
            
            # Load all active rules
            rules = Rule.query.filter_by(is_active=True).all()
            self.rules_cache = {}
            
            for rule in rules:
                key = f"{rule.rule_type}:{rule.field}:{rule.number_norm or 'default'}"
                self.rules_cache[key] = float(rule.value)
            
            # Load all blocked numbers
            blocked_numbers = BlockedNumber.query.filter_by(is_active=True).all()
            self.blocked_cache = {}
            
            for blocked in blocked_numbers:
                key = f"{blocked.field}:{blocked.number_norm}"
                self.blocked_cache[key] = blocked.reason
            
            self.cache_timestamp = now
    
    def get_payout_rate(self, field: str, number_norm: str = None) -> float:
        """Get payout rate with caching"""
        self._refresh_cache()
        
        # Try specific number first
        if number_norm:
            key = f"payout:{field}:{number_norm}"
            if key in self.rules_cache:
                return self.rules_cache[key]
        
        # Fall back to default
        key = f"payout:{field}:default"
        return self.rules_cache.get(key, 0.0)
    
    def get_limit_amount(self, field: str, number_norm: str = None) -> float:
        """Get limit amount with caching"""
        self._refresh_cache()
        
        # Try specific number first
        if number_norm:
            key = f"limit:{field}:{number_norm}"
            if key in self.rules_cache:
                return self.rules_cache[key]
        
        # Fall back to default
        key = f"limit:{field}:default"
        return self.rules_cache.get(key, float('inf'))
    
    def is_number_blocked(self, field: str, number_norm: str) -> Tuple[bool, Optional[str]]:
        """Check if number is blocked with caching"""
        self._refresh_cache()
        
        key = f"{field}:{number_norm}"
        if key in self.blocked_cache:
            return True, self.blocked_cache[key]
        
        return False, None
    
    def validate_number_purchase(self, field: str, number: str, amount: float, batch_id: str) -> Dict[str, Any]:
        """
        Comprehensive validation of number purchase
        
        Args:
            field: Field type (2_top, 2_bottom, 3_top, tote)
            number: Number to purchase
            amount: Purchase amount
            batch_id: Current batch ID
        
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'data': {}
        }
        
        try:
            # Normalize number
            number_norm = normalize_number(number, field)
            result['data']['number_norm'] = number_norm
            result['data']['number_input'] = number
            
            # Check if blocked
            is_blocked, block_reason = self.is_number_blocked(field, number_norm)
            if is_blocked:
                # Check if blocked number has reduced payout
                blocked_payout_rate = self.get_payout_rate(field, number_norm)
                if blocked_payout_rate > 0:
                    # Blocked number with reduced payout
                    result['warnings'].append(f"เลข {number_norm} เป็นเลขอั้น จ่ายในอัตรา {blocked_payout_rate}x")
                    result['data']['is_blocked'] = True
                    result['data']['payout_rate'] = blocked_payout_rate
                else:
                    # Completely blocked
                    result['valid'] = False
                    result['errors'].append(f"เลข {number_norm} ถูกอั้น: {block_reason or 'ไม่ระบุเหตุผล'}")
                    return result
            else:
                # Normal number
                payout_rate = self.get_payout_rate(field, number_norm)
                result['data']['is_blocked'] = False
                result['data']['payout_rate'] = payout_rate
            
            # Calculate potential payout
            potential_payout = amount * result['data']['payout_rate']
            result['data']['buy_amount'] = amount
            result['data']['potential_payout'] = potential_payout
            
            # Check limit
            limit_check = self._check_purchase_limit(field, number_norm, amount, batch_id)
            result['data'].update(limit_check)
            
            if limit_check['limit_exceeded']:
                result['valid'] = False
                result['errors'].append(limit_check['limit_message'])
            
            # Handle tote canonicalization
            if field == 'tote':
                canonical_forms = canonicalize_tote(number_norm)
                result['data']['canonical_forms'] = canonical_forms
                
                if len(canonical_forms) > 1:
                    result['warnings'].append(f"เลขโต๊ด {number_norm} จะครอบคลุม: {', '.join(canonical_forms)}")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}")
        
        return result
    
    def _check_purchase_limit(self, field: str, number_norm: str, amount: float, batch_id: str) -> Dict[str, Any]:
        """Check purchase against limits"""
        # Get current total
        number_total = NumberTotal.query.filter_by(
            batch_id=batch_id,
            field=field,
            number_norm=number_norm
        ).first()
        
        current_total = float(number_total.total_amount) if number_total else 0.0
        
        # Get limit
        limit_amount = self.get_limit_amount(field, number_norm)
        
        new_total = current_total + amount
        limit_exceeded = new_total > limit_amount
        
        return {
            'current_total': current_total,
            'limit_amount': limit_amount,
            'new_total': new_total,
            'limit_exceeded': limit_exceeded,
            'limit_message': f"เลข {number_norm} เกินลิมิต: ปัจจุบัน {current_total:,.2f} + {amount:,.2f} > {limit_amount:,.2f}" if limit_exceeded else None
        }
    
    def process_order_items(self, items: List[Dict], batch_id: str) -> Dict[str, Any]:
        """
        Process multiple order items with cross-validation
        
        Args:
            items: List of order items
            batch_id: Current batch ID
        
        Returns:
            Processing result
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'items': [],
            'summary': {
                'total_amount': 0.0,
                'total_payout': 0.0,
                'blocked_count': 0,
                'normal_count': 0
            }
        }
        
        # Validate each item
        for i, item in enumerate(items):
            item_result = self.validate_number_purchase(
                item['field'], item['number'], float(item['amount']), batch_id
            )
            
            item_result['index'] = i
            result['items'].append(item_result)
            
            if not item_result['valid']:
                result['valid'] = False
                result['errors'].extend([f"รายการที่ {i+1}: {error}" for error in item_result['errors']])
            
            if item_result['warnings']:
                result['warnings'].extend([f"รายการที่ {i+1}: {warning}" for warning in item_result['warnings']])
            
            # Update summary
            if item_result['valid']:
                result['summary']['total_amount'] += item_result['data']['buy_amount']
                result['summary']['total_payout'] += item_result['data']['potential_payout']
                
                if item_result['data']['is_blocked']:
                    result['summary']['blocked_count'] += 1
                else:
                    result['summary']['normal_count'] += 1
        
        # Cross-validation checks
        self._perform_cross_validation(result)
        
        return result
    
    def _perform_cross_validation(self, result: Dict[str, Any]):
        """Perform cross-validation checks across all items"""
        
        # Check for duplicate numbers in same field
        seen_numbers = {}
        for item_result in result['items']:
            if not item_result['valid']:
                continue
            
            field = item_result['data'].get('field')
            number_norm = item_result['data'].get('number_norm')
            
            if not field or not number_norm:
                continue
            
            key = f"{field}:{number_norm}"
            if key in seen_numbers:
                result['valid'] = False
                result['errors'].append(f"เลข {number_norm} ในประเภท {field} ซ้ำกัน")
            else:
                seen_numbers[key] = True
        
        # Check total amount limits (if any)
        total_amount = result['summary']['total_amount']
        if total_amount > 100000:  # Example: max 100k per order
            result['warnings'].append(f"ยอดรวมสูง: {total_amount:,.2f} บาท")
        
        # Check for suspicious patterns
        if result['summary']['blocked_count'] > result['summary']['normal_count']:
            result['warnings'].append("มีเลขอั้นเป็นส่วนใหญ่ในรายการนี้")
    
    def calculate_win_payout(self, winning_numbers: Dict[str, str], batch_id: str) -> Dict[str, Any]:
        """
        Calculate payout for winning numbers
        
        Args:
            winning_numbers: Dict of field -> winning number
            batch_id: Batch ID to calculate for
        
        Returns:
            Payout calculation results
        """
        result = {
            'total_payout': 0.0,
            'winning_orders': [],
            'field_payouts': {}
        }
        
        for field, winning_number in winning_numbers.items():
            winning_number_norm = normalize_number(winning_number, field)
            
            # Find all winning order items
            winning_items = db.session.query(OrderItem).join(Order).filter(
                Order.batch_id == batch_id,
                OrderItem.field == field,
                OrderItem.number_norm == winning_number_norm
            ).all()
            
            field_payout = 0.0
            field_winners = []
            
            for item in winning_items:
                payout = float(item.potential_payout)
                field_payout += payout
                
                field_winners.append({
                    'order_id': item.order_id,
                    'order_number': item.order.order_number,
                    'user_id': item.order.user_id,
                    'number': item.number_norm,
                    'buy_amount': float(item.buy_amount),
                    'payout': payout
                })
            
            result['field_payouts'][field] = {
                'winning_number': winning_number_norm,
                'total_payout': field_payout,
                'winner_count': len(field_winners),
                'winners': field_winners
            }
            
            result['total_payout'] += field_payout
            result['winning_orders'].extend(field_winners)
        
        return result
    
    def get_risk_analysis(self, batch_id: str) -> Dict[str, Any]:
        """
        Analyze risk for current batch
        
        Args:
            batch_id: Batch ID to analyze
        
        Returns:
            Risk analysis results
        """
        analysis = {
            'total_sales': 0.0,
            'potential_payout': 0.0,
            'risk_ratio': 0.0,
            'high_risk_numbers': [],
            'field_analysis': {}
        }
        
        # Get all number totals for batch
        number_totals = NumberTotal.query.filter_by(batch_id=batch_id).all()
        
        for total in number_totals:
            field = total.field
            number_norm = total.number_norm
            amount = float(total.total_amount)
            
            # Calculate potential payout
            payout_rate = self.get_payout_rate(field, number_norm)
            potential_payout = amount * payout_rate
            
            analysis['total_sales'] += amount
            analysis['potential_payout'] += potential_payout
            
            # Track by field
            if field not in analysis['field_analysis']:
                analysis['field_analysis'][field] = {
                    'total_sales': 0.0,
                    'potential_payout': 0.0,
                    'numbers': []
                }
            
            analysis['field_analysis'][field]['total_sales'] += amount
            analysis['field_analysis'][field]['potential_payout'] += potential_payout
            analysis['field_analysis'][field]['numbers'].append({
                'number': number_norm,
                'sales': amount,
                'potential_payout': potential_payout,
                'risk_ratio': potential_payout / amount if amount > 0 else 0
            })
            
            # Check for high-risk numbers
            if potential_payout > 50000:  # Example threshold
                analysis['high_risk_numbers'].append({
                    'field': field,
                    'number': number_norm,
                    'sales': amount,
                    'potential_payout': potential_payout
                })
        
        # Calculate overall risk ratio
        if analysis['total_sales'] > 0:
            analysis['risk_ratio'] = analysis['potential_payout'] / analysis['total_sales']
        
        return analysis

# Global rule engine instance
rule_engine = RuleEngine()

