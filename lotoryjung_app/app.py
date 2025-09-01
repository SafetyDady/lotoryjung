#!/usr/bin/env python3
"""
Lotoryjung Application
Main application entry point
"""

import os
from app import create_app, db, socketio
from app.models import User, Rule, BlockedNumber, Order, OrderItem, NumberTotal, DownloadToken, AuditLog
from flask_migrate import upgrade
from werkzeug.security import generate_password_hash

# Create Flask application
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Make database models available in shell context"""
    return {
        'db': db,
        'User': User,
        'Rule': Rule,
        'BlockedNumber': BlockedNumber,
        'Order': Order,
        'OrderItem': OrderItem,
        'NumberTotal': NumberTotal,
        'DownloadToken': DownloadToken,
        'AuditLog': AuditLog
    }

@app.cli.command()
def init_db():
    """Initialize database with tables and initial data"""
    print("Creating database tables...")
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            name='Administrator',
            username='admin',
            role='admin'
        )
        admin.set_password('admin123')  # Change this in production
        db.session.add(admin)
        print("Created admin user (username: admin, password: admin123)")
    
    # Create test user if not exists
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        test_user = User(
            name='Test User',
            username='testuser',
            role='user'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        print("Created test user (username: testuser, password: test123)")
    
    # Create default rules
    default_rules = [
        # Payout rates
        {'rule_type': 'payout', 'field': '2_top', 'number_norm': None, 'value': 90.0},
        {'rule_type': 'payout', 'field': '2_bottom', 'number_norm': None, 'value': 90.0},
        {'rule_type': 'payout', 'field': '3_top', 'number_norm': None, 'value': 900.0},
        {'rule_type': 'payout', 'field': 'tote', 'number_norm': None, 'value': 150.0},
        
        # Default limits
        {'rule_type': 'limit', 'field': '2_top', 'number_norm': None, 'value': 10000.0},
        {'rule_type': 'limit', 'field': '2_bottom', 'number_norm': None, 'value': 10000.0},
        {'rule_type': 'limit', 'field': '3_top', 'number_norm': None, 'value': 5000.0},
        {'rule_type': 'limit', 'field': 'tote', 'number_norm': None, 'value': 5000.0},
    ]
    
    for rule_data in default_rules:
        existing_rule = Rule.query.filter_by(
            rule_type=rule_data['rule_type'],
            field=rule_data['field'],
            number_norm=rule_data['number_norm']
        ).first()
        
        if not existing_rule:
            rule = Rule(**rule_data)
            db.session.add(rule)
    
    # Create some sample blocked numbers
    sample_blocked = [
        {'field': '2_top', 'number_norm': '00', 'reason': 'Popular number'},
        {'field': '2_top', 'number_norm': '11', 'reason': 'Popular number'},
        {'field': '3_top', 'number_norm': '123', 'reason': 'Popular number'},
    ]
    
    for blocked_data in sample_blocked:
        existing_blocked = BlockedNumber.query.filter_by(
            field=blocked_data['field'],
            number_norm=blocked_data['number_norm']
        ).first()
        
        if not existing_blocked:
            blocked = BlockedNumber(**blocked_data)
            db.session.add(blocked)
    
    db.session.commit()
    print("Database initialized successfully!")

@app.cli.command()
def reset_db():
    """Reset database (drop all tables and recreate)"""
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Database reset complete!")

if __name__ == '__main__':
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5002, debug=True, allow_unsafe_werkzeug=True)

