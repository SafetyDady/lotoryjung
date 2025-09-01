from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Order, OrderItem, Rule, BlockedNumber, NumberTotal
from app import db
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@api_bp.route('/rules/<field>')
@login_required
def get_rules(field):
    """Get rules for a specific field"""
    payout_rule = Rule.query.filter_by(
        rule_type='payout', 
        field=field, 
        is_active=True
    ).first()
    
    limit_rule = Rule.query.filter_by(
        rule_type='limit', 
        field=field, 
        is_active=True
    ).first()
    
    return jsonify({
        'payout_rate': float(payout_rule.value) if payout_rule else 0,
        'limit': float(limit_rule.value) if limit_rule else 0
    })

@api_bp.route('/blocked_numbers/<field>')
@login_required
def get_blocked_numbers(field):
    """Get blocked numbers for a specific field"""
    blocked = BlockedNumber.query.filter_by(
        field=field, 
        is_active=True
    ).all()
    
    return jsonify({
        'blocked_numbers': [b.number_norm for b in blocked]
    })

@api_bp.route('/number_totals/<field>/<number>')
@login_required
def get_number_total(field, number):
    """Get current total for a specific number"""
    # Get current batch_id (this would be calculated based on lottery period)
    batch_id = "20240901"  # Placeholder
    
    total = NumberTotal.query.filter_by(
        batch_id=batch_id,
        field=field,
        number_norm=number
    ).first()
    
    return jsonify({
        'current_total': float(total.total_amount) if total else 0,
        'order_count': total.order_count if total else 0
    })

@api_bp.route('/validate_order', methods=['POST'])
@login_required
def validate_order():
    """Validate order before submission"""
    data = request.get_json()
    
    # Validate each item
    errors = []
    total_amount = 0
    
    for item in data.get('items', []):
        field = item.get('field')
        number = item.get('number')
        amount = float(item.get('amount', 0))
        
        # Check if number is blocked
        blocked = BlockedNumber.query.filter_by(
            field=field,
            number_norm=number,
            is_active=True
        ).first()
        
        if blocked:
            errors.append(f'เลข {number} ในประเภท {field} ถูกอั้น')
            continue
        
        # Check limit
        # ... (implement limit checking logic)
        
        total_amount += amount
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'total_amount': total_amount
    })

