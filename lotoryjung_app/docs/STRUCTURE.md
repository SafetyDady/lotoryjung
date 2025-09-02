# Project Structure

## Directory Layout
```
lotoryjung_app/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User and authentication models
│   │   ├── order.py             # Order and OrderItem models
│   │   ├── blocked_numbers.py   # BlockedNumber model
│   │   └── rule.py              # Rule model (limits management)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py             # Admin panel routes
│   │   ├── auth.py              # Authentication routes
│   │   └── main.py              # Main public routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── limit_service.py     # Business logic for limits management
│   ├── utils/
│   │   ├── __init__.py
│   │   └── number_utils.py      # Number utilities and permutations
│   └── forms/
│       ├── __init__.py
│       └── blocked_numbers.py   # WTForms definitions
├── templates/
│   ├── base.html               # Base template
│   ├── admin/
│   │   ├── base.html           # Admin base template with navigation
│   │   ├── dashboard.html      # Admin dashboard
│   │   ├── blocked_numbers.html # Blocked numbers management
│   │   ├── bulk_blocked_number_form.html # Bulk operations form
│   │   ├── group_limits.html   # Default group limits management
│   │   ├── individual_limits.html # Individual number limits management
│   │   └── edit_group_limits.html # Group limits editing form
│   ├── auth/
│   │   └── login.html          # Login page
│   └── components/
├── static/
│   ├── css/
│   │   └── style.css           # Custom styles
│   ├── js/
│   │   └── app.js              # JavaScript functions
│   └── receipts/               # Upload directory for receipts
├── docs/
│   ├── DESIGN.md               # Original system design
│   ├── GROUP_LIMITS_DESIGN.md  # Group limits design document
│   ├── INDIVIDUAL_LIMITS_DESIGN.md # Individual limits design document
│   ├── STRUCTURE.md            # This file
│   ├── INSTALLATION.md         # Setup guide
│   └── PROGRESS.md             # Development log
├── instance/                   # Flask instance folder
├── migrations/                 # Database migrations
├── config.py                   # Configuration settings
├── app.py                      # Application factory
├── run_server.py               # Server startup script
├── init_db.py                  # Database initialization script
├── init_limits.py              # Default limits initialization
└── requirements.txt            # Dependencies
```

## Key Files Description

### Core Application
- **`app.py`**: Flask application factory with extensions initialization
- **`run_server.py`**: Server startup script with configuration
- **`config.py`**: Environment และ database settings

### Models Layer (Database)
- **`app/models/user.py`**: User authentication and profile models
- **`app/models/order.py`**: Order and OrderItem models for lottery transactions
- **`app/models/blocked_numbers.py`**: BlockedNumber model for number restrictions
- **`app/models/rule.py`**: Rule model for both group and individual limits

### Services Layer (Business Logic)
- **`app/services/limit_service.py`**: Core business logic class containing:
  - Group limits management
  - Individual limits management  
  - Order validation with priority logic
  - Usage calculation and reporting

### Routes Layer (Controllers)
- **`app/routes/admin.py`**: Admin panel routes including:
  - Dashboard with statistics
  - Blocked numbers CRUD operations
  - Group limits management
  - Individual limits management with APIs
- **`app/routes/auth.py`**: Authentication routes (login/logout)
- **`app/routes/main.py`**: Public routes and user interfaces

### Utilities Layer
- **`app/utils/number_utils.py`**: Number processing utilities:
  - Permutation generation algorithms
  - Number normalization functions
  - Validation helpers

### Forms Layer
- **`app/forms/blocked_numbers.py`**: WTForms definitions for form validation

### Templates Layer
- **`templates/admin/base.html`**: Admin navigation template with sidebar
- **`templates/admin/individual_limits.html`**: Complete individual limits interface
- **`templates/admin/group_limits.html`**: Group limits dashboard
- **`templates/admin/dashboard.html`**: Main admin dashboard

### Static Assets
- **`static/css/style.css`**: Custom CSS styles
- **`static/js/app.js`**: JavaScript functions for dynamic interfaces

## Database Structure

### Extended Schema
```sql
-- Users table for authentication
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table for lottery transactions
CREATE TABLE `order` (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Order items for individual number bets
CREATE TABLE order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    field VARCHAR(20) NOT NULL,
    number_norm VARCHAR(10) NOT NULL,
    buy_amount DECIMAL(15,2) NOT NULL,
    payout_rate DECIMAL(5,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES `order` (id)
);

-- Blocked numbers table
CREATE TABLE blocked_number (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field VARCHAR(20) NOT NULL,
    number_norm VARCHAR(10) NOT NULL,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unified rules table for both group and individual limits
CREATE TABLE rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type VARCHAR(50) NOT NULL,        -- 'default_limit' or 'number_limit'
    field VARCHAR(20),                     -- '2_top', '2_bottom', '3_top', 'tote'
    number_norm VARCHAR(10),               -- NULL for group limits, specific number for individual
    limit_amount DECIMAL(15,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Number totals for usage tracking
CREATE TABLE number_total (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field VARCHAR(20) NOT NULL,
    number_norm VARCHAR(10) NOT NULL,
    total_amount DECIMAL(15,2) DEFAULT 0,
    batch_id VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs for tracking changes
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);
```

### Database Indexes
```sql
-- Performance indexes
CREATE INDEX idx_blocked_numbers_field_number ON blocked_number(field, number_norm);
CREATE INDEX idx_rule_type_field ON rule(rule_type, field);
CREATE INDEX idx_rule_number_limit ON rule(rule_type, field, number_norm) WHERE rule_type = 'number_limit';
CREATE INDEX idx_number_total_batch_field ON number_total(batch_id, field, number_norm);
CREATE INDEX idx_order_item_field_number ON order_item(field, number_norm);
```

## Data Flow Architecture

### Order Validation Flow
```
1. User Order Submission
   ↓
2. LimitService.validate_order_item()
   ↓
3. Priority Check:
   ├── Check BlockedNumber table
   ├── Check Individual Limits (Rule table with rule_type='number_limit')
   └── Fallback to Group Limits (Rule table with rule_type='default_limit')
   ↓
4. Calculate Payout Rate:
   ├── 1.0x for normal orders
   └── 0.5x for blocked/exceeded orders
   ↓
5. Return Validation Result
```

### Individual Limits Management Flow
```
1. Admin Access Individual Limits Page
   ↓
2. LimitService.get_individual_limits_list()
   ↓
3. Display Current Individual Limits + Usage
   ↓
4. CRUD Operations:
   ├── Create: POST /admin/api/set_individual_limit
   ├── Update: POST /admin/api/set_individual_limit (upsert)
   └── Delete: POST /admin/api/delete_individual_limit
   ↓
5. Real-time UI Updates via AJAX
```

### Permutation Generation Logic
```python
# Enhanced permutation system
def generate_blocked_numbers_for_field(number, field):
    if field in ['2_top', '2_bottom']:
        return generate_2digit_permutations(number, field)
    elif field == '3_top':
        return generate_3digit_permutations(number)
    elif field == 'tote':
        return generate_tote_permutations(number)

# Example: input "12" for 2_top generates:
# [('01', '2_top'), ('10', '2_top'), ('12', '2_top'), ('21', '2_top')]
```

## Security Architecture

### Authentication & Authorization
- **Flask-Login**: Session management
- **Password Hashing**: Werkzeug security utilities
- **Admin Decorator**: `@admin_required` for protected routes
- **CSRF Protection**: WTF-CSRF for form security

### API Security
```python
# All admin APIs protected with:
@login_required          # User must be authenticated
@admin_required         # User must have admin role
# Plus CSRF token validation in AJAX requests
```

### Input Validation
- **Server-side**: WTForms validation
- **Client-side**: JavaScript validation
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Protection**: Jinja2 auto-escaping

## Service Layer Design

### LimitService Class Architecture
```python
class LimitService:
    # Group Limits Management
    @staticmethod
    def get_default_group_limits() -> Dict[str, Decimal]
    def set_default_group_limit(field: str, limit: Decimal) -> bool
    
    # Individual Limits Management  
    @staticmethod
    def get_individual_limit(field: str, number_norm: str) -> Optional[Decimal]
    def set_individual_limit(field: str, number_norm: str, limit: Decimal) -> bool
    def get_individual_limits_list(field: str = None) -> List[Dict]
    
    # Validation & Usage
    @staticmethod
    def validate_order_item(field: str, number_norm: str, buy_amount: Decimal) -> Dict
    def get_current_usage(field: str, number_norm: str, batch_id: str) -> Decimal
    
    # Dashboard & Reporting
    @staticmethod
    def get_limits_dashboard_data(batch_id: str = None) -> Dict
```

## Future Architecture Considerations

### Scalability
- Database connection pooling
- Caching layer for frequent limit lookups
- API rate limiting implementation
- Background job processing for heavy operations

### Extensibility
- Plugin architecture for custom validation rules
- API versioning for mobile app integration
- Microservices separation for high-load scenarios
- Event-driven architecture for real-time updates

---
*Structure Document v2.0 - September 2, 2025*
*Updated with Individual Limits Management System*
- **`app/routes/main.py`**: Public routes (future features)

### Forms Layer
- **`app/forms/blocked_numbers.py`**: WTForms สำหรับ form validation

### Templates
- **`templates/base.html`**: Base template with Bootstrap 5
- **`templates/admin/blocked_numbers.html`**: List view with pagination และ search
- **`templates/admin/bulk_blocked_number_form.html`**: Simplified bulk add form

### Static Assets
- **`static/css/style.css`**: Custom CSS styles
- **`static/js/app.js`**: JavaScript functions สำหรับ dynamic forms

## Database Structure
```sql
-- Main table for blocked numbers
CREATE TABLE blocked_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(10) NOT NULL,
    field VARCHAR(20) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_blocked_numbers_field ON blocked_numbers(field);
CREATE INDEX idx_blocked_numbers_number ON blocked_numbers(number);
```

## Data Flow

### Bulk Add Process
1. User inputs numbers in simplified form
2. JavaScript auto-detects number type by length
3. Frontend validation before submission
4. Backend validation และ permutation generation
5. Database clearing และ bulk insert
6. Success redirect with flash message

### Permutation Generation Logic
```python
# 2-digit example: input "12"
def generate_2digit_permutations(number):
    padded = number.zfill(2)  # "12"
    reversed_num = padded[::-1]  # "21"
    return [
        (padded, '2_top'),      # 12
        (reversed_num, '2_top'), # 21
        (padded, '2_bottom'),    # 12
        (reversed_num, '2_bottom') # 21
    ]

# 3-digit example: input "157"
def generate_3digit_permutations(number):
    # Generate all 6 permutations for 3_top
    # Plus 1 tote record
    # Total: 7 records
```

## Security Measures
- CSRF protection ใน forms
- Input sanitization
- SQL injection prevention
- Rate limiting
- Admin authentication (future implementation)

---
*Structure Document v1.0 - September 2, 2025*
