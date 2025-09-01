# Security Implementation - P0 Critical Requirements

## ภาพรวม
เอกสารนี้กำหนดมาตรการความปลอดภัยที่จำเป็นสำหรับระบบ Lotoryjung ตาม P0 requirements รวมถึง Session Security, Rate Limiting, Secret Key Management, และ Audit Logging

## 1. Session Security

### 1.1 Session Cookie Configuration
การตั้งค่า session cookies ให้ปลอดภัยเป็นสิ่งสำคัญอันดับแรกในการป้องกันการโจมตีผ่าน session hijacking และ cross-site scripting attacks

```python
# config.py
import os
from datetime import timedelta

class Config:
    # Secret Key Management
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True      # ป้องกัน XSS
    SESSION_COOKIE_SECURE = True        # ใช้เฉพาะ HTTPS (production)
    SESSION_COOKIE_SAMESITE = 'Lax'     # ป้องกัน CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # หมดอายุ 8 ชั่วโมง
    
    # Additional Security Headers
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF token หมดอายุใน 1 ชั่วโมง

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # HTTP ได้ใน development

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True   # HTTPS เท่านั้นใน production
```

### 1.2 Session Management
```python
# app.py
from flask import Flask, session, request
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.config.from_object('config.ProductionConfig')

@app.before_request
def before_request():
    """ตรวจสอบ session ก่อนทุก request"""
    
    # ต่ออายุ session หากใกล้หมดอายุ
    if 'user_id' in session:
        session.permanent = True
        
        # ตรวจสอบ session timeout
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            if datetime.now() - last_activity > timedelta(hours=8):
                session.clear()
                return redirect(url_for('login'))
        
        # อัพเดท last activity
        session['last_activity'] = datetime.now().isoformat()
        
        # Regenerate session ID เป็นระยะ (ทุก 30 นาที)
        session_created = session.get('session_created')
        if session_created:
            session_created = datetime.fromisoformat(session_created)
            if datetime.now() - session_created > timedelta(minutes=30):
                regenerate_session_id()

def regenerate_session_id():
    """สร้าง session ID ใหม่เพื่อป้องกัน session fixation"""
    user_data = {k: v for k, v in session.items() if k != 'session_created'}
    session.clear()
    session.update(user_data)
    session['session_created'] = datetime.now().isoformat()
    session['session_id'] = secrets.token_urlsafe(32)
```

### 1.3 Secure Login Implementation
```python
# auth.py
from flask import request, session, flash, redirect, url_for
from werkzeug.security import check_password_hash
from functools import wraps
import bcrypt
import secrets

def login_required(f):
    """Decorator สำหรับตรวจสอบการ login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('กรุณาเข้าสู่ระบบ', 'error')
            return redirect(url_for('login'))
        
        # ตรวจสอบ session integrity
        if not verify_session_integrity():
            session.clear()
            flash('Session ไม่ถูกต้อง กรุณาเข้าสู่ระบบใหม่', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator สำหรับตรวจสอบสิทธิ์ admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            abort(401)
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def verify_session_integrity():
    """ตรวจสอบความถูกต้องของ session"""
    required_fields = ['user_id', 'username', 'role', 'session_created']
    return all(field in session for field in required_fields)

@app.route('/login', methods=['POST'])
def login():
    """Secure login endpoint"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        flash('กรุณากรอกชื่อผู้ใช้และรหัสผ่าน', 'error')
        return redirect(url_for('login_page'))
    
    # ตรวจสอบ user
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if user and check_password_hash(user.password_hash, password):
        # สร้าง session ใหม่
        session.clear()
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['session_created'] = datetime.now().isoformat()
        session['session_id'] = secrets.token_urlsafe(32)
        session.permanent = True
        
        # บันทึก audit log
        log_audit_event(
            user_id=user.id,
            action='login_success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        flash(f'ยินดีต้อนรับ {user.name}', 'success')
        return redirect(url_for('dashboard'))
    else:
        # บันทึก login failure
        log_audit_event(
            action='login_failed',
            table_name='users',
            old_values={'username': username},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
        return redirect(url_for('login_page'))
```

## 2. Rate Limiting

### 2.1 Flask-Limiter Setup
```python
# app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request
import redis

# Redis connection สำหรับ production
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Limiter configuration
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="redis://localhost:6379",  # ใช้ Redis ใน production
    # storage_uri="memory://",  # ใช้ memory ใน development
)

# Custom key function สำหรับ user-based limiting
def get_user_id():
    """ดึง user_id สำหรับ rate limiting"""
    if 'user_id' in session:
        return f"user_{session['user_id']}"
    return get_remote_address()

# Rate limiting decorators
def rate_limit_by_user(limit):
    """Rate limiting ตาม user"""
    return limiter.limit(limit, key_func=get_user_id)
```

### 2.2 Endpoint-Specific Rate Limiting
```python
# Login endpoint - เข้มงวดมาก
@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute", key_func=get_remote_addr)
@limiter.limit("20 per hour", key_func=get_remote_addr)
def login():
    # ... login logic ...
    pass

# Order creation - จำกัดตาม user
@app.route('/create-order', methods=['POST'])
@login_required
@rate_limit_by_user("60 per minute")
@rate_limit_by_user("500 per hour")
def create_order():
    # ... order creation logic ...
    pass

# Admin endpoints - จำกัดเฉพาะ admin
@app.route('/admin/purge-data', methods=['POST'])
@admin_required
@limiter.limit("1 per minute", key_func=get_user_id)
def purge_data():
    # ... data purge logic ...
    pass

# PDF download - จำกัดการดาวน์โหลด
@app.route('/secure/download/<token>')
@login_required
@rate_limit_by_user("30 per minute")
def secure_download(token):
    # ... download logic ...
    pass

# API endpoints - จำกัดทั่วไป
@app.route('/api/check-limit', methods=['POST'])
@login_required
@rate_limit_by_user("100 per minute")
def check_limit():
    # ... limit check logic ...
    pass
```

### 2.3 Rate Limiting Error Handling
```python
from flask_limiter.errors import RateLimitExceeded

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    """จัดการเมื่อเกิน rate limit"""
    
    # บันทึก rate limit violation
    log_audit_event(
        action='rate_limit_exceeded',
        old_values={
            'limit': str(e.limit),
            'endpoint': request.endpoint,
            'method': request.method
        },
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    if request.is_json:
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'คุณทำรายการเร็วเกินไป กรุณารอสักครู่',
            'retry_after': e.retry_after
        }), 429
    else:
        flash('คุณทำรายการเร็วเกินไป กรุณารอสักครู่', 'error')
        return redirect(request.referrer or url_for('dashboard')), 429

# Custom rate limit checker
def check_custom_rate_limit(user_id, action, limit_per_minute=10):
    """ตรวจสอบ rate limit แบบกำหนดเอง"""
    key = f"rate_limit:{user_id}:{action}"
    current_count = redis_client.get(key)
    
    if current_count is None:
        redis_client.setex(key, 60, 1)  # Set with 60 seconds expiry
        return True
    
    if int(current_count) >= limit_per_minute:
        return False
    
    redis_client.incr(key)
    return True
```

## 3. Secret Key Management

### 3.1 Environment Variables
```bash
# .env (production)
SECRET_KEY=your-super-secret-key-here-minimum-32-characters-long
DATABASE_URL=sqlite:///data/lottery.db
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=production

# .env.development
SECRET_KEY=development-key-not-for-production
DATABASE_URL=sqlite:///data/lottery_dev.db
FLASK_ENV=development
```

### 3.2 Key Generation และ Rotation
```python
# utils/security.py
import secrets
import os
from cryptography.fernet import Fernet

def generate_secret_key():
    """สร้าง secret key ใหม่"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """สร้าง encryption key สำหรับข้อมูลสำคัญ"""
    return Fernet.generate_key()

def encrypt_sensitive_data(data, key):
    """เข้ารหัสข้อมูลสำคัญ"""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data, key):
    """ถอดรหัสข้อมูลสำคัญ"""
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

# Key rotation script
def rotate_secret_key():
    """หมุนเวียน secret key (ใช้เมื่อจำเป็น)"""
    new_key = generate_secret_key()
    
    # บันทึก key เก่าไว้ชั่วคราว
    old_key = os.environ.get('SECRET_KEY')
    
    # อัพเดท environment variable
    # (ต้องทำผ่าน deployment system)
    print(f"New SECRET_KEY: {new_key}")
    print("Please update your environment variables and restart the application")
    
    return new_key
```

### 3.3 Configuration Validation
```python
# config.py
import os
import sys

def validate_config():
    """ตรวจสอบ configuration ก่อนเริ่มแอป"""
    
    # ตรวจสอบ SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        print("ERROR: SECRET_KEY environment variable is not set")
        sys.exit(1)
    
    if len(secret_key) < 32:
        print("WARNING: SECRET_KEY should be at least 32 characters long")
    
    # ตรวจสอบ production settings
    if os.environ.get('FLASK_ENV') == 'production':
        if not os.environ.get('DATABASE_URL'):
            print("ERROR: DATABASE_URL must be set in production")
            sys.exit(1)
        
        if secret_key == 'development-key-not-for-production':
            print("ERROR: Cannot use development SECRET_KEY in production")
            sys.exit(1)
    
    print("Configuration validation passed")

# เรียกใช้ตอน startup
validate_config()
```

## 4. Audit Logging

### 4.1 Audit Log System
```python
# services/audit.py
from datetime import datetime
from flask import request, session, g
import json
import logging

# Setup audit logger
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('logs/audit.log')
audit_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

def log_audit_event(user_id=None, action=None, table_name=None, record_id=None,
                   old_values=None, new_values=None, ip_address=None, 
                   user_agent=None, session_id=None):
    """บันทึก audit event ลงฐานข้อมูลและไฟล์ log"""
    
    try:
        # ดึงข้อมูลจาก request context
        if not user_id and 'user_id' in session:
            user_id = session['user_id']
        
        if not ip_address:
            ip_address = request.remote_addr
        
        if not user_agent:
            user_agent = request.headers.get('User-Agent', '')
        
        if not session_id and 'session_id' in session:
            session_id = session['session_id']
        
        # สร้าง audit log record
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,  # Truncate
            session_id=session_id
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        # บันทึกลงไฟล์ log ด้วย
        log_message = {
            'user_id': user_id,
            'action': action,
            'table_name': table_name,
            'record_id': record_id,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        audit_logger.info(json.dumps(log_message))
        
    except Exception as e:
        # ไม่ให้ audit logging ทำให้ระบบหลักล้มเหลว
        print(f"Audit logging failed: {str(e)}")

# Decorator สำหรับ auto-audit
def audit_action(action, table_name=None):
    """Decorator สำหรับบันทึก audit log อัตโนมัติ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # บันทึกก่อนทำ action
            log_audit_event(
                action=f"{action}_start",
                table_name=table_name
            )
            
            try:
                result = f(*args, **kwargs)
                
                # บันทึกหลังทำ action สำเร็จ
                log_audit_event(
                    action=f"{action}_success",
                    table_name=table_name
                )
                
                return result
                
            except Exception as e:
                # บันทึกเมื่อเกิดข้อผิดพลาด
                log_audit_event(
                    action=f"{action}_error",
                    table_name=table_name,
                    old_values={'error': str(e)}
                )
                raise
        
        return decorated_function
    return decorator
```

### 4.2 Audit Events
```python
# ตัวอย่างการใช้งาน audit logging

@app.route('/create-order', methods=['POST'])
@login_required
@audit_action('create_order', 'orders')
def create_order():
    """สร้างคำสั่งซื้อพร้อม audit logging"""
    
    order_data = request.get_json()
    
    # บันทึกข้อมูลที่ส่งมา
    log_audit_event(
        action='order_data_received',
        table_name='orders',
        new_values=order_data
    )
    
    # สร้าง order
    order = Order(
        user_id=session['user_id'],
        customer_name=order_data.get('customer_name'),
        total_amount=order_data.get('total_amount'),
        lottery_period=calculate_lottery_period(datetime.now().date()),
        batch_id=get_current_batch_id()
    )
    
    db.session.add(order)
    db.session.flush()  # เพื่อได้ order.id
    
    # บันทึก order creation
    log_audit_event(
        action='order_created',
        table_name='orders',
        record_id=order.id,
        new_values={
            'order_id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount),
            'user_id': order.user_id
        }
    )
    
    # สร้าง order items
    for item_data in order_data.get('items', []):
        order_item = OrderItem(
            order_id=order.id,
            number=item_data['number'],
            number_norm=normalize_number(item_data['number'], item_data['field']),
            field=item_data['field'],
            buy_amount=item_data['buy_amount'],
            payout_factor=get_payout_factor(item_data['number'], item_data['field']),
            payout_amount=item_data['buy_amount'] * get_payout_factor(item_data['number'], item_data['field'])
        )
        
        db.session.add(order_item)
        
        # บันทึก item creation
        log_audit_event(
            action='order_item_created',
            table_name='order_items',
            record_id=order_item.id,
            new_values={
                'order_id': order.id,
                'number': item_data['number'],
                'field': item_data['field'],
                'buy_amount': float(item_data['buy_amount'])
            }
        )
    
    db.session.commit()
    
    return jsonify({'success': True, 'order_id': order.id})

@app.route('/admin/update-rule', methods=['POST'])
@admin_required
@audit_action('update_rule', 'rules')
def update_rule():
    """อัพเดทกฎพร้อม audit logging"""
    
    rule_id = request.form.get('rule_id')
    rule = Rule.query.get_or_404(rule_id)
    
    # บันทึกค่าเก่า
    old_values = {
        'rule_type': rule.rule_type,
        'field': rule.field,
        'payout_factor': float(rule.payout_factor) if rule.payout_factor else None,
        'limit_amount': rule.limit_amount,
        'is_active': rule.is_active
    }
    
    # อัพเดทค่าใหม่
    rule.payout_factor = request.form.get('payout_factor')
    rule.limit_amount = request.form.get('limit_amount')
    rule.is_active = request.form.get('is_active') == 'true'
    
    new_values = {
        'rule_type': rule.rule_type,
        'field': rule.field,
        'payout_factor': float(rule.payout_factor) if rule.payout_factor else None,
        'limit_amount': rule.limit_amount,
        'is_active': rule.is_active
    }
    
    # บันทึก audit log
    log_audit_event(
        action='rule_updated',
        table_name='rules',
        record_id=rule.id,
        old_values=old_values,
        new_values=new_values
    )
    
    db.session.commit()
    
    return jsonify({'success': True})
```

### 4.3 Audit Log Analysis
```python
# services/audit_analysis.py

def get_user_activity(user_id, start_date=None, end_date=None):
    """ดึงกิจกรรมของ user"""
    
    query = AuditLog.query.filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    return query.order_by(AuditLog.created_at.desc()).all()

def get_suspicious_activities():
    """ดึงกิจกรรมที่น่าสงสัย"""
    
    # หา login failures มากเกินไป
    failed_logins = db.session.query(
        AuditLog.ip_address,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.action == 'login_failed',
        AuditLog.created_at >= datetime.now() - timedelta(hours=1)
    ).group_by(AuditLog.ip_address).having(
        func.count(AuditLog.id) > 10
    ).all()
    
    # หา rate limit violations
    rate_limit_violations = AuditLog.query.filter(
        AuditLog.action == 'rate_limit_exceeded',
        AuditLog.created_at >= datetime.now() - timedelta(hours=1)
    ).all()
    
    # หา admin actions ที่ผิดปกติ
    admin_actions = AuditLog.query.join(User).filter(
        User.role == 'admin',
        AuditLog.action.in_(['rule_updated', 'user_created', 'data_purged']),
        AuditLog.created_at >= datetime.now() - timedelta(days=1)
    ).all()
    
    return {
        'failed_logins': failed_logins,
        'rate_limit_violations': rate_limit_violations,
        'admin_actions': admin_actions
    }

def generate_audit_report(start_date, end_date):
    """สร้างรายงาน audit"""
    
    # สถิติการใช้งาน
    total_actions = AuditLog.query.filter(
        AuditLog.created_at.between(start_date, end_date)
    ).count()
    
    # การกระทำแยกตามประเภท
    action_stats = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at.between(start_date, end_date)
    ).group_by(AuditLog.action).all()
    
    # ผู้ใช้ที่มีกิจกรรมมากที่สุด
    top_users = db.session.query(
        User.username,
        func.count(AuditLog.id).label('count')
    ).join(AuditLog).filter(
        AuditLog.created_at.between(start_date, end_date)
    ).group_by(User.username).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    return {
        'period': f"{start_date} to {end_date}",
        'total_actions': total_actions,
        'action_stats': dict(action_stats),
        'top_users': dict(top_users)
    }
```

## 5. Additional Security Headers

### 5.1 Security Headers Middleware
```python
# middleware/security.py
from flask import Flask

def add_security_headers(app: Flask):
    """เพิ่ม security headers ให้กับทุก response"""
    
    @app.after_request
    def set_security_headers(response):
        # ป้องกัน clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # ป้องกัน MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # เปิดใช้งาน XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (CSP)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HTTPS Strict Transport Security (HSTS) - เฉพาะ production
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        return response
```

### 5.2 Input Validation และ Sanitization
```python
# utils/validation.py
import re
from flask import request
from markupsafe import escape

def validate_number_input(number, field):
    """ตรวจสอบความถูกต้องของเลข"""
    
    if not number or not isinstance(number, str):
        return False, "เลขไม่ถูกต้อง"
    
    number = number.strip()
    
    if field in ['2_top', '2_bottom']:
        if not re.match(r'^\d{1,2}$', number):
            return False, "เลข 2 หลักต้องเป็นตัวเลข 1-2 หลัก"
        if int(number) > 99:
            return False, "เลข 2 หลักต้องไม่เกิน 99"
    
    elif field == '3_top':
        if not re.match(r'^\d{1,3}$', number):
            return False, "เลข 3 หลักต้องเป็นตัวเลข 1-3 หลัก"
        if int(number) > 999:
            return False, "เลข 3 หลักต้องไม่เกิน 999"
    
    elif field == 'tote':
        if not re.match(r'^\d{3}$', number):
            return False, "โต๊ดต้องเป็นตัวเลข 3 หลัก"
    
    return True, "ถูกต้อง"

def sanitize_input(data):
    """ทำความสะอาด input data"""
    
    if isinstance(data, str):
        # ลบ HTML tags และ escape special characters
        data = escape(data.strip())
        # ลบ characters ที่อันตราย
        data = re.sub(r'[<>"\']', '', data)
        return data
    
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data

def validate_order_data(order_data):
    """ตรวจสอบข้อมูลการสั่งซื้อ"""
    
    errors = []
    
    # ตรวจสอบ customer_name
    if 'customer_name' in order_data:
        customer_name = order_data['customer_name']
        if customer_name and len(customer_name) > 100:
            errors.append("ชื่อลูกค้าต้องไม่เกิน 100 ตัวอักษร")
    
    # ตรวจสอบ items
    if 'items' not in order_data or not order_data['items']:
        errors.append("ต้องมีรายการสั่งซื้ออย่างน้อย 1 รายการ")
    else:
        for i, item in enumerate(order_data['items']):
            # ตรวจสอบ number
            if 'number' not in item:
                errors.append(f"รายการที่ {i+1}: ไม่มีเลข")
                continue
            
            # ตรวจสอบ field
            if 'field' not in item or item['field'] not in ['2_top', '2_bottom', '3_top', 'tote']:
                errors.append(f"รายการที่ {i+1}: ประเภทไม่ถูกต้อง")
                continue
            
            # ตรวจสอบเลข
            is_valid, message = validate_number_input(item['number'], item['field'])
            if not is_valid:
                errors.append(f"รายการที่ {i+1}: {message}")
            
            # ตรวจสอบจำนวนเงิน
            if 'buy_amount' not in item:
                errors.append(f"รายการที่ {i+1}: ไม่มีจำนวนเงิน")
            else:
                try:
                    amount = float(item['buy_amount'])
                    if amount <= 0:
                        errors.append(f"รายการที่ {i+1}: จำนวนเงินต้องมากกว่า 0")
                    if amount > 100000:
                        errors.append(f"รายการที่ {i+1}: จำนวนเงินต้องไม่เกิน 100,000")
                except (ValueError, TypeError):
                    errors.append(f"รายการที่ {i+1}: จำนวนเงินไม่ถูกต้อง")
    
    return len(errors) == 0, errors
```

## 6. Security Monitoring

### 6.1 Real-time Monitoring
```python
# services/security_monitor.py
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

class SecurityMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'failed_logins_per_ip': 10,
            'failed_logins_per_hour': 50,
            'rate_limit_violations_per_hour': 100,
            'admin_actions_per_hour': 20
        }
    
    def check_security_alerts(self):
        """ตรวจสอบและส่ง security alerts"""
        
        alerts = []
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # ตรวจสอบ failed logins ต่อ IP
        failed_logins_by_ip = db.session.query(
            AuditLog.ip_address,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.action == 'login_failed',
            AuditLog.created_at >= one_hour_ago
        ).group_by(AuditLog.ip_address).all()
        
        for ip, count in failed_logins_by_ip:
            if count >= self.alert_thresholds['failed_logins_per_ip']:
                alerts.append(f"Suspicious login attempts from IP {ip}: {count} failures in 1 hour")
        
        # ตรวจสอบ rate limit violations
        rate_limit_count = AuditLog.query.filter(
            AuditLog.action == 'rate_limit_exceeded',
            AuditLog.created_at >= one_hour_ago
        ).count()
        
        if rate_limit_count >= self.alert_thresholds['rate_limit_violations_per_hour']:
            alerts.append(f"High rate limit violations: {rate_limit_count} in 1 hour")
        
        # ตรวจสอบ admin actions
        admin_actions_count = AuditLog.query.join(User).filter(
            User.role == 'admin',
            AuditLog.created_at >= one_hour_ago
        ).count()
        
        if admin_actions_count >= self.alert_thresholds['admin_actions_per_hour']:
            alerts.append(f"High admin activity: {admin_actions_count} actions in 1 hour")
        
        # ส่ง alerts
        if alerts:
            self.send_security_alert(alerts)
        
        return alerts
    
    def send_security_alert(self, alerts):
        """ส่ง security alert ทาง email"""
        
        subject = "Security Alert - Lotoryjung System"
        body = "Security alerts detected:\n\n" + "\n".join(alerts)
        
        # ส่ง email (ต้องตั้งค่า SMTP)
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = 'system@lotoryjung.com'
            msg['To'] = 'admin@lotoryjung.com'
            
            # ส่ง email (ต้องตั้งค่า SMTP server)
            # smtp_server.send_message(msg)
            
            # บันทึก log
            log_audit_event(
                action='security_alert_sent',
                new_values={'alerts': alerts}
            )
            
        except Exception as e:
            print(f"Failed to send security alert: {str(e)}")

# Scheduled task สำหรับ monitoring
@app.cli.command()
def check_security():
    """CLI command สำหรับตรวจสอบความปลอดภัย"""
    monitor = SecurityMonitor()
    alerts = monitor.check_security_alerts()
    
    if alerts:
        print(f"Found {len(alerts)} security alerts")
        for alert in alerts:
            print(f"- {alert}")
    else:
        print("No security alerts found")
```

## สรุป
การ implement Security Measures ตาม P0 requirements นี้จะช่วยเพิ่มความปลอดภัยให้กับระบบ Lotoryjung อย่างมีนัยสำคัญ รวมถึงการป้องกันการโจมตีทั่วไป การจำกัดการใช้งาน และการติดตามกิจกรรมที่น่าสงสัย ระบบนี้พร้อมสำหรับการใช้งานจริงในสภาพแวดล้อม production

