# 🎰 Lotoryjung - Advanced Lottery Management System

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

### 🛡️ Security Features
- **CSRF Protection** - ป้องกันการโจมตี Cross-Site Request Forgery
- **Admin Authorization** - ระบบสิทธิ์ผู้ดูแลระบบ
- **Input Validation** - ตรวจสอบข้อมูลนำเข้าทุกขั้นตอน
- **SQL Injection Prevention** - ป้องกันการโจมตี SQL Injection

## 🏗️ System Architecture

### 📋 Validation Priority Logic
```
Priority 1: Blocked Numbers Check
    ├── If blocked → 0.5x payout rate
    └── If not blocked → Continue

Priority 2: Individual Limits Check  
    ├── If individual limit exists → Use individual limit
    └── If no individual limit → Continue

Priority 3: Default Group Limits
    └── Apply default group limit for field type
```

### 🎲 Field Types Supported
- **2_top** (2 ตัวบน) - 2-digit top lottery
- **2_bottom** (2 ตัวล่าง) - 2-digit bottom lottery  
- **3_top** (3 ตัวบน) - 3-digit top lottery
- **tote** (โต๊ด) - Tote betting

### 💾 Database Schema
```sql
-- Core tables
user                 -- User authentication
order               -- Lottery orders
order_item          -- Individual lottery bets
blocked_number      -- Blocked lottery numbers
rule                -- Both group and individual limits
number_total        -- Usage tracking
audit_log          -- Change tracking
```

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
python init_db.py

# Initialize default limits
python init_limits.py

# Start server
python run_server.py
```

### Default Access
- **URL**: http://127.0.0.1:8080
- **Admin Login**: admin / admin123
- **Test User**: testuser / test123

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

### Adding Individual Limit
```python
from app.services.limit_service import LimitService

# Set limit of 500 for number "12" in 2_top category
success = LimitService.set_individual_limit("2_top", "12", 500)
```

### Validating Order
```python
# Validate order with priority logic
result = LimitService.validate_order_item("2_top", "12", 300)
print(f"Payout rate: {result['payout_rate']}x")
print(f"Status: {result['reason']}")
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

### System Improvements
- [ ] Database connection pooling
- [ ] Caching layer implementation
- [ ] Background job processing
- [ ] Microservices architecture
- [ ] Container deployment (Docker)

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 style guidelines
2. Write comprehensive tests
3. Update documentation
4. Use meaningful commit messages

### Code Structure
- **Models**: Database layer (`app/models/`)
- **Services**: Business logic (`app/services/`)
- **Routes**: Controller layer (`app/routes/`)
- **Templates**: View layer (`templates/`)
- **Static**: Frontend assets (`static/`)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support & Troubleshooting

### Common Issues
- **CSRF Token Errors**: Ensure AJAX requests include CSRF token
- **Template Rendering**: Check Jinja2 syntax and function usage
- **Database Errors**: Verify database initialization and migrations
- **Permission Issues**: Confirm admin user authentication

### Getting Help
- Check documentation in `/docs` folder
- Review server logs for detailed error messages
- Test API endpoints individually
- Verify database schema integrity

---

## 📊 System Status

**Current Version**: 2.0  
**Last Updated**: September 2, 2025  
**Status**: Production Ready with Individual Limits ✅

### Feature Completeness
- ✅ User Authentication System
- ✅ Order Management  
- ✅ Blocked Numbers Management
- ✅ Group Limits Management
- ✅ Individual Limits Management
- ✅ Admin Dashboard
- ✅ Security Implementation
- ✅ API Endpoints
- ✅ Documentation

**🎉 Ready for production use with comprehensive lottery management capabilities!**
