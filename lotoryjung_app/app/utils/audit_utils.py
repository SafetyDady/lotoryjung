"""
Audit utilities for comprehensive logging and monitoring
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app
from flask_login import current_user
import json
import pytz

from app import db
from app.models import AuditLog

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class AuditLogger:
    """Comprehensive audit logging utility"""
    
    @staticmethod
    def log_action(action: str, resource: str = None, resource_id: str = None, 
                   details: Dict = None, user_id: int = None, severity: str = 'info'):
        """
        Log an action with full context
        
        Args:
            action: Action performed
            resource: Resource type affected
            resource_id: Resource ID affected
            details: Additional details
            user_id: User ID (defaults to current user)
            severity: Log severity (info, warning, error, critical)
        """
        try:
            audit_log = AuditLog(
                user_id=user_id or (current_user.id if current_user.is_authenticated else None),
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=AuditLogger._get_client_ip(),
                user_agent=request.user_agent.string if request else None,
                details={
                    'severity': severity,
                    'timestamp': datetime.now(BANGKOK_TZ).isoformat(),
                    **(details or {})
                }
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
        except Exception as e:
            # Fallback logging to prevent audit failures from breaking the application
            current_app.logger.error(f"Audit logging failed: {str(e)}")
    
    @staticmethod
    def _get_client_ip() -> str:
        """Get client IP address with proxy support"""
        if request:
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            elif request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
            else:
                return request.remote_addr or 'unknown'
        return 'system'
    
    @staticmethod
    def log_login_attempt(username: str, success: bool, reason: str = None):
        """Log login attempt"""
        AuditLogger.log_action(
            action='login_attempt',
            resource='user',
            details={
                'username': username,
                'success': success,
                'reason': reason,
                'user_agent': request.user_agent.string if request else None
            },
            severity='info' if success else 'warning'
        )
    
    @staticmethod
    def log_order_creation(order_id: int, order_number: str, total_amount: float, items_count: int):
        """Log order creation"""
        AuditLogger.log_action(
            action='create_order',
            resource='order',
            resource_id=str(order_id),
            details={
                'order_number': order_number,
                'total_amount': total_amount,
                'items_count': items_count
            },
            severity='info'
        )
    
    @staticmethod
    def log_rule_change(rule_type: str, field: str, old_value: float, new_value: float, number_norm: str = None):
        """Log rule changes"""
        AuditLogger.log_action(
            action='update_rule',
            resource='rule',
            details={
                'rule_type': rule_type,
                'field': field,
                'number_norm': number_norm,
                'old_value': old_value,
                'new_value': new_value
            },
            severity='info'
        )
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict = None, severity: str = 'warning'):
        """Log security events"""
        AuditLogger.log_action(
            action=f'security_{event_type}',
            resource='security',
            details={
                'event_type': event_type,
                **(details or {})
            },
            severity=severity
        )
    
    @staticmethod
    def log_data_access(resource: str, resource_id: str, access_type: str = 'read'):
        """Log data access"""
        AuditLogger.log_action(
            action=f'data_{access_type}',
            resource=resource,
            resource_id=resource_id,
            details={
                'access_type': access_type
            },
            severity='info'
        )
    
    @staticmethod
    def log_admin_action(action: str, target_resource: str, target_id: str, details: Dict = None):
        """Log admin actions"""
        AuditLogger.log_action(
            action=f'admin_{action}',
            resource=target_resource,
            resource_id=target_id,
            details=details,
            severity='info'
        )

def audit_action(action: str, resource: str = None, severity: str = 'info'):
    """Decorator for automatic action auditing"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = datetime.now(BANGKOK_TZ)
            
            try:
                result = f(*args, **kwargs)
                
                # Log successful action
                AuditLogger.log_action(
                    action=action,
                    resource=resource,
                    details={
                        'duration_ms': (datetime.now(BANGKOK_TZ) - start_time).total_seconds() * 1000,
                        'success': True
                    },
                    severity=severity
                )
                
                return result
                
            except Exception as e:
                # Log failed action
                AuditLogger.log_action(
                    action=f'{action}_failed',
                    resource=resource,
                    details={
                        'duration_ms': (datetime.now(BANGKOK_TZ) - start_time).total_seconds() * 1000,
                        'success': False,
                        'error': str(e)
                    },
                    severity='error'
                )
                
                raise
        
        return decorated_function
    return decorator

class AuditAnalyzer:
    """Utility for analyzing audit logs"""
    
    @staticmethod
    def get_user_activity(user_id: int, hours: int = 24) -> Dict[str, Any]:
        """Get user activity summary"""
        since = datetime.now(BANGKOK_TZ) - timedelta(hours=hours)
        
        logs = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= since
        ).order_by(AuditLog.created_at.desc()).all()
        
        activity = {
            'total_actions': len(logs),
            'unique_actions': len(set(log.action for log in logs)),
            'time_range': f'{hours} hours',
            'actions_by_type': {},
            'recent_actions': []
        }
        
        # Count actions by type
        for log in logs:
            action = log.action
            if action not in activity['actions_by_type']:
                activity['actions_by_type'][action] = 0
            activity['actions_by_type'][action] += 1
        
        # Get recent actions
        activity['recent_actions'] = [
            {
                'action': log.action,
                'resource': log.resource,
                'resource_id': log.resource_id,
                'created_at': log.created_at.isoformat(),
                'ip_address': log.ip_address
            }
            for log in logs[:10]
        ]
        
        return activity
    
    @staticmethod
    def get_security_events(hours: int = 24) -> Dict[str, Any]:
        """Get security events summary"""
        since = datetime.now(BANGKOK_TZ) - timedelta(hours=hours)
        
        security_logs = AuditLog.query.filter(
            AuditLog.action.like('security_%'),
            AuditLog.created_at >= since
        ).order_by(AuditLog.created_at.desc()).all()
        
        events = {
            'total_events': len(security_logs),
            'time_range': f'{hours} hours',
            'events_by_type': {},
            'events_by_severity': {},
            'recent_events': []
        }
        
        for log in security_logs:
            # Count by event type
            event_type = log.action.replace('security_', '')
            if event_type not in events['events_by_type']:
                events['events_by_type'][event_type] = 0
            events['events_by_type'][event_type] += 1
            
            # Count by severity
            severity = log.details.get('severity', 'unknown') if log.details else 'unknown'
            if severity not in events['events_by_severity']:
                events['events_by_severity'][severity] = 0
            events['events_by_severity'][severity] += 1
        
        # Get recent events
        events['recent_events'] = [
            {
                'action': log.action,
                'user_id': log.user_id,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat(),
                'details': log.details
            }
            for log in security_logs[:20]
        ]
        
        return events
    
    @staticmethod
    def get_failed_actions(hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed actions"""
        since = datetime.now(BANGKOK_TZ) - timedelta(hours=hours)
        
        failed_logs = AuditLog.query.filter(
            AuditLog.action.like('%_failed'),
            AuditLog.created_at >= since
        ).order_by(AuditLog.created_at.desc()).all()
        
        return [
            {
                'action': log.action,
                'user_id': log.user_id,
                'resource': log.resource,
                'resource_id': log.resource_id,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat(),
                'details': log.details
            }
            for log in failed_logs
        ]
    
    @staticmethod
    def get_admin_activity(hours: int = 24) -> Dict[str, Any]:
        """Get admin activity summary"""
        since = datetime.now(BANGKOK_TZ) - timedelta(hours=hours)
        
        admin_logs = AuditLog.query.filter(
            AuditLog.action.like('admin_%'),
            AuditLog.created_at >= since
        ).order_by(AuditLog.created_at.desc()).all()
        
        activity = {
            'total_actions': len(admin_logs),
            'time_range': f'{hours} hours',
            'actions_by_admin': {},
            'actions_by_type': {},
            'recent_actions': []
        }
        
        for log in admin_logs:
            # Count by admin user
            user_id = log.user_id or 'unknown'
            if user_id not in activity['actions_by_admin']:
                activity['actions_by_admin'][user_id] = 0
            activity['actions_by_admin'][user_id] += 1
            
            # Count by action type
            action = log.action
            if action not in activity['actions_by_type']:
                activity['actions_by_type'][action] = 0
            activity['actions_by_type'][action] += 1
        
        # Get recent actions
        activity['recent_actions'] = [
            {
                'action': log.action,
                'user_id': log.user_id,
                'resource': log.resource,
                'resource_id': log.resource_id,
                'created_at': log.created_at.isoformat(),
                'details': log.details
            }
            for log in admin_logs[:20]
        ]
        
        return activity

class ComplianceReporter:
    """Generate compliance reports from audit logs"""
    
    @staticmethod
    def generate_access_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate data access report for compliance"""
        logs = AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date,
            AuditLog.action.in_(['data_read', 'data_write', 'data_delete'])
        ).all()
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_accesses': len(logs),
            'access_by_user': {},
            'access_by_resource': {},
            'access_by_type': {}
        }
        
        for log in logs:
            # By user
            user_id = str(log.user_id) if log.user_id else 'system'
            if user_id not in report['access_by_user']:
                report['access_by_user'][user_id] = 0
            report['access_by_user'][user_id] += 1
            
            # By resource
            resource = log.resource or 'unknown'
            if resource not in report['access_by_resource']:
                report['access_by_resource'][resource] = 0
            report['access_by_resource'][resource] += 1
            
            # By access type
            access_type = log.action
            if access_type not in report['access_by_type']:
                report['access_by_type'][access_type] = 0
            report['access_by_type'][access_type] += 1
        
        return report

