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
   - วันที่ 1-16 → งวดวันที่ 16 ของเดือนเดียวกัน
   - วันที่ 17-31 → งวดวันที่ 1 ของเดือนถัดไป
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
- วันที่ 1-16 → งวดวันที่ 16 ของเดือนเดียวกัน
- วันที่ 17-31 → งวดวันที่ 1 ของเดือนถัดไป

**ตัวอย่าง:**
- สั่งซื้อ 5 กันยายน 2568 → งวดวันที่ 16 กันยายน 2568
- สั่งซื้อ 16 กันยายน 2568 → งวดวันที่ 16 กันยายน 2568
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


## 17. การจัดการไฟล์ PDF (PDF File Management)

### โครงสร้างการเก็บไฟล์

```
project_root/
├── static/
│   └── receipts/
│       ├── user_1/
│       │   ├── ORD20240901143025.pdf
│       │   ├── ORD20240902150130.pdf
│       │   └── ...
│       ├── user_2/
│       │   ├── ORD20240901144512.pdf
│       │   └── ...
│       └── admin/
│           ├── daily_reports/
│           └── monthly_reports/
```

### รูปแบบการตั้งชื่อไฟล์

**ไฟล์ PDF ใบสั่งซื้อ:**
- **รูปแบบ**: `{order_number}.pdf`
- **ตัวอย่าง**: `ORD20240901143025.pdf`
- **Path เต็ม**: `/static/receipts/{user_id}/ORD20240901143025.pdf`

**Order Number Format:**
- **รูปแบบ**: `ORD{YYYYMMDD}{HHMMSS}`
- **ORD**: คำนำหน้าคงที่
- **YYYYMMDD**: ปี-เดือน-วัน (8 หลัก)
- **HHMMSS**: ชั่วโมง-นาที-วินาที (6 หลัก)

### การสร้างและเก็บ PDF

**ขั้นตอนการสร้าง:**
1. User กด "สั่งซื้อ" หลังตรวจสอบราคาแล้ว
2. ระบบสร้าง Order Number อัตโนมัติ
3. บันทึกข้อมูลลงฐานข้อมูล
4. สร้างไฟล์ PDF จากข้อมูล Order
5. เก็บไฟล์ในโฟลเดอร์ของ User
6. บันทึก PDF path ลงฐานข้อมูล
7. ส่ง Download link ให้ User

**Python Code ตัวอย่าง:**
```python
import os
from datetime import datetime
from reportlab.pdfgen import canvas

def generate_pdf_receipt(order_data, user_id):
    # สร้าง order number
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    order_number = f"ORD{timestamp}"
    
    # สร้าง directory ถ้ายังไม่มี
    user_dir = f"static/receipts/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    
    # path ของไฟล์ PDF
    pdf_path = f"{user_dir}/{order_number}.pdf"
    
    # สร้าง PDF
    c = canvas.Canvas(pdf_path)
    # ... เขียนข้อมูลลง PDF ...
    c.save()
    
    return pdf_path, order_number
```

### การเข้าถึงไฟล์ PDF (Secure Access)

**ระบบความปลอดภัย:**
- **Authentication Required**: ต้อง login ถึงจะเข้าถึงได้
- **Indirect Access**: ไม่เปิดเผย path จริงของไฟล์
- **Token-based**: ใช้ temporary token สำหรับดาวน์โหลด
- **Time-limited**: Token หมดอายุใน 1 ชั่วโมง

**สิทธิ์การเข้าถึง:**
- **User**: เห็นเฉพาะ PDF ของตนเองเท่านั้น
- **Admin**: เห็น PDF ของทุกคนได้

**Secure URL Pattern:**
```
GET /secure/download/{token}
- ไม่เปิดเผย order_id หรือ file path
- ใช้ temporary token แทน
- Token หมดอายุอัตโนมัติ
```

**Token Generation Process:**
```python
import secrets
import hashlib
from datetime import datetime, timedelta

def generate_download_token(order_id, user_id):
    # สร้าง unique token
    timestamp = datetime.now().isoformat()
    random_string = secrets.token_urlsafe(32)
    token_data = f"{order_id}:{user_id}:{timestamp}:{random_string}"
    
    # Hash เพื่อความปลอดภัย
    token = hashlib.sha256(token_data.encode()).hexdigest()
    
    # เก็บ token ในฐานข้อมูลพร้อม expiry
    expiry = datetime.now() + timedelta(hours=1)
    save_download_token(token, order_id, user_id, expiry)
    
    return token
```

**Flask Route ตัวอย่าง:**
```python
@app.route('/generate-download-link/<int:order_id>')
@login_required
def generate_download_link(order_id):
    order = Order.query.get_or_404(order_id)
    
    # ตรวจสอบสิทธิ์
    if current_user.role != 'admin' and order.user_id != current_user.id:
        abort(403)
    
    # สร้าง secure token
    token = generate_download_token(order_id, current_user.id)
    
    return jsonify({
        'download_url': f'/secure/download/{token}',
        'expires_in': 3600  # 1 hour
    })

@app.route('/secure/download/<token>')
@login_required
def secure_download(token):
    # ตรวจสอบ token
    token_data = verify_download_token(token, current_user.id)
    if not token_data:
        abort(404)  # ไม่บอกว่า token หมดอายุ
    
    order = Order.query.get_or_404(token_data['order_id'])
    
    # ตรวจสอบสิทธิ์อีกครั้ง
    if current_user.role != 'admin' and order.user_id != current_user.id:
        abort(403)
    
    # ลบ token หลังใช้งาน (one-time use)
    delete_download_token(token)
    
    # ส่งไฟล์โดยไม่เปิดเผย path
    return send_file(
        order.pdf_path, 
        as_attachment=True,
        download_name=f"{order.order_number}.pdf"
    )
```

### การแสดงผลใน UI (Secure Download)

**ในหน้า User Dashboard:**
```html
<div class="order-history">
    <h3>รายการสั่งซื้อ</h3>
    <table>
        <tr>
            <th>เลขที่</th>
            <th>วันที่</th>
            <th>งวด</th>
            <th>ยอดรวม</th>
            <th>ใบสั่งซื้อ</th>
        </tr>
        {% for order in orders %}
        <tr>
            <td>{{ order.order_number }}</td>
            <td>{{ order.created_at.strftime('%d/%m/%Y %H:%M') }}</td>
            <td>{{ order.lottery_period.strftime('%d/%m/%Y') }}</td>
            <td>{{ order.total_amount }} บาท</td>
            <td>
                <button onclick="downloadPDF({{ order.id }})" 
                        class="btn btn-sm btn-primary">
                    <i class="fas fa-download"></i> ดาวน์โหลด
                </button>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>

<script>
async function downloadPDF(orderId) {
    try {
        // ขอ secure download link
        const response = await fetch(`/generate-download-link/${orderId}`);
        
        if (!response.ok) {
            throw new Error('ไม่สามารถสร้าง download link ได้');
        }
        
        const data = await response.json();
        
        // เปิด download link ในหน้าต่างใหม่
        window.open(data.download_url, '_blank');
        
    } catch (error) {
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}
</script>
```

**ข้อดีของระบบนี้:**
1. **ไม่เปิดเผย file path**: User ไม่รู้ว่าไฟล์อยู่ที่ไหน
2. **Token-based**: ใช้ token แทน direct link
3. **Time-limited**: Token หมดอายุอัตโนมัติ
4. **One-time use**: Token ใช้ได้ครั้งเดียว
5. **Double authentication**: ตรวจสอบสิทธิ์ 2 ครั้ง

### การสำรองข้อมูล (Backup)

**กลยุทธ์การสำรอง:**
1. **Daily Backup**: สำรอง PDF files ทุกวัน
2. **Weekly Full Backup**: สำรองทั้งหมดทุกสัปดาห์
3. **Cloud Backup**: อัพโหลดไป Cloud storage (อนาคต)

**Backup Script ตัวอย่าง:**
```bash
#!/bin/bash
# backup_pdfs.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/pdfs/$DATE"
SOURCE_DIR="/app/static/receipts"

# สร้าง backup directory
mkdir -p $BACKUP_DIR

# สำรองไฟล์
tar -czf "$BACKUP_DIR/receipts_$DATE.tar.gz" -C $SOURCE_DIR .

# ลบ backup เก่าที่เก็บไว้เกิน 30 วัน
find /backup/pdfs -name "*.tar.gz" -mtime +30 -delete
```

### การจัดการพื้นที่เก็บข้อมูล

**การประมาณขนาด:**
- PDF ใบสั่งซื้อ: ~50-100 KB ต่อไฟล์
- 100 orders/วัน = ~5-10 MB/วัน
- 1 ปี = ~1.8-3.6 GB

**การทำความสะอาด:**
- เก็บ PDF ไว้ 2 ปี
- หลัง 2 ปี ย้ายไป Archive storage
- ลบไฟล์ที่เสียหายหรือไม่สมบูรณ์

### การแก้ไขปัญหา (Troubleshooting)

**ปัญหาที่อาจเกิด:**
1. **ไฟล์ PDF หาย**: ตรวจสอบ backup และ restore
2. **Permission Error**: ตรวจสอบสิทธิ์โฟลเดอร์
3. **Disk Full**: ทำความสะอาดไฟล์เก่า
4. **PDF เสียหาย**: สร้างใหม่จากข้อมูลในฐานข้อมูล

**Monitoring:**
```python
# ตรวจสอบขนาดโฟลเดอร์
def check_storage_usage():
    receipts_dir = "static/receipts"
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(receipts_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    
    return total_size / (1024 * 1024)  # MB
```


### Database Schema สำหรับ Download Tokens

**ตาราง download_tokens:**
```sql
CREATE TABLE download_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(64) UNIQUE NOT NULL,
    order_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_download_tokens_token ON download_tokens(token);
CREATE INDEX idx_download_tokens_expires_at ON download_tokens(expires_at);
CREATE INDEX idx_download_tokens_order_id ON download_tokens(order_id);
```

**Helper Functions:**
```python
def save_download_token(token, order_id, user_id, expiry):
    """บันทึก download token ลงฐานข้อมูล"""
    db.session.execute(
        "INSERT INTO download_tokens (token, order_id, user_id, expires_at) "
        "VALUES (?, ?, ?, ?)",
        (token, order_id, user_id, expiry)
    )
    db.session.commit()

def verify_download_token(token, user_id):
    """ตรวจสอบ download token"""
    result = db.session.execute(
        "SELECT order_id, user_id, expires_at, used_at "
        "FROM download_tokens "
        "WHERE token = ? AND user_id = ?",
        (token, user_id)
    ).fetchone()
    
    if not result:
        return None
    
    # ตรวจสอบว่าหมดอายุหรือไม่
    if datetime.now() > result['expires_at']:
        return None
    
    # ตรวจสอบว่าใช้แล้วหรือไม่
    if result['used_at']:
        return None
    
    return {
        'order_id': result['order_id'],
        'user_id': result['user_id']
    }

def delete_download_token(token):
    """ลบ token หลังใช้งาน"""
    db.session.execute(
        "UPDATE download_tokens SET used_at = ? WHERE token = ?",
        (datetime.now(), token)
    )
    db.session.commit()

def cleanup_expired_tokens():
    """ลบ token ที่หมดอายุ (รันเป็น cron job)"""
    db.session.execute(
        "DELETE FROM download_tokens WHERE expires_at < ?",
        (datetime.now(),)
    )
    db.session.commit()
```

### การป้องกันการโจมตี (Security Measures)

**1. Rate Limiting:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/generate-download-link/<int:order_id>')
@limiter.limit("10 per minute")  # จำกัดการขอ token
@login_required
def generate_download_link(order_id):
    # ... code ...
```

**2. Token Validation:**
```python
def is_valid_token_format(token):
    """ตรวจสอบรูปแบบ token"""
    import re
    # Token ต้องเป็น hex string ยาว 64 ตัวอักษร
    return bool(re.match(r'^[a-f0-9]{64}$', token))

@app.route('/secure/download/<token>')
@login_required
def secure_download(token):
    # ตรวจสอบรูปแบบ token ก่อน
    if not is_valid_token_format(token):
        abort(404)
    
    # ... rest of code ...
```

**3. Logging และ Monitoring:**
```python
import logging

def log_download_attempt(user_id, order_id, token, success=True):
    """บันทึก log การดาวน์โหลด"""
    logger = logging.getLogger('download_security')
    
    if success:
        logger.info(f"Download success: user={user_id}, order={order_id}")
    else:
        logger.warning(f"Download failed: user={user_id}, token={token[:8]}...")

# ใน secure_download function
@app.route('/secure/download/<token>')
@login_required
def secure_download(token):
    try:
        # ... validation code ...
        log_download_attempt(current_user.id, order.id, token, True)
        return send_file(...)
    except Exception as e:
        log_download_attempt(current_user.id, None, token, False)
        abort(404)
```

**4. Additional Security Headers:**
```python
@app.after_request
def add_security_headers(response):
    """เพิ่ม security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

### การทดสอบระบบ (Testing)

**Unit Tests:**
```python
def test_generate_download_token():
    """ทดสอบการสร้าง token"""
    token = generate_download_token(1, 1)
    assert len(token) == 64
    assert is_valid_token_format(token)

def test_token_expiry():
    """ทดสอบการหมดอายุของ token"""
    # สร้าง token ที่หมดอายุแล้ว
    expired_token = create_expired_token()
    result = verify_download_token(expired_token, 1)
    assert result is None

def test_one_time_use():
    """ทดสอบการใช้ token ครั้งเดียว"""
    token = generate_download_token(1, 1)
    
    # ใช้ครั้งแรก - ควรสำเร็จ
    result1 = verify_download_token(token, 1)
    assert result1 is not None
    
    delete_download_token(token)
    
    # ใช้ครั้งที่สอง - ควรล้มเหลว
    result2 = verify_download_token(token, 1)
    assert result2 is None
```

