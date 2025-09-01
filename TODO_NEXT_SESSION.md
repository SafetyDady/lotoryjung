# TODO List - Priority Order for Next Session

## 🚨 IMMEDIATE PRIORITY (Session ต่อไป)

### 1. สร้าง Order Form Template
```bash
# ไฟล์ที่ต้องสร้าง/แก้ไข:
/home/safety/lotojung/lotoryjung_app/templates/user/new_order.html
```

**เนื้อหาที่ต้องมี:**
- Form สำหรับใส่หมายเลขลอตเตอรี่ (2-3 หลัก)
- Input สำหรับจำนวนเงินเดิมพัน
- ปุ่ม Submit และ Cancel
- แสดงข้อมูล limit ปัจจุบัน
- Validation ฝั่ง frontend (JavaScript)

### 2. พัฒนา Order Processing Logic
```bash
# ไฟล์ที่ต้องแก้ไข:
/home/safety/lotojung/lotoryjung_app/app/routes/user.py
```

**เพิ่ม Route:**
```python
@user_bp.route('/new_order', methods=['POST'])
@login_required
def submit_order():
    # รับข้อมูลจาก form
    # validate หมายเลข
    # ตรวจสอบ limits
    # บันทึกลงฐานข้อมูล
    # ส่งกลับผลลัพธ์
```

### 3. สร้าง Utility Functions
```bash
# ไฟล์ที่ต้องสร้าง:
/home/safety/lotojung/lotoryjung_app/app/utils/lottery.py
```

**Functions ที่ต้องมี:**
- `validate_lottery_number(number)` - ตรวจสอบรูปแบบหมายเลข
- `normalize_tote(number)` - แปลงเป็น canonical form
- `check_number_limits(user, number, amount)` - ตรวจสอบ limits
- `get_current_lottery_period()` - หาช่วงเวลาลอตเตอรี่ปัจจุบัน

### 4. แก้ไข Template Context
```bash
# ไฟล์ที่ต้องแก้ไข:
/home/safety/lotojung/lotoryjung_app/app/__init__.py
```

**เพิ่ม Context Functions:**
- `get_user_limits()` - ข้อมูล limits ของ user
- `get_blocked_numbers()` - รายการหมายเลขที่ห้าม

## 🔧 SECONDARY PRIORITY

### 5. Admin User Management
```bash
# ไฟล์ที่ต้องแก้ไข:
/home/safety/lotojung/lotoryjung_app/app/routes/admin.py
/home/safety/lotojung/lotoryjung_app/templates/admin/users.html
```

### 6. Blocked Numbers Management
```bash
# ไฟล์ที่ต้องแก้ไข:
/home/safety/lotojung/lotoryjung_app/app/routes/admin.py
/home/safety/lotojung/lotoryjung_app/templates/admin/blocked_numbers.html
```

### 7. Rules & Limits Management
```bash
# ไฟล์ที่ต้องแก้ไข:
/home/safety/lotojung/lotoryjung_app/app/routes/admin.py
/home/safety/lotojung/lotoryjung_app/templates/admin/rules.html
```

## 📋 TESTING PLAN

### การทดสอบสำหรับ Session ต่อไป:
1. **User Flow Testing:**
   - Login → Dashboard → New Order → Submit → ดูผลลัพธ์
   
2. **Order Form Testing:**
   - ใส่หมายเลขถูกต้อง/ผิด
   - ใส่จำนวนเงินต่างๆ
   - ทดสอบ validation
   
3. **Database Testing:**
   - ตรวจสอบ order ถูกบันทึกหรือไม่
   - ตรวจสอบ order_items ถูกต้องหรือไม่

## 🗂️ FILES TO HAVE READY

### Current Working Files:
- ✅ `/home/safety/lotojung/lotoryjung_app/app.py` - Main app
- ✅ `/home/safety/lotojung/lotoryjung_app/app/routes/user.py` - User routes
- ✅ `/home/safety/lotojung/lotoryjung_app/templates/user/dashboard.html` - Dashboard
- ✅ `/home/safety/lotojung/lotoryjung_app/app/models.py` - Database models

### Need to Create/Fix:
- ❌ `/templates/user/new_order.html` - Order form template
- ❌ `/app/utils/lottery.py` - Business logic utilities
- ❌ Order processing in user routes
- ❌ Admin management interfaces

## 🚀 QUICK START COMMANDS FOR NEXT SESSION

```bash
# 1. เข้าไปยัง directory
cd /home/safety/lotojung/lotoryjung_app

# 2. เริ่ม server
python3 app.py

# 3. Test login
# URL: http://localhost:8080
# User: admin / admin123 หรือ user1 / password123

# 4. ทดสอบ dashboard
# URL: http://localhost:8080/user/dashboard

# 5. ทดสอบ order form (หลังจากสร้างแล้ว)
# URL: http://localhost:8080/user/new_order
```

## 📝 SESSION NOTES

**สิ่งที่ทำไปแล้ว:**
- ✅ Git pull สำเร็จ
- ✅ Setup database และ dependencies
- ✅ แก้ไข template errors ใน dashboard
- ✅ Flask server ทำงานได้
- ✅ Authentication system ใช้งานได้

**ปัญหาที่พบ:**
- ❌ ไม่มี order form ให้ user ใช้งาน
- ❌ Business logic ยังไม่ได้ implement
- ❌ Admin features ยังไม่ทำงาน

**เป้าหมายหลัก:**
สร้าง Order Form ที่สมบูรณ์เพื่อให้ user สามารถเดิมพันลอตเตอรี่ได้
