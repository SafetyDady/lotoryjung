# Project Structure

## Directory Layout
```
lotoryjung_app/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── blocked_numbers.py    # Database models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py             # Admin routes
│   │   └── main.py              # Main routes
│   └── forms/
│       ├── __init__.py
│       └── blocked_numbers.py    # WTForms
├── templates/
│   ├── base.html                # Base template
│   ├── admin/
│   │   ├── blocked_numbers.html     # List view
│   │   └── bulk_blocked_number_form.html  # Bulk add form
│   └── components/
├── static/
│   ├── css/
│   │   └── style.css            # Custom styles
│   └── js/
│       └── app.js               # JavaScript functions
├── docs/
│   ├── DESIGN.md                # System design
│   ├── STRUCTURE.md             # This file
│   ├── INSTALLATION.md          # Setup guide
│   └── PROGRESS.md              # Development log
├── migrations/                  # Database migrations
├── config.py                    # Configuration
├── app.py                       # Application entry point
└── requirements.txt             # Dependencies
```

## Key Files Description

### Core Application
- **`app.py`**: Flask application entry point และ configuration
- **`config.py`**: Environment และ database settings

### Models Layer
- **`app/models/blocked_numbers.py`**: SQLAlchemy model สำหรับ blocked numbers

### Routes Layer
- **`app/routes/admin.py`**: Admin panel routes, bulk operations, database management
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
