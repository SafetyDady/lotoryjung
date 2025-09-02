# Installation Guide

## Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for cloning repository)

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/SafetyDady/lotoryjung.git
cd lotoryjung
```

### 2. Create Virtual Environment
```bash
python3 -m venv env
source env/bin/activate  # Linux/Mac
# หรือ
env\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
cd lotoryjung_app
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env
```

### 5. Database Setup
```bash
# Initialize database
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 6. Run Application
```bash
python3 app.py
```

Application จะรันที่: http://localhost:5002

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
