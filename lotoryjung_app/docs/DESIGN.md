# LotoJung System Design

## System Overview
LotoJung เป็นระบบจัดการหมายเลขล็อตเตอรี่ที่ออกแบบมาเพื่อความเรียบง่ายและประสิทธิภาพ

## Core Features

### 1. Auto-Detection System
- **Input Processing**: ระบบตรวจจับประเภทหมายเลขอัตโนมัติจากความยาว
  - 2 หลัก → ประเภท 2_digit
  - 3 หลัก → ประเภท 3_digit
- **No Manual Selection**: ไม่ต้องเลือก field type ด้วยตนเอง

### 2. Permutation Logic
#### 2-Digit Numbers
- Input: `12`
- Output: 4 records
  - `2_top`: 12, 21
  - `2_bottom`: 12, 21

#### 3-Digit Numbers  
- Input: `157`
- Output: 7 records
  - `3_top`: 6 permutations (157, 175, 517, 571, 715, 751)
  - `tote`: 1 record (157)

### 3. Database Schema
```sql
TABLE blocked_numbers (
    id INTEGER PRIMARY KEY,
    number VARCHAR(10) NOT NULL,
    field VARCHAR(20) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. User Interface Design
- **Simplified Layout**: Single-column form without sidebars
- **Clean Input Fields**: No placeholder text distractions
- **Responsive Design**: Bootstrap 5 framework
- **Real-time Validation**: JavaScript validation

## Technical Architecture

### Backend (Flask)
- **Routes**: `/admin/blocked_numbers/*`
- **Validation**: Server-side number validation
- **Database**: SQLite with proper indexing
- **Security**: Input sanitization and CSRF protection

### Frontend (JavaScript)
- **Dynamic Forms**: Add/remove input rows
- **Auto-detection**: Number type detection
- **AJAX Submission**: Seamless form submission

### Database Management
- **Clear Operations**: Multiple methods to clear old data
- **Bulk Insert**: Efficient batch operations
- **Data Integrity**: Foreign key constraints

## Performance Considerations
- **Pagination**: Large dataset handling
- **Indexing**: Optimized database queries
- **Caching**: Static asset optimization

---
*Design Document v2.0 - September 2, 2025*

## ภาพรวมระบบ (System Overview)

ระบบจัดการเลขอั้นหวย (Lottery Blocked Numbers Management System) เป็นเว็บแอปพลิเคชันที่พัฒนาด้วย Flask สำหรับจัดการและควบคุมเลขที่ต้องการบล็อคในระบบหวย

## การออกแบบ UI/UX

### หลักการออกแบบ
1. **ความเรียบง่าย (Simplicity)**: UI ที่เรียบง่าย ไม่ซับซ้อน
2. **การใช้งานง่าย (Usability)**: Auto-detection ประเภทตัวเลขจากความยาว
3. **ประสิทธิภาพ (Efficiency)**: การป้อนข้อมูลและการสร้าง permutations แบบอัตโนมัติ

### Layout Design
- **Full-width Layout**: ใช้พื้นที่เต็มหน้าจอ (col-12)
- **2-Column Input System**: 
  - คอลัมน์ซ้าย: เลข 2 หลัก
  - คอลัมน์ขวา: เลข 3 หลัก
- **Clean Interface**: ไม่มี sidebar cards, statistics, หรือ preview panels

### Color Scheme
- **Primary**: Blue (#007bff) - สำหรับปุ่มหลักและ headers
- **Success**: Green (#28a745) - สำหรับ confirmation และ success states
- **Danger**: Red (#dc3545) - สำหรับการลบและ warning states
- **Warning**: Yellow (#ffc107) - สำหรับ validation messages

## ระบบ Auto-Detection

### หลักการทำงาน
1. **Length-based Detection**: ระบบตรวจสอบจำนวนหลักของตัวเลขที่ป้อน
   - 1-2 หลัก → ประเภท "2_digit"
   - 3 หลัก → ประเภท "3_digit"

2. **Real-time Validation**: ตรวจสอบความถูกต้องทันทีขณะป้อนข้อมูล

### การสร้าง Permutations
- **2 หลัก**: สร้าง 4 permutations (2_top + 2_bottom)
- **3 หลัก**: สร้าง 7 permutations (6 ใน 3_top + 1 ใน tote)

## Database Design

### ตาราง blocked_numbers
```sql
CREATE TABLE blocked_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(10) NOT NULL,
    field VARCHAR(20) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Field Types
- `2_top`: เลข 2 หลักส่วนบน
- `2_bottom`: เลข 2 หลักส่วนล่าง  
- `3_top`: เลข 3 หลักส่วนบน
- `tote`: เลขโต๊ต

## Security Features

### Rate Limiting
- **Bulk Operations**: จำกัด 10 requests ต่อนาที
- **General Routes**: จำกัด 100 requests ต่อนาที

### Input Validation
- **Length Validation**: ตรวจสอบความยาวตัวเลข
- **Pattern Validation**: ยอมรับเฉพาะตัวเลข 0-9
- **XSS Protection**: Escape HTML characters

## Performance Optimization

### Database Operations
- **Bulk Insert**: ใช้ executemany() สำหรับการเพิ่มข้อมูลจำนวนมาก
- **Clear Before Insert**: ล้างข้อมูลเก่าก่อนเพิ่มข้อมูลใหม่
- **Indexed Queries**: Index บน fields ที่ใช้ search บ่อย

### Frontend Optimization
- **Minimal JavaScript**: ใช้ vanilla JavaScript ลดการพึ่งพา libraries
- **Event Delegation**: จัดการ events อย่างมีประสิทธิภาพ
- **DOM Optimization**: อัปเดต DOM เฉพาะส่วนที่จำเป็น

## Error Handling

### Frontend Validation
- **Real-time Feedback**: แสดง error messages ทันที
- **User-friendly Messages**: ข้อความแจ้งเตือนที่เข้าใจง่าย

### Backend Validation
- **Data Integrity**: ตรวจสอบความถูกต้องของข้อมูลก่อนบันทึก
- **Transaction Safety**: ใช้ database transactions
- **Graceful Degradation**: จัดการ errors อย่างสง่างาม

## Responsive Design

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Mobile-first Approach
- ออกแบบสำหรับมือถือก่อน
- Progressive enhancement สำหรับหน้าจอใหญ่

## Accessibility

### WCAG Compliance
- **Keyboard Navigation**: สามารถใช้งานด้วยแป้นพิมพ์
- **Screen Reader Support**: รองรับ screen readers
- **Color Contrast**: สีที่มี contrast เพียงพอ

### Semantic HTML
- ใช้ HTML elements ที่มีความหมาย
- Proper heading hierarchy
- Form labels และ descriptions

## Future Enhancements

### Phase 2 Features
1. **Advanced Analytics**: รายงานและสถิติการใช้งาน
2. **Export/Import**: การนำเข้า/ส่งออกข้อมูล
3. **API Integration**: RESTful API สำหรับ external systems
4. **Real-time Updates**: WebSocket สำหรับการอัปเดตแบบ real-time

### Scalability Considerations
1. **Caching Layer**: Redis สำหรับ cache
2. **Database Sharding**: แบ่ง database เมื่อข้อมูลเยอะ
3. **Load Balancing**: กระจายโหลดเมื่อมี traffic สูง

---

*อัปเดตล่าสุด: September 2, 2025*
*เวอร์ชัน: 2.0 - Simplified UI Design*
