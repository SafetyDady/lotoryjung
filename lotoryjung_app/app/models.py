from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pytz
from app import db

# Timezone configuration
BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # user, admin
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(BANGKOK_TZ))
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Rule(db.Model):
    """Rule model for business rules and configurations"""
    __tablename__ = 'rules'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_type = db.Column(db.String(50), nullable=False)  # limit, blocked, payout
    field = db.Column(db.String(20), nullable=False)  # 2_top, 2_bottom, 3_top, tote
    number_norm = db.Column(db.String(10), nullable=True)  # normalized number
    value = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(BANGKOK_TZ))
    
    __table_args__ = (
        db.UniqueConstraint('rule_type', 'field', 'number_norm', name='unique_rule'),
        db.Index('idx_rule_lookup', 'rule_type', 'field', 'number_norm', 'is_active'),
    )
    
    def __repr__(self):
        return f'<Rule {self.rule_type}:{self.field}:{self.number_norm}={self.value}>'

class BlockedNumber(db.Model):
    """Blocked numbers model"""
    __tablename__ = 'blocked_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    field = db.Column(db.String(20), nullable=False)  # 2_top, 2_bottom, 3_top, tote
    number_norm = db.Column(db.String(10), nullable=False)  # normalized number
    reason = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ))
    
    __table_args__ = (
        db.UniqueConstraint('field', 'number_norm', name='unique_blocked_number'),
        db.Index('idx_blocked_lookup', 'field', 'number_norm', 'is_active'),
    )
    
    def __repr__(self):
        return f'<BlockedNumber {self.field}:{self.number_norm}>'

class Order(db.Model):
    """Order model for purchase orders"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    customer_name = db.Column(db.String(100), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, cancelled
    lottery_period = db.Column(db.Date, nullable=False, index=True)  # วันที่หวยออก
    batch_id = db.Column(db.String(20), nullable=False, index=True)  # batch identifier
    pdf_path = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ), index=True)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(BANGKOK_TZ))
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    download_tokens = db.relationship('DownloadToken', backref='order', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_order_period_batch', 'lottery_period', 'batch_id'),
        db.Index('idx_order_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    """Order item model for individual number purchases"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    field = db.Column(db.String(20), nullable=False)  # 2_top, 2_bottom, 3_top, tote
    number_input = db.Column(db.String(10), nullable=False)  # original input
    number_norm = db.Column(db.String(10), nullable=False, index=True)  # normalized number
    buy_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payout_rate = db.Column(db.Numeric(5, 2), nullable=False)  # payout multiplier
    potential_payout = db.Column(db.Numeric(10, 2), nullable=False)  # calculated payout
    is_blocked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ))
    
    __table_args__ = (
        db.UniqueConstraint('order_id', 'field', 'number_norm', name='unique_order_item'),
        db.Index('idx_item_field_number', 'field', 'number_norm'),
        db.Index('idx_item_order_field', 'order_id', 'field'),
    )
    
    def __repr__(self):
        return f'<OrderItem {self.field}:{self.number_norm}@{self.buy_amount}>'

class NumberTotal(db.Model):
    """Number totals for limit tracking"""
    __tablename__ = 'number_totals'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(20), nullable=False, index=True)
    field = db.Column(db.String(20), nullable=False)
    number_norm = db.Column(db.String(10), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    order_count = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ))
    
    __table_args__ = (
        db.UniqueConstraint('batch_id', 'field', 'number_norm', name='unique_number_total'),
        db.Index('idx_total_batch_field', 'batch_id', 'field'),
    )
    
    def __repr__(self):
        return f'<NumberTotal {self.batch_id}:{self.field}:{self.number_norm}={self.total_amount}>'

class DownloadToken(db.Model):
    """Secure download tokens for PDF receipts"""
    __tablename__ = 'download_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ))
    
    __table_args__ = (
        db.Index('idx_token_user', 'user_id', 'expires_at'),
    )
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.now(BANGKOK_TZ) > self.expires_at.replace(tzinfo=BANGKOK_TZ)
    
    def __repr__(self):
        return f'<DownloadToken {self.token[:8]}...>'

class AuditLog(db.Model):
    """Audit log for security tracking"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # login, logout, create_order, etc.
    resource = db.Column(db.String(50), nullable=True)  # order, user, etc.
    resource_id = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(BANGKOK_TZ), index=True)
    
    __table_args__ = (
        db.Index('idx_audit_user_action', 'user_id', 'action'),
        db.Index('idx_audit_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<AuditLog {self.action}:{self.resource}:{self.resource_id}>'

