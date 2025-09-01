"""
Rule service for managing business rules
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal

from app import db
from app.models import Rule, BlockedNumber, AuditLog

class RuleService:
    """Service class for rule operations"""
    
    @staticmethod
    def get_payout_rate(field: str, number_norm: str = None) -> Optional[float]:
        """
        Get payout rate for field and optional specific number
        
        Args:
            field: Field type (2_top, 2_bottom, 3_top, tote)
            number_norm: Optional specific number
        
        Returns:
            Payout rate or None if not found
        """
        # Try specific number first
        if number_norm:
            rule = Rule.query.filter_by(
                rule_type='payout',
                field=field,
                number_norm=number_norm,
                is_active=True
            ).first()
            
            if rule:
                return float(rule.value)
        
        # Fall back to default field rate
        rule = Rule.query.filter_by(
            rule_type='payout',
            field=field,
            number_norm=None,
            is_active=True
        ).first()
        
        return float(rule.value) if rule else None
    
    @staticmethod
    def get_limit_amount(field: str, number_norm: str = None) -> Optional[float]:
        """
        Get limit amount for field and optional specific number
        
        Args:
            field: Field type
            number_norm: Optional specific number
        
        Returns:
            Limit amount or None if not found
        """
        # Try specific number first
        if number_norm:
            rule = Rule.query.filter_by(
                rule_type='limit',
                field=field,
                number_norm=number_norm,
                is_active=True
            ).first()
            
            if rule:
                return float(rule.value)
        
        # Fall back to default field limit
        rule = Rule.query.filter_by(
            rule_type='limit',
            field=field,
            number_norm=None,
            is_active=True
        ).first()
        
        return float(rule.value) if rule else None
    
    @staticmethod
    def set_payout_rate(field: str, rate: float, number_norm: str = None, user_id: int = None) -> Rule:
        """
        Set payout rate for field
        
        Args:
            field: Field type
            rate: Payout rate
            number_norm: Optional specific number
            user_id: User ID for audit log
        
        Returns:
            Rule object
        """
        # Check if rule exists
        existing_rule = Rule.query.filter_by(
            rule_type='payout',
            field=field,
            number_norm=number_norm
        ).first()
        
        if existing_rule:
            old_value = float(existing_rule.value)
            existing_rule.value = Decimal(str(rate))
            existing_rule.is_active = True
            rule = existing_rule
        else:
            rule = Rule(
                rule_type='payout',
                field=field,
                number_norm=number_norm,
                value=Decimal(str(rate)),
                is_active=True
            )
            db.session.add(rule)
            old_value = None
        
        db.session.commit()
        
        # Log change
        if user_id:
            audit_log = AuditLog(
                user_id=user_id,
                action='update_payout_rate',
                resource='rule',
                resource_id=str(rule.id),
                details={
                    'field': field,
                    'number_norm': number_norm,
                    'old_value': old_value,
                    'new_value': rate
                }
            )
            db.session.add(audit_log)
            db.session.commit()
        
        return rule
    
    @staticmethod
    def set_limit_amount(field: str, amount: float, number_norm: str = None, user_id: int = None) -> Rule:
        """
        Set limit amount for field
        
        Args:
            field: Field type
            amount: Limit amount
            number_norm: Optional specific number
            user_id: User ID for audit log
        
        Returns:
            Rule object
        """
        # Check if rule exists
        existing_rule = Rule.query.filter_by(
            rule_type='limit',
            field=field,
            number_norm=number_norm
        ).first()
        
        if existing_rule:
            old_value = float(existing_rule.value)
            existing_rule.value = Decimal(str(amount))
            existing_rule.is_active = True
            rule = existing_rule
        else:
            rule = Rule(
                rule_type='limit',
                field=field,
                number_norm=number_norm,
                value=Decimal(str(amount)),
                is_active=True
            )
            db.session.add(rule)
            old_value = None
        
        db.session.commit()
        
        # Log change
        if user_id:
            audit_log = AuditLog(
                user_id=user_id,
                action='update_limit',
                resource='rule',
                resource_id=str(rule.id),
                details={
                    'field': field,
                    'number_norm': number_norm,
                    'old_value': old_value,
                    'new_value': amount
                }
            )
            db.session.add(audit_log)
            db.session.commit()
        
        return rule
    
    @staticmethod
    def is_number_blocked(field: str, number_norm: str) -> Tuple[bool, Optional[str]]:
        """
        Check if number is blocked
        
        Args:
            field: Field type
            number_norm: Normalized number
        
        Returns:
            Tuple of (is_blocked, reason)
        """
        blocked = BlockedNumber.query.filter_by(
            field=field,
            number_norm=number_norm,
            is_active=True
        ).first()
        
        if blocked:
            return True, blocked.reason
        
        return False, None
    
    @staticmethod
    def block_number(field: str, number_norm: str, reason: str = None, user_id: int = None) -> BlockedNumber:
        """
        Block a number
        
        Args:
            field: Field type
            number_norm: Normalized number
            reason: Reason for blocking
            user_id: User ID for audit log
        
        Returns:
            BlockedNumber object
        """
        # Check if already blocked
        existing_blocked = BlockedNumber.query.filter_by(
            field=field,
            number_norm=number_norm
        ).first()
        
        if existing_blocked:
            existing_blocked.is_active = True
            existing_blocked.reason = reason
            blocked = existing_blocked
        else:
            blocked = BlockedNumber(
                field=field,
                number_norm=number_norm,
                reason=reason,
                is_active=True
            )
            db.session.add(blocked)
        
        db.session.commit()
        
        # Log change
        if user_id:
            audit_log = AuditLog(
                user_id=user_id,
                action='block_number',
                resource='blocked_number',
                resource_id=str(blocked.id),
                details={
                    'field': field,
                    'number_norm': number_norm,
                    'reason': reason
                }
            )
            db.session.add(audit_log)
            db.session.commit()
        
        return blocked
    
    @staticmethod
    def unblock_number(field: str, number_norm: str, user_id: int = None) -> bool:
        """
        Unblock a number
        
        Args:
            field: Field type
            number_norm: Normalized number
            user_id: User ID for audit log
        
        Returns:
            True if unblocked, False if not found
        """
        blocked = BlockedNumber.query.filter_by(
            field=field,
            number_norm=number_norm,
            is_active=True
        ).first()
        
        if not blocked:
            return False
        
        blocked.is_active = False
        db.session.commit()
        
        # Log change
        if user_id:
            audit_log = AuditLog(
                user_id=user_id,
                action='unblock_number',
                resource='blocked_number',
                resource_id=str(blocked.id),
                details={
                    'field': field,
                    'number_norm': number_norm
                }
            )
            db.session.add(audit_log)
            db.session.commit()
        
        return True
    
    @staticmethod
    def get_all_blocked_numbers(field: str = None) -> List[Dict]:
        """
        Get all blocked numbers
        
        Args:
            field: Optional field filter
        
        Returns:
            List of blocked number dictionaries
        """
        query = BlockedNumber.query.filter_by(is_active=True)
        
        if field:
            query = query.filter_by(field=field)
        
        blocked_numbers = query.order_by(BlockedNumber.field, BlockedNumber.number_norm).all()
        
        return [
            {
                'id': blocked.id,
                'field': blocked.field,
                'number_norm': blocked.number_norm,
                'reason': blocked.reason,
                'created_at': blocked.created_at
            }
            for blocked in blocked_numbers
        ]
    
    @staticmethod
    def get_all_rules(rule_type: str = None, field: str = None) -> List[Dict]:
        """
        Get all rules
        
        Args:
            rule_type: Optional rule type filter (payout, limit)
            field: Optional field filter
        
        Returns:
            List of rule dictionaries
        """
        query = Rule.query.filter_by(is_active=True)
        
        if rule_type:
            query = query.filter_by(rule_type=rule_type)
        
        if field:
            query = query.filter_by(field=field)
        
        rules = query.order_by(Rule.rule_type, Rule.field, Rule.number_norm).all()
        
        return [
            {
                'id': rule.id,
                'rule_type': rule.rule_type,
                'field': rule.field,
                'number_norm': rule.number_norm,
                'value': float(rule.value),
                'created_at': rule.created_at,
                'updated_at': rule.updated_at
            }
            for rule in rules
        ]
    
    @staticmethod
    def bulk_update_payout_rates(rates: Dict[str, float], user_id: int = None) -> int:
        """
        Bulk update payout rates
        
        Args:
            rates: Dictionary of field -> rate
            user_id: User ID for audit log
        
        Returns:
            Number of rules updated
        """
        updated_count = 0
        
        for field, rate in rates.items():
            RuleService.set_payout_rate(field, rate, user_id=user_id)
            updated_count += 1
        
        return updated_count
    
    @staticmethod
    def bulk_update_limits(limits: Dict[str, float], user_id: int = None) -> int:
        """
        Bulk update limit amounts
        
        Args:
            limits: Dictionary of field -> limit
            user_id: User ID for audit log
        
        Returns:
            Number of rules updated
        """
        updated_count = 0
        
        for field, limit in limits.items():
            RuleService.set_limit_amount(field, limit, user_id=user_id)
            updated_count += 1
        
        return updated_count

