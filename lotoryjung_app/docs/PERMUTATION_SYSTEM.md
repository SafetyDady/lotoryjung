# Permutation System Documentation
## ระบบการสร้างเลขเรียงสำหรับเลขอั้น (Blocked Numbers)

### 📋 Overview
ระบบ Permutation ใน Lotoryjung App ทำหน้าที่สร้างการเรียงสับเปลี่ยนของเลขที่ป้อนเข้ามา เพื่อให้ระบบสามารถบล็อกเลขทุกรูปแบบที่เป็นไปได้ของเลขนั้น

### 🎯 วัตถุประสงค์
1. **ป้องกันการชนรางวัล** - บล็อกเลขทุกรูปแบบที่อาจออกรางวัล
2. **ความครอบคลุม** - ไม่ให้มีช่องทางหลบเลี่ยงการบล็อก
3. **ประสิทธิภาพ** - สร้าง permutations อัตโนมัติไม่ต้องกรอกทีละตัว

---

## 🔢 หลักการทำงาน

### เลข 2 หลัก (2-digit Numbers)
เมื่อกรอกเลข 2 หลัก เช่น `12` ระบบจะสร้าง:

#### Permutations ที่สร้าง:
- `12` (เลขต้นฉบับ)
- `21` (สลับตำแหน่ง)

#### การกระจายไปยัง Fields:
```
INPUT: 12 (2_digit)
OUTPUT:
├── 2_top: [12, 21]     # 2 ตัวบน
└── 2_bottom: [12, 21]  # 2 ตัวล่าง
```

**ตัวอย่าง:**
```javascript
generatePermutations("12", "2_digit")
// ผลลัพธ์:
[
  {field: "2_top", number_norm: "12"},
  {field: "2_top", number_norm: "21"},
  {field: "2_bottom", number_norm: "12"},
  {field: "2_bottom", number_norm: "21"}
]
```

---

### เลข 3 หลัก (3-digit Numbers)
เมื่อกรอกเลข 3 หลัก เช่น `123` ระบบจะสร้าง:

#### Permutations ที่สร้าง:
- `123` (เลขต้นฉบับ)
- `132` (สลับตำแหน่งที่ 2,3)
- `213` (สลับตำแหน่งที่ 1,2)
- `231` (หมุนขวา)
- `312` (หมุนซ้าย)
- `321` (กลับหัวท้าย)

#### การกระจายไปยัง Fields:
```
INPUT: 123 (3_digit)
OUTPUT:
├── 3_top: [123, 132, 213, 231, 312, 321]  # 3 ตัวบน (6 permutations)
└── tote: [123]                            # โต๊ด (เลขต้นฉบับเท่านั้น)
```

**ตัวอย่าง:**
```javascript
generatePermutations("123", "3_digit")
// ผลลัพธ์:
[
  {field: "3_top", number_norm: "123"},
  {field: "3_top", number_norm: "132"},
  {field: "3_top", number_norm: "213"},
  {field: "3_top", number_norm: "231"},
  {field: "3_top", number_norm: "312"},
  {field: "3_top", number_norm: "321"},
  {field: "tote", number_norm: "123"}
]
```

---

## 🛠️ Implementation Details

### Core Function: `generate_blocked_numbers_for_field()`
**Location:** `/app/utils/number_utils.py`

```python
def generate_blocked_numbers_for_field(number, number_type):
    """
    สร้าง blocked numbers สำหรับเลขที่กำหนด
    
    Args:
        number (str): เลขที่ต้องการสร้าง permutations
        number_type (str): ประเภทเลข ("2_digit" หรือ "3_digit")
        
    Returns:
        List[Dict]: รายการ records ที่จะบันทึกลง database
    """
```

### Algorithm Flow:
1. **Input Validation** - ตรวจสอบความถูกต้องของข้อมูลนำเข้า
2. **Generate Permutations** - สร้างการเรียงสับเปลี่ยน
3. **Field Assignment** - กำหนด field ตามประเภทเลข
4. **Format Output** - จัดรูปแบบข้อมูลสำหรับ database

---

## 📊 การใช้งานใน Bulk Add System

### Workflow:
1. **User Input** - ผู้ใช้กรอกเลขในฟอร์ม Bulk Add
2. **Validation** - ตรวจสอบรูปแบบและประเภทเลข
3. **Clear Database** - ลบเลขอั้นเก่าทั้งหมด
4. **Generate Permutations** - สร้าง permutations สำหรับทุกเลข
5. **Remove Duplicates** - กรองเลขซ้ำใน memory
6. **Batch Insert** - บันทึกลง database ครั้งเดียว

### Bulk Add Example:
```javascript
Input: [
  {number: "12", type: "2_digit"},
  {number: "13", type: "2_digit"}, 
  {number: "123", type: "3_digit"}
]

Generated Records:
├── 2_top: [12, 21, 13, 31]           # 4 records
├── 2_bottom: [12, 21, 13, 31]        # 4 records  
├── 3_top: [123, 132, 213, 231, 312, 321]  # 6 records
└── tote: [123]                       # 1 record
Total: 15 records
```

---

## 🔍 Technical Specifications

### Database Schema:
```sql
CREATE TABLE blocked_numbers (
    id INTEGER PRIMARY KEY,
    field VARCHAR(20) NOT NULL,        -- '2_top', '2_bottom', '3_top', 'tote'
    number_norm VARCHAR(3) NOT NULL,   -- normalized number string
    reason TEXT,                       -- optional reason
    is_active BOOLEAN DEFAULT 1,      -- active status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field, number_norm)         -- prevent duplicates
);
```

### Field Mappings:
| Field | Description | Permutation Rules |
|-------|-------------|-------------------|
| `2_top` | 2 ตัวบน | All 2! permutations |
| `2_bottom` | 2 ตัวล่าง | All 2! permutations |  
| `3_top` | 3 ตัวบน | All 3! permutations |
| `tote` | โต๊ด | Original number only |

---

## 🧪 Testing Examples

### Test Case 1: Single 2-digit
```python
result = generate_blocked_numbers_for_field("45", "2_digit")
expected = [
    {"field": "2_top", "number_norm": "45"},
    {"field": "2_top", "number_norm": "54"},
    {"field": "2_bottom", "number_norm": "45"},
    {"field": "2_bottom", "number_norm": "54"}
]
assert result == expected
```

### Test Case 2: Single 3-digit
```python
result = generate_blocked_numbers_for_field("987", "3_digit")
expected_count = 7  # 6 for 3_top + 1 for tote
assert len(result) == expected_count
assert len([r for r in result if r["field"] == "3_top"]) == 6
assert len([r for r in result if r["field"] == "tote"]) == 1
```

---

## 🚨 Edge Cases & Considerations

### 1. Duplicate Digits
- เลข `11` → permutations: `[11]` (เหมือนเดิม)
- เลข `112` → permutations: `[112, 121, 211]` (ไม่ซ้ำ)

### 2. Leading Zeros
- เลขที่ขึ้นต้นด้วย 0 จะถูก normalize
- `012` → `12` (treated as 2-digit)

### 3. Performance Optimization
- ใช้ `itertools.permutations()` สำหรับความเร็ว
- Batch insert แทน individual inserts
- Memory-based duplicate filtering

---

## 🔧 Maintenance & Monitoring

### Logging:
- Debug logs แสดงจำนวน permutations ที่สร้าง
- Error handling สำหรับ invalid inputs
- Transaction rollback เมื่อเกิด error

### Performance Metrics:
- เลข 2 หลัก: ~0.1ms per number
- เลข 3 หลัก: ~0.5ms per number
- Bulk add 100 numbers: ~2-5 seconds

---

## 📚 Related Documentation
- [API Documentation](API_DOCUMENTATION.md)
- [Database Design](DESIGN.md) 
- [Installation Guide](INSTALLATION.md)
- [System Structure](STRUCTURE.md)

---

## 🎯 Summary
Permutation System เป็นหัวใจสำคัญของระบบเลขอั้น ที่ช่วยให้ระบบสามารถป้องกันการชนรางวัลได้อย่างครอบคลุม โดยการสร้างการเรียงสับเปลี่ยนทุกรูปแบบของเลขที่กำหนด และกระจายไปยัง field ที่เหมาะสมตามกฎหวย

**Key Benefits:**
- ✅ ครอบคลุมทุกรูปแบบเลขที่เป็นไปได้
- ✅ ประสิทธิภาพสูงด้วย batch processing  
- ✅ ป้องกัน duplicate ด้วย unique constraints
- ✅ ใช้งานง่ายผ่าน bulk add interface
