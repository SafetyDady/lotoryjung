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
    def get_base_payout_rates() -> Dict[str, int]:
        """Get base payout rates from database rules"""
        rates = {}
        
        # Query payout rules (rule_type='payout', number_norm=NULL)
        payout_rules = Rule.query.filter(
            Rule.rule_type == 'payout',
            Rule.number_norm.is_(None),
            Rule.is_active == True
        ).all()
        
        for rule in payout_rules:
            rates[rule.field] = int(rule.value)
        
        # Set system fallback rates if not found in database
        system_defaults = {
            '2_top': 90,
            '2_bottom': 90,
            '3_top': 900,
            'tote': 150
        }
        
        for field, default_rate in system_defaults.items():
            if field not in rates:
                rates[field] = default_rate
                
        return rates
    
    @staticmethod
    def get_base_payout_rate(field: str) -> int:
        """Get base payout rate for specific field"""
        rates = LimitService.get_base_payout_rates()
        return rates.get(field, 0)
    
    @staticmethod
    def set_base_payout_rate(field: str, rate: int) -> bool:
        """Set base payout rate for field"""
        try:
            # Find existing rule or create new
            rule = Rule.query.filter(
                Rule.rule_type == 'payout',
                Rule.field == field,
                Rule.number_norm.is_(None)
            ).first()
            
            if rule:
                rule.value = Decimal(str(rate))
            else:
                rule = Rule(
                    rule_type='payout',
                    field=field,
                    number_norm=None,
                    value=Decimal(str(rate)),
                    is_active=True
                )
                db.session.add(rule)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error setting base payout rate: {e}")
            return False

    @staticmethod
    def get_default_limits() -> Dict[str, Decimal]:
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
        default_limits = LimitService.get_default_limits()
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
    def get_default_group_limits() -> Dict[str, Decimal]:
        """Get default limits for all field groups"""
        limits = {}
        
        # Query default limit rules (rule_type='default_limit', number_norm=NULL)
        default_rules = Rule.query.filter(
            Rule.rule_type == 'default_limit',
            Rule.number_norm.is_(None),
            Rule.is_active == True
        ).all()
        
        for rule in default_rules:
            limits[rule.field] = Decimal(str(rule.value))
        
        # Set system fallback limits if not found in database
        system_defaults = {
            '2_top': Decimal('10000'),
            '2_bottom': Decimal('10000'),
            '3_top': Decimal('5000'),
            'tote': Decimal('3000')
        }
        
        for field, default_limit in system_defaults.items():
            if field not in limits:
                limits[field] = default_limit
                
        return limits
    
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
                'reason': 'มียอดซื้อรวมเกินโควต้า - จ่ายครึ่งเดียว'
            })
        
        return result
    
    @staticmethod
    def get_limits_dashboard_data(batch_id: str = None) -> Dict:
        """Get dashboard data for limits overview - showing individual number risks"""
        if not batch_id:
            batch_id = LimitService._get_current_batch_id()
        
        default_limits = LimitService.get_default_group_limits()
        
        # Get usage summary by field - focus on individual numbers
        dashboard_data = {}
        for field in ['2_top', '2_bottom', '3_top', 'tote']:
            # Get all numbers with totals for this field
            totals = NumberTotal.query.filter(
                NumberTotal.batch_id == batch_id,
                NumberTotal.field == field
            ).order_by(NumberTotal.total_amount.desc()).all()
            
            # Get default limit for this field (used as individual limit too)
            default_limit = default_limits.get(field, Decimal('700'))
            
            # Analyze individual numbers
            exceeded_numbers = []  # Numbers over limit
            risky_numbers = []    # Numbers 90%+ of limit
            top_numbers = []      # Top 10 by amount
            
            for total in totals:
                # Get individual limit (could be custom or default)
                individual_limit = LimitService.get_individual_limit(field, total.number_norm)
                usage_percent = float((total.total_amount / individual_limit) * 100) if individual_limit > 0 else 0
                
                number_info = {
                    'number': total.number_norm,
                    'amount': total.total_amount,
                    'limit': individual_limit,
                    'usage_percent': round(usage_percent, 1),
                    'order_count': total.order_count
                }
                
                # Categorize numbers
                if total.total_amount > individual_limit:
                    exceeded_numbers.append(number_info)
                elif usage_percent >= 90:
                    risky_numbers.append(number_info)
                
                # Add to top list (limit to 10)
                if len(top_numbers) < 10:
                    top_numbers.append(number_info)
            
            # Calculate totals for reference
            total_orders = sum(t.order_count for t in totals)
            numbers_count = len(totals)
            
            dashboard_data[field] = {
                'field_name': LimitService._get_field_display_name(field),
                'default_limit': default_limit,
                'exceeded_count': len(exceeded_numbers),
                'risky_count': len(risky_numbers),
                'total_orders': total_orders,
                'total_numbers': numbers_count,
                'exceeded_numbers': exceeded_numbers[:5],  # Show top 5 exceeded
                'risky_numbers': risky_numbers[:5],       # Show top 5 risky  
                'top_numbers': top_numbers[:5],           # Show top 5 amounts
                'status': 'danger' if exceeded_numbers else 'warning' if risky_numbers else 'safe'
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
