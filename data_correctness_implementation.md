# Data Correctness Implementation - P0 Critical Requirements

## ภาพรวม
เอกสารนี้กำหนดการปรับปรุงความถูกต้องของข้อมูลในระบบ Lotoryjung ตาม P0 requirements รวมถึงการ Canonicalize โต๊ด, การ Normalize เลข, และการป้องกันข้อมูลซ้ำด้วย Unique Constraints

## 1. Number Canonicalization และ Normalization

### 1.1 หลักการ Canonicalization
การ Canonicalize คือการแปลงข้อมูลให้อยู่ในรูปแบบมาตรฐานเดียวกัน เพื่อให้การเปรียบเทียบและการค้นหาทำได้อย่างถูกต้อง โดยเฉพาะสำหรับโต๊ดที่มีการเรียงลำดับตัวเลขที่แตกต่างกันแต่มีความหมายเดียวกัน

```python
# utils/number_utils.py
import re
from typing import Tuple, Optional

def normalize_number(number: str, field: str) -> str:
    """
    ปรับมาตรฐานเลขตาม field ที่กำหนด
    
    Args:
        number: เลขที่ต้องการปรับมาตรฐาน
        field: ประเภทของเลข ('2_top', '2_bottom', '3_top', 'tote')
    
    Returns:
        เลขที่ปรับมาตรฐานแล้ว
    
    Raises:
        ValueError: เมื่อเลขหรือ field ไม่ถูกต้อง
    """
    
    if not number or not isinstance(number, str):
        raise ValueError("Number must be a non-empty string")
    
    # ลบช่องว่างและตัวอักษรที่ไม่ใช่ตัวเลข
    number = re.sub(r'[^\d]', '', number.strip())
    
    if not number:
        raise ValueError("Number must contain at least one digit")
    
    if field in ['2_top', '2_bottom']:
        # เลข 2 หลัก: 00-99
        if len(number) > 2:
            raise ValueError(f"2-digit number cannot be longer than 2 digits: {number}")
        
        normalized = number.zfill(2)
        
        if int(normalized) > 99:
            raise ValueError(f"2-digit number cannot exceed 99: {normalized}")
        
        return normalized
    
    elif field == '3_top':
        # เลข 3 หลัก: 000-999
        if len(number) > 3:
            raise ValueError(f"3-digit number cannot be longer than 3 digits: {number}")
        
        normalized = number.zfill(3)
        
        if int(normalized) > 999:
            raise ValueError(f"3-digit number cannot exceed 999: {normalized}")
        
        return normalized
    
    elif field == 'tote':
        # โต๊ด: ต้องเป็น 3 หลักและทำ canonicalization
        if len(number) != 3:
            raise ValueError(f"Tote number must be exactly 3 digits: {number}")
        
        return canonicalize_tote(number)
    
    else:
        raise ValueError(f"Invalid field: {field}")

def canonicalize_tote(number: str) -> str:
    """
    แปลงโต๊ดให้เป็นรูปแบบมาตรฐาน (เรียงจากน้อยไปมาก)
    
    Args:
        number: เลขโต๊ด 3 หลัก
    
    Returns:
        เลขโต๊ดที่เรียงลำดับแล้ว
    
    Examples:
        canonicalize_tote("367") -> "367"
        canonicalize_tote("736") -> "367"
        canonicalize_tote("673") -> "367"
    """
    
    if not number or len(number) != 3:
        raise ValueError("Tote number must be exactly 3 digits")
    
    if not number.isdigit():
        raise ValueError("Tote number must contain only digits")
    
    # เรียงตัวเลขจากน้อยไปมาก
    sorted_digits = sorted(number)
    return ''.join(sorted_digits)

def validate_number_format(number: str, field: str) -> Tuple[bool, str]:
    """
    ตรวจสอบรูปแบบของเลขก่อนการ normalize
    
    Args:
        number: เลขที่ต้องการตรวจสอบ
        field: ประเภทของเลข
    
    Returns:
        Tuple ของ (is_valid, error_message)
    """
    
    try:
        normalize_number(number, field)
        return True, "Valid"
    except ValueError as e:
        return False, str(e)

def get_all_tote_permutations(canonical_tote: str) -> list:
    """
    สร้างรายการโต๊ดทั้งหมดที่เป็นไปได้จาก canonical form
    
    Args:
        canonical_tote: โต๊ดในรูปแบบ canonical
    
    Returns:
        รายการโต๊ดทั้งหมดที่เป็นไปได้
    
    Examples:
        get_all_tote_permutations("367") -> ["367", "376", "637", "673", "736", "763"]
    """
    
    from itertools import permutations
    
    if len(canonical_tote) != 3:
        raise ValueError("Canonical tote must be 3 digits")
    
    # สร้าง permutations ทั้งหมด
    perms = set()
    for perm in permutations(canonical_tote):
        perms.add(''.join(perm))
    
    return sorted(list(perms))

# ตัวอย่างการใช้งาน
def test_normalization():
    """ทดสอบการ normalize และ canonicalize"""
    
    test_cases = [
        # 2 หลักบน
        ("5", "2_top", "05"),
        ("25", "2_top", "25"),
        ("99", "2_top", "99"),
        
        # 2 หลักล่าง
        ("7", "2_bottom", "07"),
        ("34", "2_bottom", "34"),
        
        # 3 หลักบน
        ("1", "3_top", "001"),
        ("123", "3_top", "123"),
        ("999", "3_top", "999"),
        
        # โต๊ด
        ("367", "tote", "367"),
        ("736", "tote", "367"),
        ("673", "tote", "367"),
        ("111", "tote", "111"),
        ("123", "tote", "123"),
    ]
    
    for input_num, field, expected in test_cases:
        try:
            result = normalize_number(input_num, field)
            status = "✓" if result == expected else "✗"
            print(f"{status} {input_num} ({field}) -> {result} (expected: {expected})")
        except Exception as e:
            print(f"✗ {input_num} ({field}) -> ERROR: {e}")

if __name__ == "__main__":
    test_normalization()
```

### 1.2 Advanced Normalization Functions
```python
# utils/advanced_normalization.py

class NumberNormalizer:
    """คลาสสำหรับจัดการการ normalize เลขอย่างครอบคลุม"""
    
    def __init__(self):
        self.field_configs = {
            '2_top': {'min_length': 1, 'max_length': 2, 'pad_length': 2, 'max_value': 99},
            '2_bottom': {'min_length': 1, 'max_length': 2, 'pad_length': 2, 'max_value': 99},
            '3_top': {'min_length': 1, 'max_length': 3, 'pad_length': 3, 'max_value': 999},
            'tote': {'min_length': 3, 'max_length': 3, 'pad_length': 3, 'max_value': 999, 'canonicalize': True}
        }
    
    def normalize_batch(self, numbers_and_fields: list) -> list:
        """
        Normalize หลายเลขพร้อมกัน
        
        Args:
            numbers_and_fields: รายการ tuple ของ (number, field)
        
        Returns:
            รายการผลลัพธ์ที่ normalize แล้ว
        """
        
        results = []
        for number, field in numbers_and_fields:
            try:
                normalized = normalize_number(number, field)
                results.append({
                    'original': number,
                    'field': field,
                    'normalized': normalized,
                    'success': True,
                    'error': None
                })
            except Exception as e:
                results.append({
                    'original': number,
                    'field': field,
                    'normalized': None,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def validate_and_normalize_order_items(self, items: list) -> Tuple[bool, list, list]:
        """
        ตรวจสอบและ normalize รายการสั่งซื้อทั้งหมด
        
        Args:
            items: รายการ order items
        
        Returns:
            Tuple ของ (all_valid, normalized_items, errors)
        """
        
        normalized_items = []
        errors = []
        all_valid = True
        
        for i, item in enumerate(items):
            try:
                # ตรวจสอบฟิลด์ที่จำเป็น
                if 'number' not in item or 'field' not in item:
                    errors.append(f"รายการที่ {i+1}: ขาดข้อมูล number หรือ field")
                    all_valid = False
                    continue
                
                # Normalize number
                normalized_number = normalize_number(item['number'], item['field'])
                
                # สร้าง normalized item
                normalized_item = item.copy()
                normalized_item['number_norm'] = normalized_number
                normalized_item['original_number'] = item['number']
                
                # เพิ่มข้อมูลเพิ่มเติมสำหรับโต๊ด
                if item['field'] == 'tote':
                    normalized_item['tote_permutations'] = get_all_tote_permutations(normalized_number)
                    normalized_item['is_canonical'] = item['number'] == normalized_number
                
                normalized_items.append(normalized_item)
                
            except Exception as e:
                errors.append(f"รายการที่ {i+1}: {str(e)}")
                all_valid = False
        
        return all_valid, normalized_items, errors
    
    def find_duplicate_numbers(self, items: list) -> list:
        """
        ค้นหาเลขที่ซ้ำกันในรายการสั่งซื้อ
        
        Args:
            items: รายการ normalized items
        
        Returns:
            รายการเลขที่ซ้ำกัน
        """
        
        seen = {}
        duplicates = []
        
        for i, item in enumerate(items):
            key = f"{item['field']}:{item['number_norm']}"
            
            if key in seen:
                duplicates.append({
                    'number_norm': item['number_norm'],
                    'field': item['field'],
                    'positions': [seen[key], i],
                    'original_numbers': [items[seen[key]]['original_number'], item['original_number']]
                })
            else:
                seen[key] = i
        
        return duplicates

# Integration กับ Order Processing
def process_order_with_normalization(order_data: dict) -> dict:
    """
    ประมวลผลคำสั่งซื้อพร้อมการ normalize
    
    Args:
        order_data: ข้อมูลคำสั่งซื้อ
    
    Returns:
        ผลลัพธ์การประมวลผล
    """
    
    normalizer = NumberNormalizer()
    
    # ตรวจสอบและ normalize items
    items = order_data.get('items', [])
    all_valid, normalized_items, errors = normalizer.validate_and_normalize_order_items(items)
    
    if not all_valid:
        return {
            'success': False,
            'errors': errors,
            'normalized_items': normalized_items
        }
    
    # ตรวจสอบเลขซ้ำ
    duplicates = normalizer.find_duplicate_numbers(normalized_items)
    if duplicates:
        duplicate_errors = []
        for dup in duplicates:
            duplicate_errors.append(
                f"เลข {dup['number_norm']} ({dup['field']}) ซ้ำกัน: "
                f"{', '.join(dup['original_numbers'])}"
            )
        
        return {
            'success': False,
            'errors': duplicate_errors,
            'duplicates': duplicates,
            'normalized_items': normalized_items
        }
    
    return {
        'success': True,
        'normalized_items': normalized_items,
        'total_items': len(normalized_items)
    }
```

## 2. Unique Constraints Implementation

### 2.1 Database Constraints
```sql
-- สร้าง unique constraints ป้องกันข้อมูลซ้ำ

-- ป้องกันเลขซ้ำใน order เดียวกัน
ALTER TABLE order_items ADD CONSTRAINT unique_order_field_number 
UNIQUE (order_id, field, number_norm);

-- ป้องกัน rule ซ้ำ
ALTER TABLE rules ADD CONSTRAINT unique_rule_definition 
UNIQUE (rule_type, field, number_norm, condition_type, batch_id);

-- ป้องกัน blocked number ซ้ำ
ALTER TABLE blocked_numbers ADD CONSTRAINT unique_blocked_number 
UNIQUE (number_norm, field, batch_id);

-- ป้องกัน download token ซ้ำ
ALTER TABLE download_tokens ADD CONSTRAINT unique_download_token 
UNIQUE (token);

-- ป้องกัน order number ซ้ำ
ALTER TABLE orders ADD CONSTRAINT unique_order_number 
UNIQUE (order_number);
```

### 2.2 Application-Level Validation
```python
# services/validation_service.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

class ValidationService:
    """บริการตรวจสอบความถูกต้องของข้อมูล"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def validate_order_uniqueness(self, order_id: int, items: list) -> Tuple[bool, list]:
        """
        ตรวจสอบความซ้ำของเลขใน order
        
        Args:
            order_id: ID ของ order
            items: รายการ items ที่ต้องการตรวจสอบ
        
        Returns:
            Tuple ของ (is_valid, error_messages)
        """
        
        errors = []
        
        # ตรวจสอบซ้ำภายใน items ที่ส่งมา
        seen_combinations = set()
        for i, item in enumerate(items):
            combination = (item['field'], item['number_norm'])
            if combination in seen_combinations:
                errors.append(
                    f"รายการที่ {i+1}: เลข {item['number_norm']} ({item['field']}) ซ้ำกัน"
                )
            seen_combinations.add(combination)
        
        # ตรวจสอบซ้ำกับข้อมูลในฐานข้อมูล (สำหรับการแก้ไข order)
        if order_id:
            for item in items:
                existing = self.db.query(OrderItem).filter(
                    and_(
                        OrderItem.order_id == order_id,
                        OrderItem.field == item['field'],
                        OrderItem.number_norm == item['number_norm']
                    )
                ).first()
                
                if existing and existing.id != item.get('id'):
                    errors.append(
                        f"เลข {item['number_norm']} ({item['field']}) มีอยู่ในคำสั่งซื้อนี้แล้ว"
                    )
        
        return len(errors) == 0, errors
    
    def validate_rule_uniqueness(self, rule_data: dict, rule_id: int = None) -> Tuple[bool, str]:
        """
        ตรวจสอบความซ้ำของกฎ
        
        Args:
            rule_data: ข้อมูลกฎ
            rule_id: ID ของกฎ (สำหรับการแก้ไข)
        
        Returns:
            Tuple ของ (is_valid, error_message)
        """
        
        existing = self.db.query(Rule).filter(
            and_(
                Rule.rule_type == rule_data['rule_type'],
                Rule.field == rule_data['field'],
                Rule.number_norm == rule_data.get('number_norm'),
                Rule.condition_type == rule_data.get('condition_type', 'normal'),
                Rule.batch_id == rule_data.get('batch_id')
            )
        ).first()
        
        if existing and (not rule_id or existing.id != rule_id):
            return False, f"กฎนี้มีอยู่แล้ว: {rule_data['rule_type']} {rule_data['field']}"
        
        return True, "Valid"
    
    def validate_blocked_number_uniqueness(self, blocked_data: dict, blocked_id: int = None) -> Tuple[bool, str]:
        """
        ตรวจสอบความซ้ำของเลขอั้น
        
        Args:
            blocked_data: ข้อมูลเลขอั้น
            blocked_id: ID ของเลขอั้น (สำหรับการแก้ไข)
        
        Returns:
            Tuple ของ (is_valid, error_message)
        """
        
        existing = self.db.query(BlockedNumber).filter(
            and_(
                BlockedNumber.number_norm == blocked_data['number_norm'],
                BlockedNumber.field == blocked_data['field'],
                BlockedNumber.batch_id == blocked_data.get('batch_id')
            )
        ).first()
        
        if existing and (not blocked_id or existing.id != blocked_id):
            return False, f"เลขอั้น {blocked_data['number_norm']} ({blocked_data['field']}) มีอยู่แล้ว"
        
        return True, "Valid"
    
    def safe_create_order_items(self, order_id: int, items: list) -> Tuple[bool, list, list]:
        """
        สร้าง order items อย่างปลอดภัยพร้อมตรวจสอบความซ้ำ
        
        Args:
            order_id: ID ของ order
            items: รายการ items ที่ต้องการสร้าง
        
        Returns:
            Tuple ของ (success, created_items, errors)
        """
        
        created_items = []
        errors = []
        
        # ตรวจสอบความซ้ำก่อน
        is_valid, validation_errors = self.validate_order_uniqueness(order_id, items)
        if not is_valid:
            return False, [], validation_errors
        
        # สร้าง items ทีละรายการ
        for item_data in items:
            try:
                order_item = OrderItem(
                    order_id=order_id,
                    number=item_data['original_number'],
                    number_norm=item_data['number_norm'],
                    field=item_data['field'],
                    buy_amount=item_data['buy_amount'],
                    payout_factor=item_data['payout_factor'],
                    payout_amount=item_data['payout_amount'],
                    is_blocked=item_data.get('is_blocked', False)
                )
                
                self.db.add(order_item)
                self.db.flush()  # เพื่อให้ได้ ID
                
                created_items.append(order_item)
                
            except IntegrityError as e:
                self.db.rollback()
                if 'unique_order_field_number' in str(e):
                    errors.append(
                        f"เลข {item_data['number_norm']} ({item_data['field']}) ซ้ำกัน"
                    )
                else:
                    errors.append(f"ข้อผิดพลาดในการสร้างรายการ: {str(e)}")
                break
            
            except Exception as e:
                self.db.rollback()
                errors.append(f"ข้อผิดพลาด: {str(e)}")
                break
        
        if errors:
            return False, created_items, errors
        
        return True, created_items, []
```

### 2.3 Constraint Error Handling
```python
# utils/constraint_handler.py
from sqlalchemy.exc import IntegrityError
import re

class ConstraintErrorHandler:
    """จัดการข้อผิดพลาดจาก database constraints"""
    
    def __init__(self):
        self.constraint_messages = {
            'unique_order_field_number': 'เลขนี้มีอยู่ในคำสั่งซื้อแล้ว',
            'unique_rule_definition': 'กฎนี้มีอยู่แล้ว',
            'unique_blocked_number': 'เลขอั้นนี้มีอยู่แล้ว',
            'unique_download_token': 'Token นี้ถูกใช้แล้ว',
            'unique_order_number': 'หมายเลขคำสั่งซื้อนี้มีอยู่แล้ว',
            'UNIQUE constraint failed': 'ข้อมูลซ้ำกัน'
        }
    
    def handle_integrity_error(self, error: IntegrityError) -> str:
        """
        แปลง IntegrityError เป็นข้อความที่เข้าใจง่าย
        
        Args:
            error: IntegrityError จาก SQLAlchemy
        
        Returns:
            ข้อความแสดงข้อผิดพลาดที่เข้าใจง่าย
        """
        
        error_msg = str(error.orig).lower()
        
        # ตรวจสอบ constraint ต่างๆ
        for constraint, message in self.constraint_messages.items():
            if constraint.lower() in error_msg:
                return message
        
        # ตรวจสอบ UNIQUE constraint แบบทั่วไป
        if 'unique' in error_msg:
            # พยายามดึงชื่อคอลัมน์ที่ซ้ำ
            column_match = re.search(r'column (\w+)', error_msg)
            if column_match:
                column_name = column_match.group(1)
                return f"ข้อมูลในฟิลด์ {column_name} ซ้ำกัน"
            
            return "ข้อมูลซ้ำกัน"
        
        # ตรวจสอบ FOREIGN KEY constraint
        if 'foreign key' in error_msg:
            return "ข้อมูลอ้างอิงไม่ถูกต้อง"
        
        # ตรวจสอบ NOT NULL constraint
        if 'not null' in error_msg:
            column_match = re.search(r'column (\w+)', error_msg)
            if column_match:
                column_name = column_match.group(1)
                return f"ฟิลด์ {column_name} จำเป็นต้องมีข้อมูล"
            
            return "ข้อมูลที่จำเป็นหายไป"
        
        return "เกิดข้อผิดพลาดในการบันทึกข้อมูล"
    
    def safe_execute_with_constraint_handling(self, operation, *args, **kwargs):
        """
        Execute operation พร้อมจัดการ constraint errors
        
        Args:
            operation: function ที่ต้องการ execute
            *args, **kwargs: arguments สำหรับ operation
        
        Returns:
            Tuple ของ (success, result, error_message)
        """
        
        try:
            result = operation(*args, **kwargs)
            return True, result, None
        
        except IntegrityError as e:
            error_message = self.handle_integrity_error(e)
            return False, None, error_message
        
        except Exception as e:
            return False, None, f"เกิดข้อผิดพลาด: {str(e)}"

# ตัวอย่างการใช้งาน
def create_order_with_constraint_handling(order_data: dict):
    """สร้าง order พร้อมจัดการ constraint errors"""
    
    handler = ConstraintErrorHandler()
    
    def _create_order():
        # Normalize และ validate ข้อมูล
        normalizer = NumberNormalizer()
        validation_result = process_order_with_normalization(order_data)
        
        if not validation_result['success']:
            raise ValueError('; '.join(validation_result['errors']))
        
        # สร้าง order
        order = Order(
            order_number=generate_order_number(),
            user_id=order_data['user_id'],
            customer_name=order_data.get('customer_name'),
            total_amount=order_data['total_amount'],
            lottery_period=calculate_lottery_period(datetime.now().date()),
            batch_id=get_current_batch_id()
        )
        
        db.session.add(order)
        db.session.flush()
        
        # สร้าง order items
        validator = ValidationService(db.session)
        success, items, errors = validator.safe_create_order_items(
            order.id, 
            validation_result['normalized_items']
        )
        
        if not success:
            raise ValueError('; '.join(errors))
        
        db.session.commit()
        return order
    
    success, result, error = handler.safe_execute_with_constraint_handling(_create_order)
    
    if success:
        return {
            'success': True,
            'order': result,
            'message': 'สร้างคำสั่งซื้อสำเร็จ'
        }
    else:
        return {
            'success': False,
            'error': error,
            'message': 'ไม่สามารถสร้างคำสั่งซื้อได้'
        }
```

## 3. Data Integrity Checks

### 3.1 Comprehensive Data Validation
```python
# services/data_integrity.py
from datetime import datetime, timedelta
from decimal import Decimal
import logging

class DataIntegrityChecker:
    """ตรวจสอบความถูกต้องและความสมบูรณ์ของข้อมูล"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger('data_integrity')
    
    def check_order_integrity(self, order_id: int) -> dict:
        """
        ตรวจสอบความถูกต้องของ order
        
        Args:
            order_id: ID ของ order ที่ต้องการตรวจสอบ
        
        Returns:
            ผลการตรวจสอบ
        """
        
        issues = []
        warnings = []
        
        order = self.db.query(Order).get(order_id)
        if not order:
            return {'valid': False, 'issues': ['Order not found']}
        
        # ตรวจสอบ order items
        items = self.db.query(OrderItem).filter_by(order_id=order_id).all()
        
        if not items:
            issues.append("Order has no items")
        
        total_calculated = Decimal('0')
        
        for item in items:
            # ตรวจสอบ number normalization
            try:
                expected_norm = normalize_number(item.number, item.field)
                if item.number_norm != expected_norm:
                    issues.append(
                        f"Item {item.id}: number_norm mismatch. "
                        f"Expected: {expected_norm}, Got: {item.number_norm}"
                    )
            except Exception as e:
                issues.append(f"Item {item.id}: normalization error: {str(e)}")
            
            # ตรวจสอบ payout calculation
            expected_payout = item.buy_amount * item.payout_factor
            if abs(item.payout_amount - expected_payout) > Decimal('0.01'):
                issues.append(
                    f"Item {item.id}: payout calculation error. "
                    f"Expected: {expected_payout}, Got: {item.payout_amount}"
                )
            
            # ตรวจสอบ field values
            if item.field not in ['2_top', '2_bottom', '3_top', 'tote']:
                issues.append(f"Item {item.id}: invalid field: {item.field}")
            
            # ตรวจสอบ amounts
            if item.buy_amount <= 0:
                issues.append(f"Item {item.id}: invalid buy_amount: {item.buy_amount}")
            
            if item.payout_factor <= 0:
                issues.append(f"Item {item.id}: invalid payout_factor: {item.payout_factor}")
            
            total_calculated += item.buy_amount
        
        # ตรวจสอบ total amount
        if abs(order.total_amount - total_calculated) > Decimal('0.01'):
            issues.append(
                f"Order total mismatch. Expected: {total_calculated}, Got: {order.total_amount}"
            )
        
        # ตรวจสอบ lottery period
        if order.lottery_period:
            expected_period = calculate_lottery_period(order.created_at.date())
            if order.lottery_period != expected_period:
                warnings.append(
                    f"Lottery period mismatch. Expected: {expected_period}, Got: {order.lottery_period}"
                )
        
        # ตรวจสอบ batch_id
        if order.batch_id:
            expected_batch = get_current_batch_id_for_date(order.created_at.date())
            if order.batch_id != expected_batch:
                warnings.append(
                    f"Batch ID mismatch. Expected: {expected_batch}, Got: {order.batch_id}"
                )
        
        return {
            'valid': len(issues) == 0,
            'order_id': order_id,
            'issues': issues,
            'warnings': warnings,
            'items_count': len(items),
            'total_amount': float(order.total_amount)
        }
    
    def check_database_integrity(self) -> dict:
        """
        ตรวจสอบความถูกต้องของฐานข้อมูลทั้งหมด
        
        Returns:
            ผลการตรวจสอบโดยรวม
        """
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'orders': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'rules': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'blocked_numbers': {'total': 0, 'valid': 0, 'invalid': 0, 'issues': []},
            'summary': {'overall_valid': True, 'total_issues': 0}
        }
        
        # ตรวจสอบ orders
        orders = self.db.query(Order).all()
        results['orders']['total'] = len(orders)
        
        for order in orders:
            order_check = self.check_order_integrity(order.id)
            if order_check['valid']:
                results['orders']['valid'] += 1
            else:
                results['orders']['invalid'] += 1
                results['orders']['issues'].extend([
                    f"Order {order.id}: {issue}" for issue in order_check['issues']
                ])
        
        # ตรวจสอบ rules
        rules = self.db.query(Rule).all()
        results['rules']['total'] = len(rules)
        
        for rule in rules:
            rule_issues = self.check_rule_integrity(rule)
            if rule_issues:
                results['rules']['invalid'] += 1
                results['rules']['issues'].extend([
                    f"Rule {rule.id}: {issue}" for issue in rule_issues
                ])
            else:
                results['rules']['valid'] += 1
        
        # ตรวจสอบ blocked numbers
        blocked_numbers = self.db.query(BlockedNumber).all()
        results['blocked_numbers']['total'] = len(blocked_numbers)
        
        for blocked in blocked_numbers:
            blocked_issues = self.check_blocked_number_integrity(blocked)
            if blocked_issues:
                results['blocked_numbers']['invalid'] += 1
                results['blocked_numbers']['issues'].extend([
                    f"Blocked {blocked.id}: {issue}" for issue in blocked_issues
                ])
            else:
                results['blocked_numbers']['valid'] += 1
        
        # สรุปผล
        total_issues = (
            len(results['orders']['issues']) +
            len(results['rules']['issues']) +
            len(results['blocked_numbers']['issues'])
        )
        
        results['summary']['total_issues'] = total_issues
        results['summary']['overall_valid'] = total_issues == 0
        
        return results
    
    def check_rule_integrity(self, rule: Rule) -> list:
        """ตรวจสอบความถูกต้องของ rule"""
        
        issues = []
        
        # ตรวจสอบ rule_type
        if rule.rule_type not in ['payout', 'limit']:
            issues.append(f"Invalid rule_type: {rule.rule_type}")
        
        # ตรวจสอบ field
        if rule.field not in ['2_top', '2_bottom', '3_top', 'tote']:
            issues.append(f"Invalid field: {rule.field}")
        
        # ตรวจสอบ number_norm
        if rule.number_norm:
            try:
                expected_norm = normalize_number(rule.number_norm, rule.field)
                if rule.number_norm != expected_norm:
                    issues.append(f"number_norm not normalized: {rule.number_norm}")
            except Exception as e:
                issues.append(f"Invalid number_norm: {str(e)}")
        
        # ตรวจสอบ values ตาม rule_type
        if rule.rule_type == 'payout':
            if not rule.payout_factor or rule.payout_factor <= 0:
                issues.append(f"Invalid payout_factor: {rule.payout_factor}")
        elif rule.rule_type == 'limit':
            if not rule.limit_amount or rule.limit_amount <= 0:
                issues.append(f"Invalid limit_amount: {rule.limit_amount}")
        
        return issues
    
    def check_blocked_number_integrity(self, blocked: BlockedNumber) -> list:
        """ตรวจสอบความถูกต้องของ blocked number"""
        
        issues = []
        
        # ตรวจสอบ field
        valid_fields = ['all', '2_top', '2_bottom', '3_top', 'tote']
        if blocked.field not in valid_fields:
            issues.append(f"Invalid field: {blocked.field}")
        
        # ตรวจสอบ number_norm
        if blocked.field != 'all':
            try:
                expected_norm = normalize_number(blocked.number_norm, blocked.field)
                if blocked.number_norm != expected_norm:
                    issues.append(f"number_norm not normalized: {blocked.number_norm}")
            except Exception as e:
                issues.append(f"Invalid number_norm: {str(e)}")
        
        # ตรวจสอบ payout_factor
        if blocked.payout_factor < 0 or blocked.payout_factor > 1:
            issues.append(f"Invalid payout_factor: {blocked.payout_factor}")
        
        return issues
    
    def fix_data_integrity_issues(self, dry_run: bool = True) -> dict:
        """
        แก้ไขปัญหาความถูกต้องของข้อมูล
        
        Args:
            dry_run: ถ้า True จะไม่แก้ไขจริง แค่แสดงผลที่จะแก้ไข
        
        Returns:
            ผลการแก้ไข
        """
        
        fixes_applied = []
        fixes_failed = []
        
        # แก้ไข order items ที่ number_norm ไม่ถูกต้อง
        items_with_wrong_norm = self.db.query(OrderItem).all()
        
        for item in items_with_wrong_norm:
            try:
                expected_norm = normalize_number(item.number, item.field)
                if item.number_norm != expected_norm:
                    if not dry_run:
                        item.number_norm = expected_norm
                        self.db.add(item)
                    
                    fixes_applied.append(
                        f"OrderItem {item.id}: Fixed number_norm from {item.number_norm} to {expected_norm}"
                    )
            except Exception as e:
                fixes_failed.append(
                    f"OrderItem {item.id}: Failed to fix number_norm: {str(e)}"
                )
        
        # แก้ไข payout calculations ที่ผิด
        for item in items_with_wrong_norm:
            expected_payout = item.buy_amount * item.payout_factor
            if abs(item.payout_amount - expected_payout) > Decimal('0.01'):
                if not dry_run:
                    item.payout_amount = expected_payout
                    self.db.add(item)
                
                fixes_applied.append(
                    f"OrderItem {item.id}: Fixed payout_amount from {item.payout_amount} to {expected_payout}"
                )
        
        if not dry_run and fixes_applied:
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                fixes_failed.append(f"Failed to commit fixes: {str(e)}")
        
        return {
            'dry_run': dry_run,
            'fixes_applied': fixes_applied,
            'fixes_failed': fixes_failed,
            'total_fixes': len(fixes_applied),
            'total_failures': len(fixes_failed)
        }
```

### 3.2 Automated Data Consistency Checks
```python
# tasks/data_consistency.py
from celery import Celery
from datetime import datetime, timedelta

# สำหรับ scheduled tasks
app = Celery('data_consistency')

@app.task
def daily_data_integrity_check():
    """ตรวจสอบความถูกต้องของข้อมูลรายวัน"""
    
    checker = DataIntegrityChecker(db.session)
    results = checker.check_database_integrity()
    
    # บันทึกผลลัพธ์
    log_audit_event(
        action='daily_integrity_check',
        new_values=results
    )
    
    # ส่งแจ้งเตือนถ้าพบปัญหา
    if not results['summary']['overall_valid']:
        send_integrity_alert(results)
    
    return results

@app.task
def fix_data_inconsistencies():
    """แก้ไขปัญหาข้อมูลอัตโนมัติ"""
    
    checker = DataIntegrityChecker(db.session)
    
    # ทดลองแก้ไขก่อน (dry run)
    dry_run_results = checker.fix_data_integrity_issues(dry_run=True)
    
    # ถ้ามีการแก้ไขที่ปลอดภัย ให้ทำจริง
    if dry_run_results['total_fixes'] > 0 and dry_run_results['total_failures'] == 0:
        actual_results = checker.fix_data_integrity_issues(dry_run=False)
        
        log_audit_event(
            action='auto_fix_data_issues',
            new_values=actual_results
        )
        
        return actual_results
    
    return dry_run_results

def send_integrity_alert(results: dict):
    """ส่งแจ้งเตือนเมื่อพบปัญหาความถูกต้องของข้อมูล"""
    
    total_issues = results['summary']['total_issues']
    
    alert_message = f"""
    Data Integrity Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Total Issues Found: {total_issues}
    
    Orders: {results['orders']['invalid']}/{results['orders']['total']} invalid
    Rules: {results['rules']['invalid']}/{results['rules']['total']} invalid
    Blocked Numbers: {results['blocked_numbers']['invalid']}/{results['blocked_numbers']['total']} invalid
    
    Please check the system logs for detailed information.
    """
    
    # ส่งผ่าน email หรือ notification system
    # send_email('admin@lotoryjung.com', 'Data Integrity Alert', alert_message)
    
    print(alert_message)  # สำหรับ development
```

## สรุป
การ implement Data Correctness ตาม P0 requirements นี้จะช่วยให้ระบบมีความถูกต้องและความน่าเชื่อถือสูงขึ้น ผ่านการ normalize ข้อมูลอย่างเป็นระบบ การป้องกันข้อมูลซ้ำด้วย unique constraints และการตรวจสอบความสมบูรณ์ของข้อมูลอย่างต่อเนื่อง ระบบนี้พร้อมสำหรับการใช้งานจริงและสามารถรองรับการขยายตัวในอนาคตได้

