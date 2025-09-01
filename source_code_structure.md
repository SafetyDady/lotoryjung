# Source Code Structure - โครงสร้างโค้ด

## 1. โครงสร้างโฟลเดอร์หลัก (Main Directory Structure)

```
lottery_system/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .env                        # Environment variables
├── .gitignore                  # Git ignore file
│
├── src/                        # Source code directory
│   ├── __init__.py
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── order.py           # Order model
│   │   ├── order_item.py      # Order item model
│   │   ├── limit.py           # Limit model
│   │   ├── blocked_number.py  # Blocked number model
│   │   └── number_total.py    # Number total model
│   │
│   ├── routes/                 # Route handlers
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   ├── admin.py           # Admin routes
│   │   ├── user.py            # User routes
│   │   ├── api.py             # API routes
│   │   └── main.py            # Main routes
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication service
│   │   ├── order_service.py   # Order processing service
│   │   ├── limit_service.py   # Limit checking service
│   │   ├── pdf_service.py     # PDF generation service
│   │   └── export_service.py  # Data export service
│   │
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── decorators.py      # Custom decorators
│   │   ├── validators.py      # Input validation
│   │   ├── helpers.py         # Helper functions
│   │   └── constants.py       # Application constants
│   │
│   └── database/               # Database related
│       ├── __init__.py
│       ├── connection.py      # Database connection
│       ├── migrations.py      # Database migrations
│       └── seed_data.py       # Initial data seeding
│
├── static/                     # Static files
│   ├── css/                   # Stylesheets
│   │   ├── bootstrap.min.css
│   │   ├── main.css           # Custom styles
│   │   ├── admin.css          # Admin specific styles
│   │   └── mobile.css         # Mobile responsive styles
│   │
│   ├── js/                    # JavaScript files
│   │   ├── bootstrap.min.js
│   │   ├── jquery.min.js
│   │   ├── main.js            # Main JavaScript
│   │   ├── admin.js           # Admin JavaScript
│   │   ├── order.js           # Order form JavaScript
│   │   └── utils.js           # Utility functions
│   │
│   ├── images/                # Image files
│   │   ├── logo.png
│   │   └── icons/
│   │
│   └── receipts/              # Generated PDF receipts
│       └── {user_id}/         # User-specific folders
│           └── {order_id}.pdf
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── auth/                  # Authentication templates
│   │   ├── login.html
│   │   └── logout.html
│   │
│   ├── admin/                 # Admin templates
│   │   ├── dashboard.html
│   │   ├── user_management.html
│   │   ├── limit_settings.html
│   │   ├── blocked_numbers.html
│   │   └── export_data.html
│   │
│   ├── user/                  # User templates
│   │   ├── dashboard.html
│   │   ├── order_form.html
│   │   └── order_history.html
│   │
│   └── components/            # Reusable components
│       ├── navbar.html
│       ├── sidebar.html
│       ├── alerts.html
│       └── pagination.html
│
├── data/                      # Data directory
│   ├── lottery.db            # SQLite database
│   └── backups/              # Database backups
│       └── lottery_backup_YYYYMMDD.db
│
├── logs/                      # Log files
│   ├── app.log               # Application logs
│   ├── error.log             # Error logs
│   └── access.log            # Access logs
│
├── tests/                     # Test files
│   ├── __init__.py
│   ├── test_models.py        # Model tests
│   ├── test_routes.py        # Route tests
│   ├── test_services.py      # Service tests
│   └── test_utils.py         # Utility tests
│
└── docs/                      # Documentation
    ├── api_documentation.md
    ├── user_manual.md
    └── admin_manual.md
```

## 2. Core Application Files

### app.py (Main Application)
```python
from flask import Flask
from src.database.connection import init_db
from src.routes import register_routes
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    init_db(app)
    
    # Register routes
    register_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

### config.py (Configuration)
```python
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///data/lottery.db'
    UPLOAD_FOLDER = 'static/receipts'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # PDF Settings
    PDF_FONT_SIZE = 12
    PDF_PAGE_SIZE = 'A4'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
```

## 3. Database Models

### src/models/user.py
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')  # 'admin' or 'user'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
```

### src/models/order.py
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .user import Base

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    customer_name = Column(String(100))  # Optional customer name
    total_amount = Column(Integer, default=0)  # Total in cents
    status = Column(String(20), default='completed')
    pdf_path = Column(String(255))  # Path to generated PDF
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def generate_order_number(self):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ORD{timestamp}"
```

### src/models/order_item.py
```python
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from .user import Base

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    number = Column(String(10), nullable=False)  # The lottery number
    
    # Purchase amounts
    buy_2_top = Column(Integer, default=0)      # 2ตัวบน
    buy_2_bottom = Column(Integer, default=0)   # 2ตัวล่าง
    buy_3_top = Column(Integer, default=0)      # 3ตัวบน
    buy_tote = Column(Integer, default=0)       # โต๊ด
    
    # Payout rates
    payout_2_top = Column(Numeric(3,1), default=1.0)    # ราคาจ่าย 2ตัวบน
    payout_2_bottom = Column(Numeric(3,1), default=1.0) # ราคาจ่าย 2ตัวล่าง
    payout_3_top = Column(Numeric(3,1), default=1.0)    # ราคาจ่าย 3ตัวบน
    payout_tote = Column(Numeric(3,1), default=1.0)     # ราคาจ่าย โต๊ด
    
    # Relationships
    order = relationship("Order", back_populates="items")
    
    @property
    def total_amount(self):
        return self.buy_2_top + self.buy_2_bottom + self.buy_3_top + self.buy_tote
```

## 4. Service Layer

### src/services/order_service.py
```python
from src.models.order import Order
from src.models.order_item import OrderItem
from src.services.limit_service import LimitService
from src.services.pdf_service import PDFService

class OrderService:
    def __init__(self):
        self.limit_service = LimitService()
        self.pdf_service = PDFService()
    
    def check_prices(self, order_data):
        """Check prices against limits and blocked numbers"""
        results = []
        
        for item in order_data['items']:
            number = item['number']
            result = {
                'number': number,
                'buy_2_top': item.get('buy_2_top', 0),
                'buy_2_bottom': item.get('buy_2_bottom', 0),
                'buy_3_top': item.get('buy_3_top', 0),
                'buy_tote': item.get('buy_tote', 0),
                'payout_2_top': 1.0,
                'payout_2_bottom': 1.0,
                'payout_3_top': 1.0,
                'payout_tote': 1.0,
                'warnings': []
            }
            
            # Check blocked numbers
            if self.limit_service.is_blocked_number(number):
                result['payout_2_top'] = 0.5
                result['payout_2_bottom'] = 0.5
                result['payout_3_top'] = 0.5
                result['payout_tote'] = 0.5
                result['warnings'].append(f"เลข {number} เป็นเลขอั้น จ่ายครึ่ง")
            else:
                # Check limits
                limit_results = self.limit_service.check_limits(number, item)
                result.update(limit_results)
            
            results.append(result)
        
        return results
    
    def create_order(self, user_id, order_data, price_check_results):
        """Create new order with items"""
        order = Order(
            user_id=user_id,
            customer_name=order_data.get('customer_name'),
            order_number=Order().generate_order_number()
        )
        
        total_amount = 0
        for i, item_data in enumerate(order_data['items']):
            price_result = price_check_results[i]
            
            item = OrderItem(
                number=item_data['number'],
                buy_2_top=item_data.get('buy_2_top', 0),
                buy_2_bottom=item_data.get('buy_2_bottom', 0),
                buy_3_top=item_data.get('buy_3_top', 0),
                buy_tote=item_data.get('buy_tote', 0),
                payout_2_top=price_result['payout_2_top'],
                payout_2_bottom=price_result['payout_2_bottom'],
                payout_3_top=price_result['payout_3_top'],
                payout_tote=price_result['payout_tote']
            )
            
            order.items.append(item)
            total_amount += item.total_amount
        
        order.total_amount = total_amount
        
        # Generate PDF
        pdf_path = self.pdf_service.generate_receipt(order)
        order.pdf_path = pdf_path
        
        return order
```

## 5. Route Handlers

### src/routes/user.py
```python
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from src.services.order_service import OrderService
from src.utils.decorators import login_required, user_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    """User dashboard with order form and history"""
    return render_template('user/dashboard.html')

@user_bp.route('/check-prices', methods=['POST'])
@login_required
@user_required
def check_prices():
    """Check prices for order items"""
    order_service = OrderService()
    order_data = request.get_json()
    
    try:
        results = order_service.check_prices(order_data)
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@user_bp.route('/create-order', methods=['POST'])
@login_required
@user_required
def create_order():
    """Create new order"""
    order_service = OrderService()
    order_data = request.get_json()
    
    try:
        # Check prices first
        price_results = order_service.check_prices(order_data)
        
        # Create order
        order = order_service.create_order(
            session['user_id'], 
            order_data, 
            price_results
        )
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'pdf_url': url_for('static', filename=order.pdf_path)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

## 6. Frontend JavaScript

### static/js/order.js
```javascript
class OrderManager {
    constructor() {
        this.orderItems = [];
        this.priceChecked = false;
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.addInitialRow();
    }
    
    bindEvents() {
        $('#add-row-btn').on('click', () => this.addRow());
        $('#check-price-btn').on('click', () => this.checkPrices());
        $('#submit-order-btn').on('click', () => this.submitOrder());
        
        // Disable submit button initially
        $('#submit-order-btn').prop('disabled', true);
    }
    
    addRow() {
        if (this.orderItems.length >= 20) {
            alert('สามารถเพิ่มได้สูงสุด 20 บรรทัด');
            return;
        }
        
        const rowIndex = this.orderItems.length;
        const rowHtml = this.generateRowHtml(rowIndex);
        $('#order-table tbody').append(rowHtml);
        
        this.orderItems.push({
            number: '',
            buy_2_top: 0,
            buy_2_bottom: 0,
            buy_3_top: 0,
            buy_tote: 0
        });
        
        this.priceChecked = false;
        $('#submit-order-btn').prop('disabled', true);
    }
    
    generateRowHtml(index) {
        return `
            <tr data-index="${index}">
                <td>
                    <input type="text" class="form-control number-input" 
                           data-index="${index}" maxlength="3" pattern="[0-9]*">
                </td>
                <td>
                    <input type="number" class="form-control buy-input" 
                           data-index="${index}" data-type="buy_2_top" min="0">
                </td>
                <td>
                    <input type="number" class="form-control buy-input" 
                           data-index="${index}" data-type="buy_2_bottom" min="0">
                </td>
                <td>
                    <input type="number" class="form-control buy-input" 
                           data-index="${index}" data-type="buy_3_top" min="0">
                </td>
                <td>
                    <input type="number" class="form-control buy-input" 
                           data-index="${index}" data-type="buy_tote" min="0">
                </td>
                <td class="payout-2-top">-</td>
                <td class="payout-2-bottom">-</td>
                <td class="payout-3-top">-</td>
                <td class="payout-tote">-</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger remove-row-btn" 
                            data-index="${index}">ลบ</button>
                </td>
            </tr>
        `;
    }
    
    async checkPrices() {
        try {
            this.collectOrderData();
            
            const response = await fetch('/user/check-prices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_name: $('#customer-name').val(),
                    items: this.orderItems
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayPriceResults(result.results);
                this.priceChecked = true;
                $('#submit-order-btn').prop('disabled', false);
            } else {
                alert('เกิดข้อผิดพลาด: ' + result.error);
            }
        } catch (error) {
            alert('เกิดข้อผิดพลาดในการตรวจสอบราคา');
            console.error(error);
        }
    }
    
    displayPriceResults(results) {
        results.forEach((result, index) => {
            const row = $(`tr[data-index="${index}"]`);
            row.find('.payout-2-top').text(result.payout_2_top);
            row.find('.payout-2-bottom').text(result.payout_2_bottom);
            row.find('.payout-3-top').text(result.payout_3_top);
            row.find('.payout-tote').text(result.payout_tote);
            
            // Show warnings if any
            if (result.warnings.length > 0) {
                row.addClass('table-warning');
                row.attr('title', result.warnings.join(', '));
            }
        });
    }
    
    async submitOrder() {
        if (!this.priceChecked) {
            alert('กรุณาตรวจสอบราคาก่อนสั่งซื้อ');
            return;
        }
        
        try {
            const response = await fetch('/user/create-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_name: $('#customer-name').val(),
                    items: this.orderItems
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('สั่งซื้อสำเร็จ! เลขที่สั่งซื้อ: ' + result.order_number);
                
                // Download PDF
                window.open(result.pdf_url, '_blank');
                
                // Reset form
                this.resetForm();
            } else {
                alert('เกิดข้อผิดพลาด: ' + result.error);
            }
        } catch (error) {
            alert('เกิดข้อผิดพลาดในการสั่งซื้อ');
            console.error(error);
        }
    }
}

// Initialize when document is ready
$(document).ready(() => {
    new OrderManager();
});
```

## 7. CSS Styles

### static/css/main.css
```css
/* Main Styles */
:root {
    --primary-color: #1e3a8a;
    --secondary-color: #3b82f6;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    --light-bg: #f8fafc;
    --border-color: #e2e8f0;
}

body {
    font-family: 'Sarabun', sans-serif;
    background-color: var(--light-bg);
}

/* Header */
.navbar {
    background-color: var(--primary-color) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar-brand {
    font-weight: 600;
    color: white !important;
}

/* Cards */
.card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
}

.card-header {
    background-color: var(--primary-color);
    color: white;
    border-radius: 12px 12px 0 0 !important;
    font-weight: 600;
}

/* Buttons */
.btn-primary {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
    border-radius: 8px;
    font-weight: 500;
}

.btn-primary:hover {
    background-color: #1e40af;
    border-color: #1e40af;
}

.btn-success {
    background-color: var(--success-color);
    border-color: var(--success-color);
    border-radius: 8px;
}

.btn-warning {
    background-color: var(--warning-color);
    border-color: var(--warning-color);
    border-radius: 8px;
    color: white;
}

/* Tables */
.table {
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
}

.table thead th {
    background-color: var(--primary-color);
    color: white;
    border: none;
    font-weight: 600;
    text-align: center;
}

.table tbody td {
    vertical-align: middle;
    text-align: center;
    border-color: var(--border-color);
}

/* Form Controls */
.form-control {
    border-radius: 8px;
    border: 1px solid var(--border-color);
    padding: 0.75rem;
}

.form-control:focus {
    border-color: var(--secondary-color);
    box-shadow: 0 0 0 0.2rem rgba(59, 130, 246, 0.25);
}

/* Order Table Specific */
.order-table {
    font-size: 0.9rem;
}

.order-table input[type="text"],
.order-table input[type="number"] {
    padding: 0.5rem;
    font-size: 0.9rem;
    text-align: center;
}

.number-input {
    max-width: 80px;
}

.buy-input {
    max-width: 100px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .order-table {
        font-size: 0.8rem;
    }
    
    .order-table input {
        padding: 0.4rem;
        font-size: 0.8rem;
    }
    
    .btn {
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }
    
    .card {
        margin-bottom: 1rem;
    }
}

@media (max-width: 576px) {
    .table-responsive {
        font-size: 0.75rem;
    }
    
    .btn-sm {
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
    }
}

/* Loading States */
.loading {
    opacity: 0.6;
    pointer-events: none;
}

.spinner-border-sm {
    width: 1rem;
    height: 1rem;
}

/* Alerts */
.alert {
    border-radius: 8px;
    border: none;
}

.alert-warning {
    background-color: #fef3c7;
    color: #92400e;
}

.alert-success {
    background-color: #d1fae5;
    color: #065f46;
}

.alert-danger {
    background-color: #fee2e2;
    color: #991b1b;
}
```

## 8. Testing Structure

### tests/test_order_service.py
```python
import unittest
from unittest.mock import Mock, patch
from src.services.order_service import OrderService

class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.order_service = OrderService()
    
    def test_check_prices_normal_number(self):
        """Test price checking for normal numbers"""
        order_data = {
            'items': [
                {
                    'number': '123',
                    'buy_2_top': 100,
                    'buy_2_bottom': 50,
                    'buy_3_top': 200,
                    'buy_tote': 75
                }
            ]
        }
        
        with patch.object(self.order_service.limit_service, 'is_blocked_number', return_value=False):
            with patch.object(self.order_service.limit_service, 'check_limits', return_value={
                'payout_2_top': 1.0,
                'payout_2_bottom': 1.0,
                'payout_3_top': 1.0,
                'payout_tote': 1.0,
                'warnings': []
            }):
                results = self.order_service.check_prices(order_data)
                
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]['number'], '123')
                self.assertEqual(results[0]['payout_2_top'], 1.0)
    
    def test_check_prices_blocked_number(self):
        """Test price checking for blocked numbers"""
        order_data = {
            'items': [
                {
                    'number': '999',
                    'buy_2_top': 100,
                    'buy_2_bottom': 50
                }
            ]
        }
        
        with patch.object(self.order_service.limit_service, 'is_blocked_number', return_value=True):
            results = self.order_service.check_prices(order_data)
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['payout_2_top'], 0.5)
            self.assertEqual(results[0]['payout_2_bottom'], 0.5)
            self.assertIn('เลขอั้น', results[0]['warnings'][0])

if __name__ == '__main__':
    unittest.main()
```

## 9. Deployment Files

### requirements.txt
```
Flask==2.3.3
SQLAlchemy==2.0.21
Flask-SQLAlchemy==3.0.5
Werkzeug==2.3.7
bcrypt==4.0.1
reportlab==4.0.4
openpyxl==3.1.2
python-dotenv==1.0.0
gunicorn==21.2.0
```

### .env (Environment Variables)
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///data/lottery.db
UPLOAD_FOLDER=static/receipts
MAX_CONTENT_LENGTH=16777216
```

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Environment
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Uploads
static/receipts/
data/backups/

# Testing
.coverage
htmlcov/
.pytest_cache/
```

## 10. สรุป

โครงสร้างโค้ดนี้ออกแบบมาเพื่อให้:

1. **แยกส่วนชัดเจน**: Models, Services, Routes, Utils
2. **ง่ายต่อการบำรุงรักษา**: แต่ละไฟล์มีหน้าที่เฉพาะ
3. **ขยายได้**: สามารถเพิ่มฟีเจอร์ใหม่ได้ง่าย
4. **ทดสอบได้**: แยก Business Logic ออกจาก Route Handlers
5. **ปลอดภัย**: มีการจัดการ Authentication และ Validation
6. **Mobile Responsive**: CSS และ JavaScript รองรับทุกอุปกรณ์

โครงสร้างนี้เหมาะสำหรับการพัฒนาระบบขนาดเล็กถึงกลาง และสามารถขยายเป็นระบบใหญ่ได้ในอนาคต

