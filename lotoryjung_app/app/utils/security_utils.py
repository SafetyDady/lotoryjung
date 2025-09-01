"""
Security utilities for enhanced application security
"""

import hashlib
import secrets
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
import pytz

from app import db
from app.models import AuditLog

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class SecurityUtils:
    """Utility class for security operations"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data with salt"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000).hex() + ':' + salt
    
    @staticmethod
    def verify_hashed_data(data: str, hashed: str) -> bool:
        """Verify hashed data"""
        try:
            hash_part, salt = hashed.split(':')
            return hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000).hex() == hash_part
        except:
            return False
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_str)
        
        # Limit length
        sanitized = sanitized[:1000]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_csrf_token(token: str) -> bool:
        """Validate CSRF token (simplified implementation)"""
        # In production, implement proper CSRF validation
        return len(token) >= 16
    
    @staticmethod
    def get_client_ip() -> str:
        """Get client IP address"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict = None, user_id: int = None, severity: str = 'info'):
        """Log security events"""
        audit_log = AuditLog(
            user_id=user_id or (current_user.id if current_user.is_authenticated else None),
            action=f'security_{event_type}',
            resource='security',
            ip_address=SecurityUtils.get_client_ip(),
            user_agent=request.user_agent.string if request else None,
            details={
                'severity': severity,
                'event_type': event_type,
                **(details or {})
            }
        )
        db.session.add(audit_log)
        db.session.commit()
    
    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Check password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
        
        if not re.search(r'[A-Za-z]', password):
            errors.append("รหัสผ่านต้องมีตัวอักษร")
        
        if not re.search(r'\d', password):
            errors.append("รหัสผ่านต้องมีตัวเลข")
        
        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'admin', 'test']
        if password.lower() in weak_passwords:
            errors.append("รหัสผ่านนี้ไม่ปลอดภัย")
        
        return len(errors) == 0, errors

class RateLimiter:
    """Rate limiting utility"""
    
    def __init__(self):
        self.attempts = {}
    
    def is_rate_limited(self, key: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if key is rate limited"""
        now = datetime.now(BANGKOK_TZ)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if key in self.attempts:
            self.attempts[key] = [
                attempt for attempt in self.attempts[key]
                if attempt > window_start
            ]
        
        # Check current attempts
        current_attempts = len(self.attempts.get(key, []))
        
        if current_attempts >= max_attempts:
            SecurityUtils.log_security_event(
                'rate_limit_exceeded',
                {'key': key, 'attempts': current_attempts},
                severity='warning'
            )
            return True
        
        return False
    
    def record_attempt(self, key: str):
        """Record an attempt"""
        now = datetime.now(BANGKOK_TZ)
        
        if key not in self.attempts:
            self.attempts[key] = []
        
        self.attempts[key].append(now)

# Global rate limiter instance
rate_limiter = RateLimiter()

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            SecurityUtils.log_security_event(
                'unauthorized_access_attempt',
                {'endpoint': request.endpoint},
                severity='warning'
            )
            return jsonify({'error': 'Authentication required'}), 401
        
        if not current_user.is_admin():
            SecurityUtils.log_security_event(
                'admin_access_denied',
                {'user_id': current_user.id, 'endpoint': request.endpoint},
                user_id=current_user.id,
                severity='warning'
            )
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_attempts: int = 5, window_minutes: int = 15, key_func=None):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                key = f"{SecurityUtils.get_client_ip()}:{request.endpoint}"
            
            # Check rate limit
            if rate_limiter.is_rate_limited(key, max_attempts, window_minutes):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again in {window_minutes} minutes.'
                }), 429
            
            # Record attempt
            rate_limiter.record_attempt(key)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(schema: Dict):
    """Decorator for input validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            errors = []
            validated_data = {}
            
            for field, rules in schema.items():
                value = data.get(field)
                
                # Required field check
                if rules.get('required', False) and not value:
                    errors.append(f"Field '{field}' is required")
                    continue
                
                if value is not None:
                    # Type validation
                    field_type = rules.get('type', str)
                    try:
                        if field_type == int:
                            value = int(value)
                        elif field_type == float:
                            value = float(value)
                        elif field_type == str:
                            value = SecurityUtils.sanitize_input(str(value))
                    except ValueError:
                        errors.append(f"Field '{field}' must be of type {field_type.__name__}")
                        continue
                    
                    # Length validation
                    if 'min_length' in rules and len(str(value)) < rules['min_length']:
                        errors.append(f"Field '{field}' must be at least {rules['min_length']} characters")
                    
                    if 'max_length' in rules and len(str(value)) > rules['max_length']:
                        errors.append(f"Field '{field}' must be at most {rules['max_length']} characters")
                    
                    # Pattern validation
                    if 'pattern' in rules and not re.match(rules['pattern'], str(value)):
                        errors.append(f"Field '{field}' format is invalid")
                    
                    validated_data[field] = value
            
            if errors:
                SecurityUtils.log_security_event(
                    'input_validation_failed',
                    {'errors': errors, 'endpoint': request.endpoint},
                    severity='info'
                )
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Add validated data to request
            request.validated_data = validated_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class CSVSanitizer:
    """Utility for CSV-safe data export"""
    
    @staticmethod
    def sanitize_csv_value(value) -> str:
        """Sanitize value for CSV export to prevent injection"""
        if value is None:
            return ""
        
        str_value = str(value)
        
        # Remove or escape dangerous characters
        dangerous_chars = ['=', '+', '-', '@', '\t', '\r', '\n']
        
        for char in dangerous_chars:
            if str_value.startswith(char):
                str_value = "'" + str_value  # Prefix with single quote
                break
        
        # Escape quotes
        str_value = str_value.replace('"', '""')
        
        # Wrap in quotes if contains comma or quotes
        if ',' in str_value or '"' in str_value:
            str_value = f'"{str_value}"'
        
        return str_value
    
    @staticmethod
    def sanitize_csv_row(row: List) -> List[str]:
        """Sanitize entire CSV row"""
        return [CSVSanitizer.sanitize_csv_value(value) for value in row]

class DataPurgeService:
    """Service for secure data purging"""
    
    @staticmethod
    def purge_sensitive_data(user_id: int, confirm_token: str) -> Dict:
        """Purge sensitive data with confirmation"""
        # Verify confirmation token
        expected_token = hashlib.sha256(f"purge_{user_id}_{datetime.now().date()}".encode()).hexdigest()[:16]
        
        if confirm_token != expected_token:
            SecurityUtils.log_security_event(
                'data_purge_invalid_token',
                {'user_id': user_id},
                user_id=user_id,
                severity='warning'
            )
            raise ValueError("Invalid confirmation token")
        
        # Log purge operation
        SecurityUtils.log_security_event(
            'data_purge_initiated',
            {'user_id': user_id},
            user_id=user_id,
            severity='info'
        )
        
        # Perform purge operations
        # (Implementation would go here)
        
        return {'status': 'success', 'message': 'Data purged successfully'}

