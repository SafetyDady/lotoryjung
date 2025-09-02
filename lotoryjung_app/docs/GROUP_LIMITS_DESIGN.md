# LotoJung Group Limits Management System

## Requirement Analysis

### 1. Current Group Structure
- **2_top**: เลข 2 ตัวบน
- **2_bottom**: เลข 2 ตัวล่าง  
- **3_top**: เลข 3 ตัวบน
- **tote**: เลขโต๊ด

### 2. Limit Types Needed
- **Global Limits**: ขวดเงินรวมต่อกลุ่ม
- **Individual Number Limits**: ขวดเงินต่อเลขแต่ละตัว
- **Daily Limits**: ขวดรายวัน
- **Batch Limits**: ขวดต่อรอบการขาย

### 3. Implementation Plan

#### Phase 1: Global Group Limits
- สร้างหน้าจัดการ limit แต่ละกลุ่ม
- เพิ่ม validation ก่อนการ save order
- แสดง current usage vs limits

#### Phase 2: Advanced Features  
- Individual number limits
- Real-time limit monitoring
- Limit alerts and notifications

## Technical Design

### Database Schema (Already exists in Rule model)
```sql
-- Use existing Rule table with rule_type = 'limit'
INSERT INTO rules (rule_type, field, number_norm, value, is_active) VALUES
('limit', '2_top', NULL, 1000000.00, true),      -- Global limit for 2_top
('limit', '2_bottom', NULL, 800000.00, true),    -- Global limit for 2_bottom  
('limit', '3_top', NULL, 500000.00, true),       -- Global limit for 3_top
('limit', 'tote', NULL, 300000.00, true);        -- Global limit for tote
```

### UI Requirements
1. **Group Limits Dashboard**
   - แสดง limits ปัจจุบันของแต่ละกลุ่ม
   - แสดงการใช้งานจริง (current usage)
   - Progress bars แสดง % การใช้งาน

2. **Edit Limits Form**
   - Form สำหรับแก้ไข limit แต่ละกลุ่ม
   - Validation และ confirmation

3. **Integration with Order System**
   - ตรวจสอบ limits ก่อน confirm order
   - แสดงเตือนเมื่อใกล้เต็ม limit

### Files to Create/Modify
1. `/templates/admin/group_limits.html` - หน้าจัดการ limits
2. `/app/routes/admin.py` - เพิ่ม routes สำหรับ limits
3. `/app/services/limit_service.py` - Business logic
4. `/static/js/limits.js` - Frontend functionality

---
*Next Steps: Create the Group Limits management interface*
