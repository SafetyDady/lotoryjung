"""
Initialize default group limits in database
Run this script to set up initial limit values
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Rule
from decimal import Decimal

def init_group_limits():
    """Initialize default group limits"""
    app = create_app()
    
    with app.app_context():
        # Default limits for each group
        default_limits = [
            ('2_top', Decimal('1000000.00')),      # 1 million for 2_top
            ('2_bottom', Decimal('800000.00')),    # 800k for 2_bottom  
            ('3_top', Decimal('500000.00')),       # 500k for 3_top
            ('tote', Decimal('300000.00'))         # 300k for tote
        ]
        
        created_count = 0
        updated_count = 0
        
        for field, limit_value in default_limits:
            # Check if rule already exists
            existing_rule = Rule.query.filter(
                Rule.rule_type == 'limit',
                Rule.field == field,
                Rule.number_norm.is_(None)
            ).first()
            
            if existing_rule:
                # Update existing rule
                existing_rule.value = limit_value
                existing_rule.is_active = True
                updated_count += 1
                print(f"Updated limit for {field}: {limit_value:,.2f} บาท")
            else:
                # Create new rule
                new_rule = Rule(
                    rule_type='limit',
                    field=field,
                    number_norm=None,
                    value=limit_value,
                    is_active=True
                )
                db.session.add(new_rule)
                created_count += 1
                print(f"Created limit for {field}: {limit_value:,.2f} บาท")
        
        try:
            db.session.commit()
            print(f"\n✅ เสร็จสิ้น! สร้าง {created_count} รายการ, อัปเดต {updated_count} รายการ")
            
            # Display all current limits
            print("\n📊 ขีดจำกัดปัจจุบัน:")
            all_limits = Rule.query.filter(
                Rule.rule_type == 'limit',
                Rule.number_norm.is_(None),
                Rule.is_active == True
            ).all()
            
            for rule in all_limits:
                field_names = {
                    '2_top': '2 ตัวบน',
                    '2_bottom': '2 ตัวล่าง',
                    '3_top': '3 ตัวบน',
                    'tote': 'โต๊ด'
                }
                field_name = field_names.get(rule.field, rule.field)
                print(f"  {field_name}: {rule.value:,.2f} บาท")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == '__main__':
    init_group_limits()
