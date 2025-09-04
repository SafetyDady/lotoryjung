# 🎲 Tote Number Normalization System

## ปัญหาที่แก้ไข

ก่อนหน้านี้ระบบมีปัญหาสำคัญ:
- เลข 123, 231, 312 ถูกบันทึกแยกกัน 3 รายการ
- ทำให้รายงานผิดพลาด เพราะในความเป็นจริงควรรวมกันเป็นรายการเดียว
- อัตราการจ่ายใช้ค่า hardcode แทนที่จะดึงจากฐานข้อมูล

## 💡 วิธีการแก้ไข

### 1. Tote Number Normalization
สร้างฟังก์ชัน `generate_tote_number()` ที่แปลงเลขให้อยู่ในรูปแบบมาตรฐาน:

```python
def generate_tote_number(number_str):
    """
    แปลงเลขโต๊ดให้อยู่ในรูปแบบมาตรฐาน
    โดยเรียงหลักจากน้อยไปมาก
    """
    # ลบเครื่องหมายพิเศษ
    clean_number = number_str.replace(',', '').replace(' ', '')
    
    # เรียงหลักจากน้อยไปมาก
    sorted_digits = sorted(clean_number)
    
    return ''.join(sorted_digits)
```

### 2. ตัวอย่างการทำงาน
```python
# Input → Output
"123" → "123" ✅
"231" → "123" ✅  (รวมกับกลุ่มเดียวกัน)
"312" → "123" ✅  (รวมกับกลุ่มเดียวกัน)
"456" → "456" ✅
"645" → "456" ✅  (รวมกับ 456)
"546" → "456" ✅  (รวมกับ 456)
```

## 🗄️ การเปลี่ยนแปลงในฐานข้อมูล

### Schema เดิม
```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    field VARCHAR(50),
    number VARCHAR(10),      -- เลขที่ป้อน
    amount DECIMAL(10,2)
);
```

### Schema ใหม่
```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    field VARCHAR(50),
    number VARCHAR(10),      -- เลขที่ป้อน (เช่น "231")
    number_norm VARCHAR(10), -- เลขปกติ (เช่น "123") ← เพิ่มใหม่
    amount DECIMAL(10,2),
    UNIQUE(order_id, field, number_norm) ← ป้องกัน duplicate
);
```

## 🔄 การปรับปรุง API

### ก่อนแก้ไข
```python
# api.py - submit_bulk_order()
order_item = OrderItem(
    order_id=order_id,
    field=field,
    number=normalized_number,  # บันทึกเลขที่ป้อนตรง ๆ
    amount=amount
)
```

### หลังแก้ไข
```python
# api.py - submit_bulk_order()
# สำหรับ tote ใช้ normalization
if field == 'tote':
    normalized_number = generate_tote_number(str(number))
else:
    normalized_number = str(number)

order_item = OrderItem(
    order_id=order_id,
    field=field,
    number=str(number),        # เลขที่ป้อนจริง
    number_norm=normalized_number,  # เลขที่ normalize แล้ว
    amount=amount
)
```

## 📊 การปรับปรุง Sales Report

### ก่อนแก้ไข (ผิด)
```python
def get_all_sales_report():
    # Query โดยใช้ number ตรง ๆ
    results = db.session.query(
        OrderItem.number,
        func.sum(OrderItem.amount)
    ).filter(OrderItem.field == 'tote').group_by(OrderItem.number).all()
    
    # ผลลัพธ์:
    # [('123', 100), ('231', 200), ('312', 150)]  ← แยกกัน 3 รายการ
```

### หลังแก้ไข (ถูก)
```python
def get_all_sales_report():
    # Query โดยใช้ number_norm เพื่อรวมกลุ่ม
    results = db.session.query(
        OrderItem.number_norm,
        func.sum(OrderItem.amount)
    ).filter(OrderItem.field == 'tote').group_by(OrderItem.number_norm).all()
    
    # ผลลัพธ์:
    # [('123', 450)]  ← รวมกันเป็นรายการเดียว (100+200+150)
```

## 🧪 การทดสอบระบบ

### Test Case 1: Basic Normalization
```python
# Input
orders = [
    {"field": "tote", "number": "123", "amount": 100},
    {"field": "tote", "number": "231", "amount": 200},
    {"field": "tote", "number": "312", "amount": 150}
]

# Expected Database Storage
# number | number_norm | amount
# "123"  | "123"      | 100
# "231"  | "123"      | 200
# "312"  | "123"      | 150

# Expected Report Output
{
    "tote": [
        {
            "number": "123",
            "total_sales": 450.0,    # 100 + 200 + 150
            "expected_loss": 45.0    # 450 * 0.1 (อัตราจ่าย 100)
        }
    ]
}
```

### Test Case 2: Mixed Fields
```python
# Input (เลขเดียวกันแต่ field ต่างกัน)
orders = [
    {"field": "tote", "number": "123", "amount": 100},   # จะ normalize
    {"field": "3_top", "number": "123", "amount": 200}   # ไม่ normalize
]

# Expected Report
{
    "tote": [{"number": "123", "total_sales": 100.0}],
    "3_top": [{"number": "123", "total_sales": 200.0}]
}
# ← แยกกันเพราะ field ต่างกัน
```

## ⚡ การทำงานใน Production

### 1. API Validation
```python
POST /api/validate-bulk-order
{
    "items": [
        {"field": "tote", "number": "231", "amount": 100},
        {"field": "tote", "number": "123", "amount": 100}  // จะ error เพราะ duplicate
    ]
}
```

### 2. Database Constraint Protection
```sql
-- UNIQUE constraint จะป้องกันไม่ให้บันทึกซ้ำ
UNIQUE(order_id, field, number_norm)

-- ตัวอย่าง:
-- order_id=1, field="tote", number_norm="123" ← OK
-- order_id=1, field="tote", number_norm="123" ← ERROR: UNIQUE constraint failed
```

## 📈 ผลลัพธ์ที่ได้

### Before Fix (ผิด)
```
Tote Report:
- เลข 123: 100 บาท
- เลข 231: 200 บาท  
- เลข 312: 150 บาท
Total: 3 รายการ, 450 บาท
```

### After Fix (ถูก)
```
Tote Report:  
- เลข 123: 450 บาท (รวม 123+231+312)
Total: 1 รายการ, 450 บาท
```

## 🔧 การ Debug

### ทดสอบ Normalization Function
```python
from app.utils.number_utils import generate_tote_number

# ทดสอบ
test_numbers = ['123', '231', '312', '456', '645', '546']
for num in test_numbers:
    normalized = generate_tote_number(num)
    print(f'{num} → {normalized}')

# Expected Output:
# 123 → 123
# 231 → 123
# 312 → 123
# 456 → 456
# 645 → 456
# 546 → 456
```

### ตรวจสอบ Database
```sql
-- ดูข้อมูลใน database
SELECT number, number_norm, amount 
FROM order_items 
WHERE field = 'tote' 
ORDER BY number_norm;

-- Expected:
-- number | number_norm | amount
-- "123"  | "123"      | 100
-- "231"  | "123"      | 200
-- "312"  | "123"      | 150
```

---
**✅ สถานะ**: แก้ไขเสร็จแล้วและทดสอบผ่าน  
**🎯 ผลลัพธ์**: โต๊ดรวมกลุ่มถูกต้อง (123, 231, 312 → กลุ่ม 123)  
**👤 การยืนยัน**: "มันใช้ได้ ยอดเยี่ยมมาก"
