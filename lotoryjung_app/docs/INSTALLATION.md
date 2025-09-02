# Installation Guide

## Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for cloning repository)
- SQLite3 (included with Python)

## Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/SafetyDady/lotoryjung.git
cd lotoryjung/lotoryjung_app
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv env
source env/bin/activate  # Linux/Mac
# หรือ
env\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# Create database structure
python3 init_db.py

# Set up default limits
python3 init_limits.py
```

### 5. Start Server
```bash
python3 run_server.py
```

Application will be available at: **http://127.0.0.1:8080**

### 6. Default Login Credentials
- **Admin**: admin / admin123
- **Test User**: testuser / test123

## Detailed Installation

### Environment Configuration
Create `.env` file in project root:
```bash
# Application Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration  
SQLALCHEMY_DATABASE_URI=sqlite:///lotoryjung.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Security Configuration
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600

# Server Configuration
HOST=127.0.0.1
PORT=8080

# Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=static/receipts
```

### Database Initialization Details

#### Manual Database Setup
```bash
# Enter Python shell
python3 -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database created successfully')
"
```

#### Initialize Default Data
```bash
# Create admin user and default limits
python3 -c "
from app import create_app, db
from app.models import User, Rule
from app.services.limit_service import LimitService
from werkzeug.security import generate_password_hash
from decimal import Decimal

app = create_app()
with app.app_context():
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    
    # Create default limits
    limits = [
        ('2_top', Decimal('700')),
        ('2_bottom', Decimal('700')),
        ('3_top', Decimal('300')),
        ('tote', Decimal('700'))
    ]
    
    for field, limit in limits:
        LimitService.set_default_group_limit(field, limit)
    
    db.session.commit()
    print('Default data created successfully')
"
```

### Production Setup

#### Environment Variables for Production
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex())')
export SQLALCHEMY_DATABASE_URI=sqlite:///production.db
```

#### Using Production WSGI Server
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8080 --workers 4 app:app
```

#### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python3 init_db.py
RUN python3 init_limits.py

EXPOSE 8080

CMD ["python3", "run_server.py"]
```

```bash
# Build and run Docker container
docker build -t lotoryjung .
docker run -p 8080:8080 lotoryjung
```

## Development Setup

### Required Python Packages
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-WTF==1.1.1
WTForms==3.0.1
Flask-Migrate==4.0.5
Flask-Limiter==3.5.0
```

### Environment Variables (.env)
```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///lottery.db

# Security
WTF_CSRF_ENABLED=True
```

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

### Using Docker (Optional)
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5002
CMD ["python3", "app.py"]
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# ลบ database เก่าแล้วสร้างใหม่
rm instance/lottery.db
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

#### 2. Port Already in Use
```bash
# เปลี่ยน port ใน app.py
app.run(host='0.0.0.0', port=5003, debug=True)
```

#### 3. Permission Issues
```bash
# ตรวจสอบ permissions
chmod +x app.py
sudo chown -R $USER:$USER .
```

## Development Commands

### Database Operations
```bash
# สร้าง migration
flask db migrate -m "description"

# Apply migration
flask db upgrade

# ล้างข้อมูล
python3 -c "from app.routes.admin import clear_all_blocked_numbers; clear_all_blocked_numbers()"
```

### Testing
```bash
# Run tests (if available)
python3 -m pytest

# Check code style
flake8 app/
```

## System Requirements

### Minimum Requirements
- RAM: 512MB
- Storage: 1GB
- CPU: 1 core

### Recommended
- RAM: 2GB+
- Storage: 5GB+
- CPU: 2+ cores

---
*Installation Guide v1.0 - September 2, 2025*
