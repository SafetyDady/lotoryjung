# Rule Matrix - ระบบกติกาและกฎเกณฑ์

## ภาพรวม
เอกสารนี้กำหนดกติกาและกฎเกณฑ์ทั้งหมดสำหรับระบบ Lotoryjung รวมถึงการจ่ายเงิน (Payout) และการจำกัด (Limit) สำหรับแต่ละประเภทการเดิมพัน

## กติกาหลัก (Core Rules)

### 1. เลขอั้น (Blocked Numbers)
เลขอั้นคือเลขที่ไม่สามารถซื้อได้ หรือมีการจ่ายเงินลดลง

**กฎการจ่ายเงินสำหรับเลขอั้น:**
- **ปกติ**: จ่ายตามอัตราปกติ
- **เลขอั้น**: จ่าย 0.5 เท่าของอัตราปกติ
- **ขอบเขต**: ใช้กับทุก Field (2 บน, 2 ล่าง, 3 บน, โต๊ด)

### 2. ลิมิต (Limits)
ลิมิตคือจำนวนเงินสูงสุดที่สามารถซื้อได้สำหรับแต่ละเลข

**กฎการคำนวณลิมิต:**
- **หลักการ**: คิดจาก "เลข + ประเภท" โดยไม่สนใจเวลา
- **ขอบเขต**: แยกตามประเภท (2 บน, 2 ล่าง, 3 บน, โต๊ด)
- **การสะสม**: รวมยอดของ User ทั้งหมดสำหรับเลขและประเภทเดียวกัน

### 3. การปรับมาตรฐานเลข (Number Normalization)

**เลข 2 หลัก:**
- รูปแบบ: 00-99
- ตัวอย่าง: "5" → "05", "25" → "25"

**เลข 3 หลัก:**
- รูปแบบ: 000-999
- ตัวอย่าง: "7" → "007", "123" → "123"

**โต๊ด (Tote):**
- การปรับมาตรฐาน: เรียงลำดับจากน้อยไปมาก
- ตัวอย่าง: "367" → "367", "736" → "367", "673" → "367"

## Rule Matrix Table

### ตาราง Payout Rules

| Field | Rule Type | Number | Payout Factor | Condition | Scope |
|-------|-----------|---------|---------------|-----------|-------|
| 2_top | payout | * | 90.0 | normal | per-number |
| 2_top | payout | blocked | 45.0 | blocked | per-number |
| 2_bottom | payout | * | 90.0 | normal | per-number |
| 2_bottom | payout | blocked | 45.0 | blocked | per-number |
| 3_top | payout | * | 900.0 | normal | per-number |
| 3_top | payout | blocked | 450.0 | blocked | per-number |
| tote | payout | * | 150.0 | normal | per-number |
| tote | payout | blocked | 75.0 | blocked | per-number |

### ตาราง Limit Rules

| Field | Rule Type | Number | Limit Amount | Scope | Description |
|-------|-----------|---------|--------------|-------|-------------|
| 2_top | limit | * | 10000 | per-number | ลิมิตต่อเลข 2 ตัวบน |
| 2_bottom | limit | * | 10000 | per-number | ลิมิตต่อเลข 2 ตัวล่าง |
| 3_top | limit | * | 5000 | per-number | ลิมิตต่อเลข 3 ตัวบน |
| tote | limit | * | 8000 | per-number | ลิมิตต่อเลขโต๊ด |

### ตาราง Blocked Numbers (ตัวอย่าง)

| Number | Field | Status | Effective Date | Notes |
|--------|-------|--------|----------------|--------|
| 00 | all | blocked | 2024-01-01 | เลขอั้นทั่วไป |
| 11 | all | blocked | 2024-01-01 | เลขอั้นทั่วไป |
| 123 | 3_top | blocked | 2024-09-01 | เลขอั้นเฉพาะ 3 ตัวบน |
| 456 | tote | blocked | 2024-09-01 | เลขอั้นเฉพาะโต๊ด |

## Database Schema สำหรับ Rules

### ตาราง rules
```sql
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type VARCHAR(20) NOT NULL, -- 'payout' หรือ 'limit'
    field VARCHAR(20) NOT NULL,     -- '2_top', '2_bottom', '3_top', 'tote'
    number_norm VARCHAR(10),        -- เลขที่ปรับมาตรฐานแล้ว, NULL = ทั้งหมด
    payout_factor DECIMAL(10,2),    -- อัตราจ่าย (สำหรับ payout rules)
    limit_amount INTEGER,           -- จำนวนลิมิต (สำหรับ limit rules)
    scope VARCHAR(20) NOT NULL,     -- 'per-number', 'per-user', 'global'
    condition_type VARCHAR(20),     -- 'normal', 'blocked'
    is_active BOOLEAN DEFAULT TRUE,
    batch_id VARCHAR(50),           -- สำหรับแยกงวด (อนาคต)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(rule_type, field, number_norm, condition_type, batch_id)
);

-- Indexes
CREATE INDEX idx_rules_active ON rules(is_active, rule_type, field);
CREATE INDEX idx_rules_number ON rules(field, number_norm, is_active);
CREATE INDEX idx_rules_batch ON rules(batch_id, is_active);
```

### ตาราง blocked_numbers
```sql
CREATE TABLE blocked_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number_norm VARCHAR(10) NOT NULL,  -- เลขที่ปรับมาตรฐานแล้ว
    field VARCHAR(20) NOT NULL,        -- 'all', '2_top', '2_bottom', '3_top', 'tote'
    status VARCHAR(20) DEFAULT 'blocked', -- 'blocked', 'active'
    payout_factor DECIMAL(10,2) DEFAULT 0.5, -- อัตราจ่ายสำหรับเลขอั้น
    effective_date DATE,
    notes TEXT,
    batch_id VARCHAR(50),              -- สำหรับแยกงวด (อนาคต)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(number_norm, field, batch_id)
);

-- Indexes
CREATE INDEX idx_blocked_numbers_lookup ON blocked_numbers(number_norm, field, status);
CREATE INDEX idx_blocked_numbers_batch ON blocked_numbers(batch_id, status);
```

## การใช้งาน Rules ในระบบ

### 1. การตรวจสอบเลขอั้น
```python
def is_number_blocked(number_norm, field, batch_id=None):
    """ตรวจสอบว่าเลขนั้นเป็นเลขอั้นหรือไม่"""
    
    # ตรวจสอบเลขอั้นเฉพาะ field
    blocked = db.session.query(BlockedNumber).filter(
        BlockedNumber.number_norm == number_norm,
        BlockedNumber.field.in_([field, 'all']),
        BlockedNumber.status == 'blocked',
        BlockedNumber.batch_id == batch_id
    ).first()
    
    return blocked is not None

def get_payout_factor(number_norm, field, batch_id=None):
    """ดึงอัตราจ่ายสำหรับเลขและ field"""
    
    # ตรวจสอบเลขอั้นก่อน
    if is_number_blocked(number_norm, field, batch_id):
        blocked = db.session.query(BlockedNumber).filter(
            BlockedNumber.number_norm == number_norm,
            BlockedNumber.field.in_([field, 'all']),
            BlockedNumber.status == 'blocked',
            BlockedNumber.batch_id == batch_id
        ).first()
        return blocked.payout_factor if blocked else 0.5
    
    # ดึงอัตราจ่ายปกติ
    rule = db.session.query(Rule).filter(
        Rule.rule_type == 'payout',
        Rule.field == field,
        Rule.number_norm.is_(None),  # กฎทั่วไป
        Rule.condition_type == 'normal',
        Rule.is_active == True,
        Rule.batch_id == batch_id
    ).first()
    
    return rule.payout_factor if rule else get_default_payout_factor(field)
```

### 2. การตรวจสอบลิมิต
```python
def check_limit(number_norm, field, amount, batch_id=None):
    """ตรวจสอบว่าจำนวนเงินเกินลิมิตหรือไม่"""
    
    # ดึงลิมิตสำหรับเลขและ field นี้
    rule = db.session.query(Rule).filter(
        Rule.rule_type == 'limit',
        Rule.field == field,
        Rule.number_norm.in_([number_norm, None]),  # เฉพาะเลข หรือ ทั่วไป
        Rule.is_active == True,
        Rule.batch_id == batch_id
    ).order_by(Rule.number_norm.desc()).first()  # เฉพาะเลขก่อน
    
    if not rule:
        return False, "ไม่พบกฎลิมิต"
    
    # คำนวณยอดรวมปัจจุบัน
    current_total = db.session.query(func.sum(OrderItem.buy_amount)).join(Order).filter(
        OrderItem.number_norm == number_norm,
        OrderItem.field == field,
        Order.batch_id == batch_id,
        Order.status != 'cancelled'
    ).scalar() or 0
    
    # ตรวจสอบลิมิต
    if current_total + amount > rule.limit_amount:
        return True, f"เกินลิมิต: {current_total + amount} > {rule.limit_amount}"
    
    return False, "ผ่านการตรวจสอบลิมิต"
```

### 3. การปรับมาตรฐานเลข
```python
def normalize_number(number, field):
    """ปรับมาตรฐานเลขตาม field"""
    
    number = str(number).strip()
    
    if field in ['2_top', '2_bottom']:
        # เลข 2 หลัก: 00-99
        return number.zfill(2)
    
    elif field == '3_top':
        # เลข 3 หลัก: 000-999
        return number.zfill(3)
    
    elif field == 'tote':
        # โต๊ด: เรียงลำดับจากน้อยไปมาก
        digits = sorted(number.zfill(3))
        return ''.join(digits)
    
    return number

def canonicalize_tote(number):
    """แปลงโต๊ดให้เป็นรูปแบบมาตรฐาน"""
    # เช่น "367", "736", "673" → "367"
    digits = sorted(str(number).zfill(3))
    return ''.join(digits)
```

## การกำหนดค่าเริ่มต้น (Default Configuration)

### Payout Factors
```python
DEFAULT_PAYOUT_FACTORS = {
    '2_top': 90.0,
    '2_bottom': 90.0,
    '3_top': 900.0,
    'tote': 150.0
}

BLOCKED_PAYOUT_FACTOR = 0.5
```

### Limit Amounts
```python
DEFAULT_LIMITS = {
    '2_top': 10000,
    '2_bottom': 10000,
    '3_top': 5000,
    'tote': 8000
}
```

### การโหลดกฎเริ่มต้น
```python
def initialize_default_rules(batch_id=None):
    """โหลดกฎเริ่มต้นลงฐานข้อมูล"""
    
    # Payout rules
    for field, factor in DEFAULT_PAYOUT_FACTORS.items():
        rule = Rule(
            rule_type='payout',
            field=field,
            number_norm=None,  # ใช้กับทุกเลข
            payout_factor=factor,
            scope='per-number',
            condition_type='normal',
            batch_id=batch_id
        )
        db.session.add(rule)
    
    # Limit rules
    for field, limit in DEFAULT_LIMITS.items():
        rule = Rule(
            rule_type='limit',
            field=field,
            number_norm=None,  # ใช้กับทุกเลข
            limit_amount=limit,
            scope='per-number',
            batch_id=batch_id
        )
        db.session.add(rule)
    
    db.session.commit()
```

## การจัดการ Batch ID (อนาคต)

### วัตถุประสงค์
- แยกกฎสำหรับแต่ละงวด
- ป้องกันการทับซ้อนของงวด
- รองรับการเปลี่ยนแปลงกฎในอนาคต

### การใช้งาน
```python
def get_current_batch_id():
    """สร้าง batch_id สำหรับงวดปัจจุบัน"""
    from datetime import datetime
    
    now = datetime.now()
    if now.day <= 16:
        # งวดวันที่ 16
        return f"{now.year}{now.month:02d}16"
    else:
        # งวดวันที่ 1 เดือนถัดไป
        next_month = now.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        return f"{next_month.year}{next_month.month:02d}01"

# ตัวอย่าง: "20240916", "20241001"
```

## การทดสอบ Rules

### Test Cases
1. **เลขปกติ**: ตรวจสอบอัตราจ่ายปกติ
2. **เลขอั้น**: ตรวจสอบอัตราจ่าย 0.5
3. **เกินลิมิต**: ตรวจสอบการปฏิเสธ
4. **โต๊ด**: ตรวจสอบการปรับมาตรฐาน
5. **Batch ID**: ตรวจสอบการแยกงวด

### Unit Tests
```python
def test_normalize_number():
    assert normalize_number("5", "2_top") == "05"
    assert normalize_number("123", "3_top") == "123"
    assert normalize_number("367", "tote") == "367"
    assert normalize_number("736", "tote") == "367"

def test_payout_factor():
    # เลขปกติ
    assert get_payout_factor("05", "2_top") == 90.0
    
    # เลขอั้น
    assert get_payout_factor("00", "2_top") == 45.0  # ถ้า 00 เป็นเลขอั้น

def test_limit_check():
    # ไม่เกินลิมิต
    exceeded, msg = check_limit("05", "2_top", 5000)
    assert not exceeded
    
    # เกินลิมิต
    exceeded, msg = check_limit("05", "2_top", 15000)
    assert exceeded
```

## สรุป
Rule Matrix นี้กำหนดกติกาและกฎเกณฑ์ทั้งหมดสำหรับระบบ Lotoryjung อย่างชัดเจน รองรับการขยายตัวในอนาคต และมีความยืดหยุ่นในการปรับเปลี่ยนกฎตามความต้องการ

