from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Order, OrderItem, User
from app import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    # Get user's recent orders
    recent_orders = Order.query.filter_by(user_id=current_user.id)\
                              .order_by(Order.created_at.desc())\
                              .limit(10).all()
    
    # Get statistics
    total_orders = Order.query.filter_by(user_id=current_user.id).count()
    total_amount = db.session.query(db.func.sum(Order.total_amount))\
                            .filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('user/dashboard.html', 
                         recent_orders=recent_orders,
                         total_orders=total_orders,
                         total_amount=total_amount)

@user_bp.route('/orders')
@login_required
def orders():
    """User orders list"""
    if current_user.is_admin():
        return redirect(url_for('admin.orders'))
    
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id)\
                       .order_by(Order.created_at.desc())\
                       .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('user/orders.html', orders=orders)

@user_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('user/order_detail.html', order=order)

@user_bp.route('/new_order')
@login_required
def new_order():
    """New order form"""
    if current_user.is_admin():
        return redirect(url_for('admin.new_order'))
    
    return render_template('user/new_order.html')

@user_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('user/profile.html')

