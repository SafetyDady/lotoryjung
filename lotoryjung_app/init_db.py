#!/usr/bin/env python3
"""
Database initialization script
"""

from app import create_app, db
from app.models import User, Rule, BlockedNumber

def init_database():
    """Initialize database with tables and initial data"""
    app = create_app()
    
    with app.app_context():
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

if __name__ == '__main__':
    init_database()

