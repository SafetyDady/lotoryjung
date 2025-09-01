# System Design - ระบบรวบรวมและจัดการข้อมูลการทายเลข

## 1. ภาพรวมระบบ (System Overview)

### วัตถุประสงค์
สร้างระบบรวบรวมและจัดการข้อมูลการทายเลขจากสมาชิก รองรับเลข 2 หลัก, 3 หลัก และระบบโต๊ด พร้อมระบบการเดิมพัน "บน" "ล่าง" และ "โต๊ด" รวมถึงการจัดการรายการสมาชิกแต่ละคน

### คุณสมบัติหลัก
- ระบบ Authentication (Login/Logout)
- การจัดการสมาชิก (Admin)
- ระบบสั่งซื้อและตรวจสอบ Limit/เลขอั้น
- Dashboard แสดงยอดรวมแต่ละเลข
- ระบบ Print ใบสั่งซื้อ (PDF)
- Mobile Responsive Design

## 2. สถาปัตยกรรมระบบ (System Architecture)

### Frontend
- **Technology**: HTML5, CSS3, JavaScript (Vanilla)
- **Framework**: Bootstrap 5 (Mobile Responsive)
- **Features**: 
  - Single Page Application (SPA) style
  - AJAX calls สำหรับ Real-time updates
  - Responsive Design สำหรับ Mobile/Desktop

### Backend
- **Technology**: Python Flask
- **Features**:
  - RESTful API
  - Session Management
  - Authentication & Authorization
  - PDF Generation
  - CORS Support

### Database
- **Technology**: SQLite
- **Features**:
  - ACID Compliance
  - File-based storage
  - Built-in backup capabilities

### File Storage
- **PDF Storage**: `/static/receipts/`
- **Database**: `/data/lottery.db`
- **Logs**: `/logs/`

## 3. ผู้ใช้และสิทธิ์ (Users & Permissions)

### Admin
- **สิทธิ์**:
  - สร้าง/แก้ไข/ลบ User
  - ดู Dashboard ยอดรวมทั้งหมด
  - แก้ไขรายการสั่งซื้อของทุก User
  - จัดการ Limit แต่ละประเภท
  - จัดการเลขอั้น
  - Download รายการทั้งหมด (Excel/CSV)

### User
- **สิทธิ์**:
  - ทำรายการสั่งซื้อ
  - ดู Dashboard ของตนเอง
  - แก้ไขรายการสั่งซื้อของตนเอง
  - Download ใบสั่งซื้อ (PDF)

### ข้อมูลผู้ใช้
- **Name**: ชื่อจริง
- **Username**: ชื่อผู้ใช้ (unique)
- **Password**: รหัสผ่าน (bcrypt hashed)

## 4. ระบบการทายเลข (Number System)

### ประเภทเลข
1. **เลข 2 หลัก**: 00-99
   - **บน**: รางวัลที่ 1
   - **ล่าง**: รางวัลท้าย 2 ตัว

2. **เลข 3 หลัก**: 000-999
   - **บน**: รางวัลที่ 1
   - **โต๊ด**: เลข 3 หลักที่มีตัวเลขเดียวกันแต่เรียงต่างกัน

### ตัวอย่างโต๊ด
- เลข 367, 673, 736 → จัดเป็นกลุ่ม 367
- เลข 123, 132, 213, 231, 312, 321 → จัดเป็นกลุ่ม 123

## 5. ระบบ Limit และเลขอั้น

### ระบบ Limit
- **กลุ่ม Limit**:
  - เลข 2 ตัวบน
  - เลข 2 ตัวล่าง
  - เลข 3 ตัวบน
  - โต๊ด

- **การทำงาน**:
  - กำหนด Limit สูงสุดแต่ละกลุ่ม
  - ตรวจสอบยอดรวมใน DB
  - เมื่อเกิน Limit → จ่ายครึ่ง (0.5)

### ระบบเลขอั้น
- **การทำงาน**:
  - Admin กำหนดเลขอั้น
  - เลขอั้น → จ่ายครึ่ง (0.5) ทั้งหมด
  - ไม่ว่าจะซื้อเท่าไร

### ลำดับการตรวจสอบ
1. **ตรวจสอบเลขอั้นก่อน**
2. **ถ้าไม่เป็นเลขอั้น → ตรวจสอบ Limit**
3. **คำนวณราคาจ่าย**
4. **แสดงผลให้ User**

## 6. Flow การทำงาน (Workflow)

### การสั่งซื้อ
1. **User Login** → Redirect ไป Dashboard
2. **ระบบคำนวณงวดวันที่อัตโนมัติ**:
   - วันที่ 1-15 → งวดวันที่ 16 ของเดือนเดียวกัน
   - วันที่ 16-31 → งวดวันที่ 1 ของเดือนถัดไป
3. **กรอกข้อมูล**:
   - ชื่อลูกค้า (ไม่บังคับ)
   - เลขและราคาซื้อ
   - เพิ่มบรรทัด (สูงสุด 20 บรรทัด)
4. **กด "ตรวจสอบราคา"**:
   - ระบบตรวจสอบเลขอั้น
   - ระบบตรวจสอบ Limit
   - แสดงราคาจ่ายจริง
5. **User แก้ไขได้** → ต้องตรวจสอบราคาใหม่
6. **กด "สั่งซื้อ"** (ใช้ได้เมื่อตรวจสอบราคาแล้ว)
7. **ระบบบันทึกเข้า DB** พร้อมงวดวันที่
8. **สร้าง PDF ใบสั่งซื้อ** (แสดงงวดวันที่)
9. **ให้ User Download**

### การจัดการ Admin
1. **User Management**: เพิ่ม/ลบ/แก้ไข User
2. **Limit Management**: ตั้งค่า Limit แต่ละกลุ่ม
3. **Blocked Numbers**: จัดการเลขอั้น
4. **Dashboard**: ดูยอดรวมทั้งหมด
5. **Export Data**: Download รายการ Excel/CSV

## 7. การแสดงผล UI/UX

### หน้า Login (Landing Page)
- **Design**: เรียบง่าย, Mobile Responsive
- **Fields**: Username, Password
- **Redirect**: Admin → Admin Dashboard, User → User Dashboard

### User Dashboard
- **ส่วนที่ 1**: ข้อมูลงวดปัจจุบัน
  - แสดงงวดวันที่ที่จะซื้อ
  - คำนวณอัตโนมัติจากวันที่ปัจจุบัน
- **ส่วนที่ 2**: ฟอร์มสั่งซื้อ
  - ชื่อลูกค้า
  - ตาราง: เลข, บน, ล่าง, โต๊ด, ราคาจ่าย
  - ปุ่ม: เพิ่มบรรทัด, ตรวจสอบราคา, สั่งซื้อ
- **ส่วนที่ 3**: รายการสั่งซื้อของตนเอง
  - แยกตามงวดวันที่
  - แยกแต่ละเลข
  - ยอดรวม
  - ลิงก์ Download PDF

### Admin Dashboard
- **ส่วนที่ 1**: สถิติรวม
  - ยอดรวมแต่ละเลขแยกตามงวดวันที่
  - ยอดรวมงวดปัจจุบัน
  - จำนวน User
  - จำนวนรายการ
- **ส่วนที่ 2**: เมนูจัดการ
  - User Management
  - Limit Settings
  - Blocked Numbers
  - Export Data (แยกตามงวด)

### หน้าจัดการ Limit
- **4 กลุ่ม**: 2ตัวบน, 2ตัวล่าง, 3ตัวบน, โต๊ด
- **ฟิลด์**: จำนวน Limit สูงสุด
- **ปุ่ม**: บันทึก, รีเซ็ต

### หน้าจัดการเลขอั้น
- **ฟอร์มเพิ่ม**: ใส่เลขอั้น
- **ตารางแสดง**: รายการเลขอั้นทั้งหมด
- **ปุ่ม**: เพิ่ม, ลบ

## 8. ระบบ Print ใบสั่งซื้อ

### คุณสมบัติ
- **รูปแบบ**: เรียบง่าย, ขาวดำ
- **ไฟล์**: PDF
- **การใช้งาน**: Download เท่านั้น
- **สิทธิ์**: User เห็นของตนเองเท่านั้น

### ข้อมูลในใบสั่งซื้อ
```
================================
        ใบสั่งซื้อ
================================
เลขที่: ORD001
วันที่: 01/09/2568 14:30:25
งวดวันที่: 16/09/2568
ผู้ขาย: user123
ลูกค้า: ลูกค้า A

--------------------------------
รายการ:
--------------------------------
เลข 37
  2ตัวบน:    50 บาท (จ่าย 1.0)
  2ตัวล่าง:  50 บาท (จ่าย 0.5)

เลข 123
  3ตัวบน:    100 บาท (จ่าย 1.0)
  โต๊ด:      50 บาท (จ่าย 1.0)

--------------------------------
ยอดรวม:     250 บาท
================================
```

## 9. ความปลอดภัย (Security)

### Authentication
- **Session-based**: Flask Session
- **Password**: bcrypt hashing
- **Timeout**: 24 ชั่วโมง

### Authorization
- **Role-based**: Admin, User
- **Route Protection**: Decorator functions
- **CSRF Protection**: Flask-WTF

### Data Protection
- **SQL Injection**: Parameterized queries
- **XSS Protection**: Input sanitization
- **File Upload**: PDF generation only

## 10. การจัดเก็บข้อมูล (Data Storage)

### Database Records
แต่ละรายการสั่งซื้อจะบันทึก:
1. **เลขที่สั่งซื้อ** - Order ID
2. **งวดวันที่** - วันที่หวยออก (คำนวณจากวันที่สั่งซื้อ)
3. **เลข** - หมายเลขที่เดิมพัน
4. **ซื้อ2บน** - จำนวนเงินเดิมพัน 2 ตัวบน
5. **ซื้อ2ล่าง** - จำนวนเงินเดิมพัน 2 ตัวล่าง
6. **ซื้อ3บน** - จำนวนเงินเดิมพัน 3 ตัวบน
7. **ซื้อโต๊ด** - จำนวนเงินเดิมพันโต๊ด
8. **ราคาจ่าย2บน** - ราคาจ่ายจริง 2 ตัวบน
9. **ราคาจ่าย2ล่าง** - ราคาจ่ายจริง 2 ตัวล่าง
10. **ราคาจ่าย3บน** - ราคาจ่ายจริง 3 ตัวบน
11. **ราคาจ่ายโต๊ด** - ราคาจ่ายจริงโต๊ด
12. **ผู้ขาย(User)** - User ที่ทำรายการ
13. **ลูกค้า** - ชื่อลูกค้า (ไม่บังคับ)

### File Management
- **PDF Files**: `/static/receipts/{user_id}/{order_id}.pdf`
- **Database Backup**: Daily automatic backup
- **Log Files**: Application logs และ Error logs

## 11. การขยายระบบ (Scalability)

### ปัจจุบัน
- **Single Server**: Flask + SQLite
- **File Storage**: Local filesystem
- **Session**: Server-side storage

### อนาคต (ถ้าต้องการขยาย)
- **Database**: PostgreSQL/MySQL
- **File Storage**: Cloud storage (AWS S3)
- **Session**: Redis/Memcached
- **Load Balancer**: Nginx
- **Containerization**: Docker

## 12. การบำรุงรักษา (Maintenance)

### Backup Strategy
- **Database**: Daily backup ไฟล์ SQLite
- **PDF Files**: Weekly backup
- **Configuration**: Version control

### Monitoring
- **Application Logs**: Error tracking
- **Performance**: Response time monitoring
- **Storage**: Disk space monitoring

### Updates
- **Security Patches**: Monthly review
- **Feature Updates**: Based on user feedback
- **Database Migration**: Version-controlled scripts

## 13. การทดสอบ (Testing Strategy)

### Unit Testing
- **Models**: Database operations
- **Views**: Route handlers
- **Utils**: Helper functions

### Integration Testing
- **API Endpoints**: Request/Response testing
- **Database**: CRUD operations
- **Authentication**: Login/Logout flow

### User Acceptance Testing
- **Admin Functions**: All management features
- **User Functions**: Order placement and management
- **Mobile Responsive**: Cross-device testing

## 14. การ Deploy (Deployment)

### Development Environment
- **Local**: Flask development server
- **Database**: SQLite file
- **Debug**: Enabled

### Production Environment
- **Server**: Gunicorn + Nginx
- **Database**: SQLite (production mode)
- **SSL**: HTTPS certificate
- **Backup**: Automated daily backup

### Environment Variables
```
FLASK_ENV=production
SECRET_KEY=<random-secret-key>
DATABASE_URL=sqlite:///data/lottery.db
UPLOAD_FOLDER=static/receipts
```

## 15. สรุป

ระบบนี้ออกแบบมาเพื่อจัดการข้อมูลการทายเลขอย่างครบถ้วน โดยมีการตรวจสอบ Limit และเลขอั้นอัตโนมัติ รองรับการใช้งานทั้งบน Desktop และ Mobile พร้อมระบบ Authentication ที่ปลอดภัย และการสร้างใบสั่งซื้อ PDF อัตโนมัติ

ระบบใช้เทคโนโลยีที่เรียบง่ายแต่มีประสิทธิภาพ เหมาะสำหรับการใช้งานในองค์กรขนาดเล็กถึงกลาง และสามารถขยายได้ในอนาคตตามความต้องการ



## 16. การจัดการงวดวันที่ (Lottery Period Management)

### การคำนวณงวดอัตโนมัติ
ระบบจะคำนวณงวดวันที่อัตโนมัติเมื่อ User สั่งซื้อ:

**กฎการคำนวณ:**
- หวยออกทุกวันที่ 1 และ 16 ของเดือน
- วันที่ 1-15 → งวดวันที่ 16 ของเดือนเดียวกัน
- วันที่ 16-31 → งวดวันที่ 1 ของเดือนถัดไป

**ตัวอย่าง:**
- สั่งซื้อ 5 กันยายน 2568 → งวดวันที่ 16 กันยายน 2568
- สั่งซื้อ 20 กันยายน 2568 → งวดวันที่ 1 ตุลาคม 2568

### การแสดงผลในระบบ

**User Dashboard:**
- แสดงงวดวันที่ที่จะซื้อด้านบนฟอร์ม
- รายการสั่งซื้อแยกตามงวด
- สามารถดูประวัติงวดก่อนหน้าได้

**Admin Dashboard:**
- สรุปยอดรวมแยกตามงวด
- เลือกดูข้อมูลงวดใดงวดหนึ่ง
- Export ข้อมูลแยกตามงวด

**PDF Receipt:**
- แสดงงวดวันที่ชัดเจนในใบสั่งซื้อ
- ป้องกันความสับสนเรื่องงวด

### ประโยชน์ของระบบงวด

1. **การจัดกลุ่มข้อมูล**: แยกข้อมูลแต่ละงวดชัดเจน
2. **การรายงาน**: สร้างรายงานยอดขายแยกตามงวด
3. **การตรวจสอบ**: ตรวจสอบยอดก่อนหวยออกแต่ละงวด
4. **การวิเคราะห์**: วิเคราะห์แนวโน้มการซื้อในแต่ละงวด
5. **การบัญชี**: จัดการบัญชีแยกตามงวดได้

### API Endpoints เพิ่มเติม

```python
# ดูข้อมูลงวดปัจจุบัน
GET /api/current-period

# ดูข้อมูลงวดที่ระบุ
GET /api/period/{date}

# ดูรายการสั่งซื้อตามงวด
GET /api/orders/period/{date}

# สรุปยอดตามงวด
GET /api/summary/period/{date}
```

### Database Queries ตัวอย่าง

```sql
-- ดูยอดรวมงวดปัจจุบัน
SELECT 
    lottery_period,
    SUM(total_amount) as total
FROM orders 
WHERE lottery_period = '2024-09-16'
GROUP BY lottery_period;

-- ดูรายการแยกตามงวด
SELECT 
    lottery_period,
    COUNT(*) as order_count,
    SUM(total_amount) as total_amount
FROM orders 
GROUP BY lottery_period
ORDER BY lottery_period DESC;

-- ดูข้อมูลเลขแยกตามงวด
SELECT 
    o.lottery_period,
    oi.number,
    SUM(oi.buy_2_top + oi.buy_2_bottom + oi.buy_3_top + oi.buy_tote) as total_bet
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
WHERE o.lottery_period = '2024-09-16'
GROUP BY o.lottery_period, oi.number
ORDER BY total_bet DESC;
```

