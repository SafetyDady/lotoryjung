from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, Order, OrderItem, Rule, BlockedNumber, AuditLog, NumberTotal
from app import db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.filter_by(role='user').count()
    total_orders = Order.query.count()
    total_amount = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Get recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_orders=total_orders,
                         total_amount=total_amount,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         recent_logs=recent_logs)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Users management"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc())\
                     .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """Orders management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.created_at.desc())\
                 .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@admin_bp.route('/rules')
@login_required
@admin_required
def rules():
    """Rules management"""
    payout_rules = Rule.query.filter_by(rule_type='payout', is_active=True).all()
    limit_rules = Rule.query.filter_by(rule_type='limit', is_active=True).all()
    
    return render_template('admin/rules.html', 
                         payout_rules=payout_rules,
                         limit_rules=limit_rules)

@admin_bp.route('/blocked_numbers')
@login_required
@admin_required
def blocked_numbers():
    """Blocked numbers management"""
    page = request.args.get('page', 1, type=int)
    blocked_numbers = BlockedNumber.query.filter_by(is_active=True)\
                                        .order_by(BlockedNumber.created_at.desc())\
                                        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/blocked_numbers.html', blocked_numbers=blocked_numbers)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Reports and analytics"""
    return render_template('admin/reports.html')

@admin_bp.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    """Audit logs"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    
    query = AuditLog.query
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    logs = query.order_by(AuditLog.created_at.desc())\
              .paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/audit_logs.html', logs=logs, action_filter=action_filter)

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """System settings"""
    return render_template('admin/settings.html')

