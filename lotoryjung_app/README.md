# 🎰 Lotoryjung - Advanced Lotte### 🛒 Bulk Order Form System (COMPLETED) ⭐
- **Multi-row Orders** - สั่งซื้อหลายรายการพร้อมกัน (สูงสุด 20 บรรทัด)
- **2-Step Validation** - ตรวจสอบรายบรรทัด และ ตรวจสอบทั้งหมด
- **Field Restrictions** - 
  - เลข 2 ตัว: ซื้อ "บน" และ "ล่าง" ได้เท่านั้น
  - เลข 3 ตัว: ซื้อ "3 ตัวบน" และ "โต๊ด" ได้เท่านั้น
- **Real-time Field Validation** - ป้องกันการใส่ข้อมูลผิดประเภท
- **Dynamic Payout Display** - แสดงอัตราการจ่ายหลังการตรวจสอบ
- **External Calculation Architecture** - รองรับการคำนวณจากระบบภายนอก
- **Complete Database Integration** - บันทึกข้อมูลครบถ้วนในฐานข้อมูล

### 💾 Database-Driven Payout System (COMPLETED) ⭐
- **Dynamic Payout Rates** - ดึงอัตราการจ่ายจากฐานข้อมูล
- **External Calculation Support** - รองรับการคำนวณจากระบบภายนอก
- **Validation Factors** - บันทึกปัจจัยการตรวจสอบ (1.0x หรือ 0.5x)
- **Message Text Updates** - ข้อความเตือน "มียอดซื้อเกินโควต้า"
- **Legacy Database Compatibility** - รองรับทั้ง schema เก่าและใหม่
- **Complete Field Mapping** - แมปข้อมูลระหว่าง validation และ database fieldsSystem

เป็นระบบจัดการลอตเตอรี่ที่ครบครันด้วย Flask framework พร้อมระบบจัดการขีดจำกัดขั้นสูงและการจัดการเลขอั้น

## 🚀 Features Overview

### 🎯 Core Functionality
- **User Authentication System** - ระบบลงทะเบียนและเข้าสู่ระบบ
- **Order Management** - จัดการคำสั่งซื้อลอตเตอรี่
- **Admin Dashboard** - แดชบอร์ดสำหรับผู้ดูแลระบบ
- **Audit Logging** - บันทึกการเปลี่ยนแปลงระบบ

### 🔒 Blocked Numbers Management
- **Bulk Operations** - เพิ่มเลขอั้นหลายตัวพร้อมกัน
- **Auto-detection** - ตรวจจับประเภทเลขอัตโนมัติตามความยาว
- **Permutation Generation** - สร้างเลขสลับที่อัตโนมัติ
- **Advanced Search & Filter** - ค้นหาและกรองข้อมูลขั้นสูง

### 📊 Limits Management System

#### Group Limits (ขีดจำกัดกลุ่ม)
- **Default Limits Setting** - กำหนดขีดจำกัดเริ่มต้นสำหรับแต่ละประเภท
- **Real-time Usage Tracking** - ติดตามการใช้งานแบบเรียลไทม์
- **Visual Progress Bars** - แสดงผลการใช้งานด้วยกราฟแท่ง
- **Automated Limit Validation** - ตรวจสอบขีดจำกัดอัตโนมัติ

#### Individual Number Limits (ขีดจำกัดเลขแต่ละตัว) ⭐
- **Granular Control** - ควบคุมขีดจำกัดเฉพาะเลขแต่ละตัว
- **Priority-based Validation** - ระบบตรวจสอบตามลำดับความสำคัญ
- **CRUD Operations** - เพิ่ม/แก้ไข/ลบ ขีดจำกัดเฉพาะเลข
- **Override Default Limits** - แทนที่ขีดจำกัดเริ่มต้นได้

### �️ Bulk Order Form System (NEW) ⭐
- **Multi-row Orders** - สั่งซื้อหลายรายการพร้อมกัน (สูงสุด 20 บรรทัด)
- **2-Step Validation** - ตรวจสอบรายบรรทัด และ ตรวจสอบทั้งหมด
- **Field Restrictions** - 
  - เลข 2 ตัว: ซื้อ "บน" และ "ล่าง" ได้เท่านั้น
  - เลข 3 ตัว: ซื้อ "3 ตัวบน" และ "โต๊ด" ได้เท่านั้น
- **Real-time Field Validation** - ป้องกันการใส่ข้อมูลผิดประเภท
- **Dynamic Payout Display** - แสดงอัตราการจ่ายหลังการตรวจสอบ

### 💾 Database-Driven Payout System (NEW) ⭐
- **Dynamic Payout Rates** - ดึงอัตราการจ่ายจากฐานข้อมูล
- **External Calculation Support** - รองรับการคำนวณจากระบบภายนอก
- **Validation Factors** - บันทึกปัจจัยการตรวจสอบ (1.0x หรือ 0.5x)
- **Message Text Updates** - ข้อความเตือน "มียอดซื้อเกินโควต้า"

### �🛡️ Security Features
- **CSRF Protection** - ป้องกันการโจมตี Cross-Site Request Forgery
- **Admin Authorization** - ระบบสิทธิ์ผู้ดูแลระบบ
- **Input Validation** - ตรวจสอบข้อมูลนำเข้าทุกขั้นตอน
- **SQL Injection Prevention** - ป้องกันการโจมตี SQL Injection

## 🏗️ System Architecture

### 📋 Validation Priority Logic
```
Priority 1: Blocked Numbers Check
    ├── If blocked → 0.5x payout rate, message: "เลขอั้น"
    └── If not blocked → Continue

Priority 2: Individual Limits Check  
    ├── If individual limit exists → Use individual limit
    │   ├── If over limit → 0.5x payout rate, message: "มียอดซื้อเกินโควต้า"
    │   └── If within limit → 1.0x payout rate
    └── If no individual limit → Continue

Priority 3: Default Group Limits
    ├── If over group limit → 0.5x payout rate, message: "มียอดซื้อเกินโควต้า"
    └── If within group limit → 1.0x payout rate
```

### 🎲 Field Types Supported
- **2_top** (2 ตัวบน) - 2-digit top lottery
- **2_bottom** (2 ตัวล่าง) - 2-digit bottom lottery  
- **3_top** (3 ตัวบน) - 3-digit top lottery
- **tote** (โต๊ด) - Tote betting

### 🎯 Bulk Order Form Field Restrictions
- **เลข 2 ตัว**: สามารถเลือก "ซื้อบน" หรือ "ซื้อล่าง" ได้เท่านั้น (ไม่สามารถซื้อโต๊ดได้)
- **เลข 3 ตัว**: สามารถเลือก "ซื้อ 3 ตัวบน" หรือ "ซื้อโต๊ด" ได้เท่านั้น (ไม่สามารถซื้อล่างได้)
- **จำนวนรายการ**: สูงสุด 20 บรรทัดต่อคำสั่งซื้อ

### 💾 Database Schema (UPDATED) ⭐

#### ตารางหลัก (Core Tables)
```sql
-- User authentication
user                 
├── id (PK)
├── username (Unique)
├── password_hash
├── role (user/admin)
└── is_active

-- Orders and order items with validation factors
order               
├── id (PK)
├── order_number (Unique, Auto-generated)
├── user_id (FK)
├── customer_name
├── total_amount
├── status
├── lottery_period
└── batch_id

order_item (ENHANCED) ⭐          
├── id (PK)
├── order_id (FK)
├── field (2_top/2_bottom/3_top/tote)
├── number (NEW) -- หมายเลขต้นฉบับ
├── number_norm -- หมายเลขที่ normalize แล้ว
├── amount (NEW) -- จำนวนเงินซื้อ
├── validation_factor (NEW) -- ปัจจัยการตรวจสอบ (1.0 หรือ 0.5)
├── validation_reason (NEW) -- เหตุผลการปรับอัตรา
├── current_usage_at_time (NEW) -- ยอดใช้ ณ เวลาตรวจสอบ
├── limit_at_time (NEW) -- ขีดจำกัด ณ เวลาตรวจสอบ
├── is_blocked (NEW) -- สถานะเลขอั้น ณ เวลาตรวจสอบ
├── number_input (LEGACY) -- เก็บ compatibility กับ schema เก่า
├── buy_amount (LEGACY) -- เก็บ compatibility กับ schema เก่า
├── payout_rate (LEGACY) -- อัตราการจ่าย (รองรับ schema เก่า)
├── potential_payout (LEGACY) -- ผลตอบแทนโดยประมาณ
└── created_at

-- Rules for limits and payout rates (database-driven)
rule                
├── id (PK)
├── rule_type (limit/blocked/payout)
├── field (2_top/2_bottom/3_top/tote)
├── number_norm (NULL for defaults)
├── value
└── is_active

-- Blocked numbers
blocked_number      
├── id (PK)
├── number_norm
├── field
└── is_active

-- Usage tracking (ENHANCED)
number_total        
├── id (PK)
├── batch_id (NEW) -- ระบุ batch สำหรับติดตาม
├── number_norm
├── field
├── total_amount
├── order_count (NEW) -- จำนวนคำสั่งซื้อ
└── last_updated

-- Audit logging
audit_log          
├── id (PK)
├── user_id (FK)
├── action
├── details
└── timestamp
```

### 🔗 External Calculation Support
ระบบออกแบบมาเพื่อรองรับการคำนวณจากระบบภายนอก:
- **Validation Factors**: บันทึกปัจจัยการตรวจสอบ (1.0x ปกติ, 0.5x ลดครึ่ง)
- **Historical Context**: เก็บข้อมูล usage และ limit ณ เวลาที่ตรวจสอบ
- **Legacy Compatibility**: รองรับ schema เก่าเพื่อความต่อเนื่อง

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite3 (included in Python)
- Flask and dependencies (see requirements.txt)

### Installation
```bash
# Clone repository
git clone https://github.com/SafetyDady/lotoryjung.git
cd lotoryjung_app

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create default users and setup data
python -c "
from app import create_app, db
from app.models import User, Rule
app = create_app()
with app.app_context():
    # Create users
    admin = User(username='admin', name='Administrator', role='admin')
    admin.set_password('admin123')
    user = User(username='testuser', name='Test User', role='user')
    user.set_password('test123')
    db.session.add_all([admin, user])
    
    # Create default payout rates
    payout_rates = [
        Rule(rule_type='payout', field='2_top', value=90),
        Rule(rule_type='payout', field='2_bottom', value=90),
        Rule(rule_type='payout', field='3_top', value=900),
        Rule(rule_type='payout', field='tote', value=150)
    ]
    db.session.add_all(payout_rates)
    
    # Create default group limits
    default_limits = [
        Rule(rule_type='limit', field='2_top', value=1000),
        Rule(rule_type='limit', field='2_bottom', value=1000),
        Rule(rule_type='limit', field='3_top', value=500),
        Rule(rule_type='limit', field='tote', value=500)
    ]
    db.session.add_all(default_limits)
    
    db.session.commit()
    print('Database initialized successfully')
"

# Start server
python app.py
```

### Default Access
- **URL**: http://127.0.0.1:5002
- **Admin Login**: admin / admin123
- **Test User**: testuser / test123

## 📱 User Interface Features

### 🛍️ Bulk Order Form
- **URL**: `/bulk_order_form` (user login required)
- สั่งซื้อหลายรายการพร้อมกัน (สูงสุด 20 บรรทัด)
- ตรวจสอบความถูกต้องแบบ 2-ขั้นตอน
- แสดงอัตราการจ่ายและขีดจำกัดแบบเรียลไทม์
- Field restrictions enforcement

### 🎯 Single Order Form  
- **URL**: `/order` (user login required)
- สั่งซื้อรายการเดียว
- ตรวจสอบขีดจำกัดทันที
- การคำนวณการจ่ายแบบทันที

## 📱 Admin Panel Features

### 🏠 Dashboard
- System statistics overview
- Recent orders display
- Quick access buttons
- Performance metrics

### 🚫 Blocked Numbers Management
- **URL**: `/admin/blocked_numbers`
- Bulk add/edit/delete operations
- Auto-permutation generation
- Search and filtering capabilities

### 📊 Group Limits Management  
- **URL**: `/admin/group_limits`
- Default limits configuration
- Real-time usage monitoring
- Visual progress indicators

### 🎯 Individual Limits Management ⭐
- **URL**: `/admin/individual_limits`
- Granular number-specific limits
- Override default group limits
- Advanced filtering and search
- Modal-based CRUD operations

## 🔧 API Endpoints

### Bulk Order Validation APIs (COMPLETED) ⭐
```http
# Validate Bulk Order 
POST /api/validate_bulk_order
Content-Type: application/json
X-CSRFToken: <token>

{
    "orders": [
        {
            "rowId": "row_123456789",
            "number": "44",
            "amount_2_top": 100,
            "amount_2_bottom": 50,
            "amount_tote": 0
        }
    ]
}

# Response
{
    "success": true,
    "validation_results": [...],
    "summary": {
        "total_amount": 150,
        "estimated_payout": 13500,
        "normal_payout_items": 2,
        "reduced_payout_items": 0
    }
}

# Submit Bulk Order (COMPLETED) ⭐
POST /api/submit_bulk_order
Content-Type: application/json
X-CSRFToken: <token>

{
    "orders": [...],
    "customer_name": "ลูกค้า A"
}

# Response - External Calculation Support
{
    "success": true,
    "order_number": "ORD20250902AA83184C",
    "external_calculation_data": [
        {
            "order_item_id": 1,
            "number": "123",
            "field": "3_top",
            "amount": 10.0,
            "validation_factor": 0.5,
            "validation_reason": "เลขอั้น - Factor 0.5x",
            "for_external_calculation": {
                "base_payout_rate": 900,
                "suggested_payout": 4500.0
            }
        }
    ]
}

# Get Payout Rates (Database-Driven) ⭐
GET /api/get_payout_rates

# Response
{
    "success": true,
    "rates": {
        "2_top": 90,
        "2_bottom": 90,
        "3_top": 900,
        "tote": 150
    }
}
```

### Individual Limits APIs
```http
# Set/Update Individual Limit
POST /admin/api/set_individual_limit
Content-Type: application/json
X-CSRFToken: <token>

{
    "field": "2_top",
    "number_norm": "12", 
    "limit_amount": 500
}

# Delete Individual Limit
POST /admin/api/delete_individual_limit
Content-Type: application/json
X-CSRFToken: <token>

{
    "field": "2_top",
    "number_norm": "12"
}
```

### Group Limits APIs
```http
# Update Group Limit
POST /admin/api/update_group_limit
Content-Type: application/json

{
    "field": "2_top",
    "limit": 1000000
}

# Get Dashboard Data
GET /admin/group_limits/api/dashboard_data?batch_id=20250902
```

## 🎨 Frontend Technologies

- **Bootstrap 5.3.0** - UI framework
- **Font Awesome** - Icons
- **jQuery** - AJAX operations  
- **JavaScript ES6** - Modern JavaScript features
- **Jinja2** - Template engine

## 🔍 Usage Examples

### Bulk Order Form Validation
```javascript
// JavaScript field validation example
function validateNumberAndToggleFields(inputElement) {
    const number = inputElement.value.trim();
    const row = inputElement.closest('tr');
    
    if (number.length === 2) {
        // Enable 2-digit fields, disable 3-digit/tote
        row.querySelector('[name="amount_2_top"]').disabled = false;
        row.querySelector('[name="amount_2_bottom"]').disabled = false;
        row.querySelector('[name="amount_3_top"]').disabled = true;
        row.querySelector('[name="amount_tote"]').disabled = true;
    } else if (number.length === 3) {
        // Enable 3-digit/tote fields, disable 2-digit bottom
        row.querySelector('[name="amount_2_top"]').disabled = true;
        row.querySelector('[name="amount_2_bottom"]').disabled = true;
        row.querySelector('[name="amount_3_top"]').disabled = false;
        row.querySelector('[name="amount_tote"]').disabled = false;
    }
}
```

### Adding Individual Limit
```python
from app.services.limit_service import LimitService

# Set limit of 500 for number "12" in 2_top category
success = LimitService.set_individual_limit("2_top", "12", 500)
```

### Validating Order with External Calculation Support
```python
# Validate order with validation factors for external calculation
result = LimitService.validate_order_item("2_top", "12", 300)
print(f"Validation factor: {result['validation_factor']}x")
print(f"Reason: {result['validation_reason']}")
print(f"Base payout rate: {result['base_payout_rate']}")
```

### Getting Current Usage
```python
# Get current usage for specific number
usage = LimitService.get_current_usage("2_top", "12", "20250902")
print(f"Current usage: {usage} บาท")
```

## 📈 System Monitoring

### Performance Metrics
- Order processing speed
- Database query optimization
- Memory usage tracking
- Real-time user activity

### Audit Trail
- All admin actions logged
- User authentication tracking
- Limit changes monitoring
- System configuration changes

## 🛠️ Development Tools

### Debugging Features
- Flask debug mode
- Server-side logging
- JavaScript console logging
- Database query monitoring

### Testing Capabilities
- Manual testing tools
- API endpoint testing
- Database integrity checks
- Security validation tests

## 📖 Documentation

### Available Documents
- **[INDIVIDUAL_LIMITS_DESIGN.md](docs/INDIVIDUAL_LIMITS_DESIGN.md)** - Individual limits system design
- **[GROUP_LIMITS_DESIGN.md](docs/GROUP_LIMITS_DESIGN.md)** - Group limits system design  
- **[STRUCTURE.md](docs/STRUCTURE.md)** - Project structure overview
- **[PROGRESS.md](docs/PROGRESS.md)** - Development progress log
- **[INSTALLATION.md](docs/INSTALLATION.md)** - Installation guide

## 🚧 Future Enhancements

### Planned Features
- [ ] Mobile app API endpoints
- [ ] CSV/Excel export functionality
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Bulk individual limits operations
- [ ] Time-based limit rules
- [ ] API rate limiting
- [ ] Real-time notifications

- SQL query profiling
- Error logging and monitoring
- Development environment setup

### Testing Framework
- Unit tests for service layer
- Integration tests for API endpoints
- Frontend validation testing
- Database migration testing

## 🚦 Deployment

### Production Considerations
- **Environment Variables**: Configure production settings
- **Database**: Use PostgreSQL for production
- **Web Server**: Deploy with Gunicorn + Nginx
- **SSL Certificate**: Enable HTTPS for security
- **Backup Strategy**: Regular database backups

### Environment Setup
```bash
# Production environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/lotoryjung
export ADMIN_EMAIL=admin@example.com
```

## 🔮 Future Roadmap

### Phase 1 Enhancements (Completed ✅)
- ✅ Individual Number Limits Management System
- ✅ Bulk Order Form with 2-step Validation
- ✅ Database-driven Payout System
- ✅ Field Validation Logic
- ✅ External Calculation Support

### Phase 2 Enhancements (Planning)
- [ ] Real-time Notifications System
- [ ] Advanced Reporting & Analytics
- [ ] Mobile-responsive Design Improvements
- [ ] Multi-language Support
- [ ] API Rate Limiting

### System Improvements
- [ ] Database connection pooling
- [ ] Caching layer implementation (Redis)
- [ ] Background job processing (Celery)
- [ ] Microservices architecture
- [ ] Container deployment (Docker)

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 style guidelines
2. Write comprehensive tests
3. Update documentation
4. Use meaningful commit messages

### Code Structure
```
app/
├── models.py           # Database layer
├── services/
│   └── limit_service.py # Business logic
├── routes/
│   ├── auth.py         # Authentication
│   ├── user.py         # User routes
│   ├── admin.py        # Admin panel
│   └── api.py          # API endpoints
├── templates/          # Jinja2 templates
└── static/            # Frontend assets
```

### Contribution Process
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support & Troubleshooting

### Common Issues

#### CSRF Token Errors
```javascript
// Ensure AJAX requests include CSRF token
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", $('meta[name=csrf-token]').attr('content'));
        }
    }
});
```

#### Database Connection Issues
```bash
# Check database initialization
flask db current
flask db upgrade

# Reset database if needed
rm instance/app.db
flask db upgrade
```

#### Field Validation Problems
- Verify JavaScript validation functions
- Check field name attributes in HTML
- Ensure proper event listeners attachment

### Getting Help
- Check documentation thoroughly
- Review server logs: `tail -f logs/app.log`
- Test API endpoints with curl/Postman
- Verify database schema with DB browser

---

## 📊 System Status

**Current Version**: 2.1 (Complete Bulk Order System + External Calculation)  
**Last Updated**: September 2, 2025  
**Status**: Production Ready ✅ All Features Operational & Tested

### Feature Completeness
- ✅ Order Management System
- ✅ Admin Dashboard
- ✅ Blocked Numbers Management
- ✅ Group Limits Management  
- ✅ Individual Number Limits ⭐
- ✅ Bulk Order Form System (COMPLETED) ⭐
- ✅ Database-driven Payout System (COMPLETED) ⭐
- ✅ 2-Step Validation Process ⭐
- ✅ Field Restrictions Logic ⭐
- ✅ External Calculation Support (COMPLETED) ⭐
- ✅ Message Text Updates ("มียอดซื้อเกินโควต้า") ⭐
- ✅ Legacy Database Compatibility (COMPLETED) ⭐
- ✅ Complete Order Submission & Tracking (COMPLETED) ⭐

### Recent Updates (Version 2.1)
- ✅ **Bulk Order Form**: สมบูรณ์ - รองรับ 20 บรรทัด, 2-step validation
- ✅ **Database Integration**: บันทึกครบถ้วน - Orders, OrderItems, NumberTotals
- ✅ **External Calculation**: รองรับการคำนวณภายนอกผ่าน validation_factor
- ✅ **Legacy Compatibility**: รองรับ schema เก่าและใหม่พร้อมกัน
- ✅ **Field Mapping**: แก้ไขปัญหา compatibility ระหว่าง database fields
- ✅ **Order Tracking**: สร้าง Order Number อัตโนมัติและติดตามครบถ้วน

### Technical Specifications
- **Framework**: Flask 2.3+
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Bootstrap 5.3, jQuery, JavaScript ES6
- **Security**: CSRF Protection, Role-based Access, Rate Limiting
- **Architecture**: MVC with Service Layer Pattern + External Calculation Support

---

**🚀 เวอร์ชั่นใหม่: Complete Bulk Order System พร้อมใช้งานเต็มรูปแบบ!**  
**👨‍💻 พัฒนาโดย SafetyDady | 📅 September 2, 2025 | 🌟 Version 2.1**
- ✅ Order Management  
- ✅ Blocked Numbers Management
- ✅ Group Limits Management
- ✅ Individual Number Limits (COMPLETED)
- ✅ Bulk Order Form System (COMPLETED)
- ✅ External Calculation Architecture (COMPLETED)
- ✅ Individual Limits Management
- ✅ Admin Dashboard
- ✅ Security Implementation
- ✅ API Endpoints
- ✅ Documentation

**🎉 Ready for production use with comprehensive lottery management capabilities!**
