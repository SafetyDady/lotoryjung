# 📊 Simple Sales Reporting System

## ภาพรวมระบบ

ระบบรายงานยอดขายที่ได้รับการปรับปรุงใหม่ล่าสุด เพื่อแก้ไขปัญหาสำคัญ:
- **อัตราการจ่าย**: ดึงจากฐานข้อมูลแทนที่จะ hardcode
- **การจัดกลุ่มโต๊ด**: รวมเลขที่มีหลักเดียวกัน (123, 231, 312)
- **ความแม่นยำ**: คำนวณยอดขายและผลกำไรที่ถูกต้อง

## 🎯 คุณสมบัติหลัก

### 1. รายงานยอดขายแยกตามประเภท
- **2 ตัวบน (2_top)**: อัตราจ่าย 70
- **2 ตัวล่าง (2_bottom)**: อัตราจ่าย 70  
- **3 ตัวบน (3_top)**: อัตราจ่าย 500
- **โต๊ด (tote)**: อัตราจ่าย 100

### 2. การจัดกลุ่มโต๊ดอัตโนมัติ
```python
# ตัวอย่างการทำงาน
123 → 123 (กลุ่มมาตรฐาน)
231 → 123 (รวมกับกลุ่มเดียวกัน)
312 → 123 (รวมกับกลุ่มเดียวกัน)
```

### 3. การคำนวณผลกำไร/ขาดทุน
- ยอดขายรวม - (ยอดขาย × อัตราการจ่าย)
- แสดงเลขที่อาจทำให้เสียเงินมากที่สุด

## 🛠 การใช้งาน

### Web Interface
```
http://localhost:5000/admin/simple-sales-report
```

### API Endpoints
```python
# ดูรายงานยอดขาย
GET /api/simple-sales-report

# ตัวอย่าง Response
{
  "success": true,
  "data": {
    "field_summary": {
      "tote": {
        "count": 2,
        "total_sales": 1000.0,
        "expected_loss": 100.0
      }
    },
    "field_groups": {
      "tote": [
        {
          "number": "123",
          "total_sales": 500.0,
          "expected_loss": 50.0
        }
      ]
    }
  }
}
```

## 🔧 การติดตั้งและใช้งาน

### 1. Import Service
```python
from app.services.simple_sales_service import SimpleSalesService
```

### 2. เรียกใช้งาน
```python
# ดูรายงานทั้งหมด
result = SimpleSalesService.get_all_sales_report()

# ดูรายงานแค่ประเภทเดียว
result = SimpleSalesService.get_sales_report_by_field('tote')
```

## 📋 โครงสร้างข้อมูล

### Database Schema
```sql
-- OrderItem table จะใช้ number_norm สำหรับจัดกลุ่ม
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    field VARCHAR(50),
    number VARCHAR(10),      -- เลขที่ป้อน (เช่น "231")
    number_norm VARCHAR(10), -- เลขปกติ (เช่น "123")
    amount DECIMAL(10,2),
    UNIQUE(order_id, field, number_norm)
);
```

### Tote Normalization
```python
def generate_tote_number(number_str):
    """แปลงเลขโต๊ดให้อยู่ในรูปแบบมาตรฐาน"""
    digits = sorted(number_str.replace(',', '').replace(' ', ''))
    return ''.join(digits)
    
# ตัวอย่าง:
# "231" → "123"
# "312" → "123" 
# "456" → "456"
```

## 🧪 การทดสอบ

### ตัวอย่างข้อมูลทดสอบ
```python
# สร้างออเดอร์ทดสوบ
orders = [
    {"field": "tote", "number": "123", "amount": 100},
    {"field": "tote", "number": "231", "amount": 200},  # จะรวมกับ 123
    {"field": "tote", "number": "312", "amount": 150},  # จะรวมกับ 123
    {"field": "3_top", "number": "123", "amount": 100}, # แยกจาก tote
]
```

### ผลลัพธ์ที่คาดหวัง
```json
{
  "tote": [
    {
      "number": "123",
      "total_sales": 450.0,  // 100+200+150
      "expected_loss": 45.0  // 450 * 0.1
    }
  ],
  "3_top": [
    {
      "number": "123",
      "total_sales": 100.0,
      "expected_loss": 500.0  // 100 * 5.0
    }
  ]
}
```

## ⚠️ ข้อควรระวัง

1. **Tote vs 3_top**: เลขเดียวกันแต่ประเภทต่างกันจะแยกกัน
2. **อัตราการจ่าย**: ดึงจากฐานข้อมูล ห้าม hardcode
3. **UNIQUE Constraint**: ใช้ number_norm เพื่อป้องกัน duplicate

## 📞 การแก้ไขปัญหา

### ปัญหาทั่วไป
1. **อัตราการจ่ายผิด**: ตรวจสอบข้อมูลในตาราง Rule
2. **โต๊ดไม่รวมกัน**: ตรวจสอบ generate_tote_number()
3. **Constraint Error**: ตรวจสอบ number_norm field

### การ Debug
```python
# ตรวจสอบการทำงานของ normalization
from app.utils.number_utils import generate_tote_number
print(generate_tote_number("231"))  # ควรได้ "123"
```

---
**สถานะ**: ✅ ทดสอบแล้วและพร้อมใช้งาน  
**วันที่อัพเดต**: 4 กันยายน 2568  
**ผู้พัฒนา**: Lotoryjung Development Team
