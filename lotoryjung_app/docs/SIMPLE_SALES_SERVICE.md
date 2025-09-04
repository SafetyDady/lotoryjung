# 📊 SimpleSalesService API Documentation

## ภาพรวม
`SimpleSalesService` เป็นหัวใจสำคัญของระบบรายงานยอดขาย ที่ได้รับการแก้ไขเพื่อให้มีความแม่นยำในการคำนวณอัตราการจ่ายและการจัดกลุ่มโต๊ด

## 🎯 ปัญหาที่แก้ไข

### 1. อัตราการจ่าย (Payout Rates)
```python
# ❌ เดิม (hardcode)
def _get_payout_rate(self, field):
    rates = {
        '2_top': 70,
        '2_bottom': 70,  
        '3_top': 500,
        'tote': 100
    }
    return rates.get(field, 1)

# ✅ ใหม่ (จากฐานข้อมูล)
def _get_payout_rate(self, field):
    return LimitService.get_base_payout_rate(field)
```

### 2. การจัดกลุ่มโต๊ด (Tote Grouping)
```python
# ❌ เดิม (แยกกัน)
results = db.session.query(
    OrderItem.number,           # ใช้เลขที่ป้อน
    func.sum(OrderItem.amount)
).filter(OrderItem.field == field).group_by(OrderItem.number)

# ✅ ใหม่ (รวมกลุ่ม)
if field == 'tote':
    results = db.session.query(
        OrderItem.number_norm,      # ใช้เลขที่ normalize แล้ว
        func.sum(OrderItem.amount)
    ).filter(OrderItem.field == field).group_by(OrderItem.number_norm)
```

## 🔧 API Methods

### `get_all_sales_report()`
ดึงรายงานยอดขายทั้งหมดแยกตามประเภท

#### Response Format
```json
{
    "success": true,
    "data": {
        "field_summary": {
            "2_top": {
                "count": 2,
                "total_sales": 900.0,
                "expected_loss": 630.0
            },
            "tote": {
                "count": 2,
                "total_sales": 1000.0,
                "expected_loss": 100.0
            }
        },
        "field_groups": {
            "2_top": [
                {
                    "number": "12",
                    "total_sales": 500.0,
                    "expected_loss": 350.0
                }
            ],
            "tote": [
                {
                    "number": "123",
                    "total_sales": 1000.0,
                    "expected_loss": 100.0
                }
            ]
        },
        "highest_loss": {
            "field": "3_top",
            "number": "123",
            "amount": 500.0
        }
    }
}
```

### `get_sales_report_by_field(field)`
ดึงรายงานของประเภทเดียว

#### Parameters
- `field` (str): ประเภทหวย ('2_top', '2_bottom', '3_top', 'tote')

#### Example
```python
result = SimpleSalesService.get_sales_report_by_field('tote')
```

#### Response
```json
{
    "success": true,
    "data": [
        {
            "number": "123",
            "total_sales": 1000.0,
            "expected_loss": 100.0
        }
    ]
}
```

## 🧮 การคำนวณ Expected Loss

### สูตรการคำนวณ
```python
expected_loss = total_sales * (payout_rate / 100)
```

### ตัวอย่าง
```python
# โต๊ด: ยอดขาย 1000 บาท, อัตราจ่าย 100
expected_loss = 1000 * (100 / 100) = 1000 บาท

# 3 ตัวบน: ยอดขาย 100 บาท, อัตราจ่าย 500  
expected_loss = 100 * (500 / 100) = 500 บาท
```

## 🎲 การจัดการโต๊ด (Tote Handling)

### Normalization Logic
```python
from app.utils.number_utils import generate_tote_number

def get_sales_report_by_field(self, field):
    if field == 'tote':
        # ใช้ number_norm สำหรับจัดกลุ่ม
        results = db.session.query(
            OrderItem.number_norm.label('number'),
            func.sum(OrderItem.amount).label('total_sales')
        ).filter(
            OrderItem.field == field
        ).group_by(OrderItem.number_norm).all()
    else:
        # ใช้ number ปกติสำหรับประเภทอื่น
        results = db.session.query(
            OrderItem.number,
            func.sum(OrderItem.amount).label('total_sales')
        ).filter(
            OrderItem.field == field
        ).group_by(OrderItem.number).all()
```

### การทำงานของ Tote Grouping
```python
# ข้อมูลในฐานข้อมูล
# number | number_norm | amount
# "123"  | "123"      | 100
# "231"  | "123"      | 200  ← รวมกับ 123
# "312"  | "123"      | 150  ← รวมกับ 123

# ผลลัพธ์ในรายงาน
[
    {
        "number": "123",
        "total_sales": 450.0,  # 100 + 200 + 150
        "expected_loss": 45.0  # 450 * 0.1
    }
]
```

## 📈 การใช้งานใน Admin Interface

### Template Integration
```html
<!-- templates/admin/simple_sales_report.html -->
<div id="sales-report">
    <!-- แสดงข้อมูลจาก SimpleSalesService -->
</div>

<script>
async function loadSalesReport() {
    const response = await fetch('/api/simple-sales-report');
    const data = await response.json();
    
    if (data.success) {
        renderReport(data.data);
    }
}
</script>
```

### Route Handler
```python
# app/routes/admin.py
@admin.route('/simple-sales-report')
def simple_sales_report():
    return render_template('admin/simple_sales_report.html')

# API endpoint
@api.route('/simple-sales-report')
def api_simple_sales_report():
    result = SimpleSalesService.get_all_sales_report()
    return jsonify(result)
```

## 🧪 Testing Examples

### Test Setup
```python
from app.services.simple_sales_service import SimpleSalesService
from app import create_app, db

app = create_app()
with app.app_context():
    result = SimpleSalesService.get_all_sales_report()
```

### Sample Test Data
```python
# สร้างข้อมูลทดสอบ
orders = [
    {"field": "tote", "number": "123", "amount": 100},
    {"field": "tote", "number": "231", "amount": 200},  # จะรวมกับ 123
    {"field": "3_top", "number": "456", "amount": 300},
    {"field": "2_top", "number": "12", "amount": 150}
]
```

### Expected Results
```json
{
    "field_summary": {
        "tote": {
            "count": 1,           # รวมกลุ่มแล้ว 123,231 → 123
            "total_sales": 300.0,
            "expected_loss": 30.0
        },
        "3_top": {
            "count": 1,
            "total_sales": 300.0,
            "expected_loss": 1500.0  # 300 * 5.0
        }
    }
}
```

## 🚨 Error Handling

### Common Errors
```python
# Database connection error
{
    "success": false,
    "error": "Database connection failed"
}

# No data found
{
    "success": true,
    "data": {
        "field_summary": {},
        "field_groups": {},
        "highest_loss": None
    }
}

# Invalid field type
{
    "success": false,
    "error": "Invalid field type: xyz"
}
```

### Debug Information
```python
# เปิดใช้งาน debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

result = SimpleSalesService.get_all_sales_report()
# จะแสดง SQL queries และ processing steps
```

## 📊 Performance Considerations

### Database Optimization
```python
# ใช้ index สำหรับการ query
# CREATE INDEX idx_order_items_field ON order_items(field);
# CREATE INDEX idx_order_items_norm ON order_items(field, number_norm);
```

### Caching (Future Enhancement)
```python
# เพิ่ม caching ในอนาคต
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_sales_report(field):
    return SimpleSalesService.get_sales_report_by_field(field)
```

## 🎯 Integration Examples

### Flask Route
```python
@app.route('/dashboard')
def dashboard():
    sales_data = SimpleSalesService.get_all_sales_report()
    return render_template('dashboard.html', sales=sales_data)
```

### JavaScript Frontend
```javascript
// ดึงข้อมูลแบบ async
async function getSalesData() {
    try {
        const response = await fetch('/api/simple-sales-report');
        const data = await response.json();
        
        if (data.success) {
            updateDashboard(data.data);
        }
    } catch (error) {
        console.error('Sales report error:', error);
    }
}
```

---
**✅ Status**: Production Ready  
**🔧 Version**: 2.1.0  
**📅 Last Updated**: September 4, 2025  
**👨‍💻 Author**: Lotoryjung Development Team
