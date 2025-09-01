# Database Structure - โครงสร้างฐานข้อมูล

## 1. ภาพรวมฐานข้อมูล (Database Overview)

### เทคโนโลยี
- **Database**: SQLite 3
- **ORM**: SQLAlchemy
- **ไฟล์**: `data/lottery.db`

### ข้อดีของ SQLite
- ไม่ต้องติดตั้ง Database Server
- ไฟล์เดียวจบ ง่ายต่อการ Backup
- รองรับ ACID Transactions
- เหมาะสำหรับระบบขนาดเล็กถึงกลาง

## 2. โครงสร้างตาราง (Table Structure)

### 2.1 ตาราง users (ข้อมูลผู้ใช้)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
```

**คำอธิบายฟิลด์:**
- `id`: Primary Key อัตโนมัติ
- `name`: ชื่อจริงของผู้ใช้
- `username`: ชื่อผู้ใช้สำหรับ Login (ไม่ซ้ำ)
- `password_hash`: รหัสผ่านที่เข้ารหัสด้วย bcrypt
- `role`: บทบาท ('admin' หรือ 'user')
- `is_active`: สถานะการใช้งาน (1=ใช้งาน, 0=ปิดใช้งาน)
- `created_at`: วันที่สร้าง
- `updated_at`: วันที่แก้ไขล่าสุด

### 2.2 ตาราง orders (รายการสั่งซื้อ)

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    customer_name VARCHAR(100),
    lottery_period DATE NOT NULL,           -- งวดวันที่ (วันที่หวยออก)
    total_amount INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'completed',
    pdf_path VARCHAR(255),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_lottery_period ON orders(lottery_period);
```

**คำอธิบายฟิลด์:**
- `id`: Primary Key อัตโนมัติ
- `order_number`: เลขที่สั่งซื้อ (รูปแบบ: ORD20240901143025)
- `user_id`: Foreign Key อ้างอิงถึง users.id
- `customer_name`: ชื่อลูกค้า (ไม่บังคับ)
- `lottery_period`: งวดวันที่ (วันที่หวยออก) - คำนวณจากวันที่สั่งซื้อ
- `total_amount`: ยอดรวมเป็นสตางค์ (เก็บเป็น Integer เพื่อความแม่นยำ)
- `status`: สถานะ ('completed', 'cancelled', 'pending')
- `pdf_path`: Path ของไฟล์ PDF ใบสั่งซื้อ
- `notes`: หมายเหตุเพิ่มเติม
- `created_at`: วันที่สร้าง
- `updated_at`: วันที่แก้ไขล่าสุด

### 2.3 ตาราง order_items (รายละเอียดแต่ละเลข)

```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    number VARCHAR(10) NOT NULL,
    buy_2_top INTEGER DEFAULT 0,
    buy_2_bottom INTEGER DEFAULT 0,
    buy_3_top INTEGER DEFAULT 0,
    buy_tote INTEGER DEFAULT 0,
    payout_2_top DECIMAL(3,1) DEFAULT 1.0,
    payout_2_bottom DECIMAL(3,1) DEFAULT 1.0,
    payout_3_top DECIMAL(3,1) DEFAULT 1.0,
    payout_tote DECIMAL(3,1) DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_number ON order_items(number);
CREATE INDEX idx_order_items_created_at ON order_items(created_at);
```

**คำอธิบายฟิลด์:**
- `id`: Primary Key อัตโนมัติ
- `order_id`: Foreign Key อ้างอิงถึง orders.id
- `number`: หมายเลขที่เดิมพัน (2-3 หลัก)
- `buy_2_top`: จำนวนเงินซื้อ 2 ตัวบน (สตางค์)
- `buy_2_bottom`: จำนวนเงินซื้อ 2 ตัวล่าง (สตางค์)
- `buy_3_top`: จำนวนเงินซื้อ 3 ตัวบน (สตางค์)
- `buy_tote`: จำนวนเงินซื้อโต๊ด (สตางค์)
- `payout_2_top`: ราคาจ่าย 2 ตัวบน (1.0 = เต็ม, 0.5 = ครึ่ง)
- `payout_2_bottom`: ราคาจ่าย 2 ตัวล่าง
- `payout_3_top`: ราคาจ่าย 3 ตัวบน
- `payout_tote`: ราคาจ่ายโต๊ด
- `created_at`: วันที่สร้าง

### 2.4 ตาราง limits (การกำหนด Limit)

```sql
CREATE TABLE limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(20) NOT NULL UNIQUE,
    limit_amount INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_limits_category ON limits(category);
CREATE INDEX idx_limits_active ON limits(is_active);
```

**คำอธิบายฟิลด์:**
- `id`: Primary Key อัตโนมัติ
- `category`: ประเภท ('2_top', '2_bottom', '3_top', 'tote')
- `limit_amount`: จำนวน Limit สูงสุด (สตางค์)
- `is_active`: สถานะการใช้งาน
- `created_at`: วันที่สร้าง
- `updated_at`: วันที่แก้ไขล่าสุด

**ข้อมูลเริ่มต้น:**
```sql
INSERT INTO limits (category, limit_amount) VALUES
('2_top', 50000),      -- 500 บาท
('2_bottom', 50000),   -- 500 บาท
('3_top', 100000),     -- 1,000 บาท
('tote', 75000);       -- 750 บาท
```

### 2.5 ตาราง blocked_numbers (เลขอั้น)

```sql
CREATE TABLE blocked_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(10) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_blocked_numbers_number ON blocked_numbers(number);
CREATE INDEX idx_blocked_numbers_active ON blocked_numbers(is_active);
```

**คำอธิบายฟิลด์:**
- `id`: Primary Key อัตโนมัติ
- `number`: หมายเลขที่ถูกอั้น
- `is_active`: สถานะการใช้งาน
- `created_at`: วันที่สร้าง
- `updated_at`: วันที่แก้ไขล่าสุด

### 2.6 ตาราง number_totals (ยอดรวมแต่ละเลข)

```sql
CREATE TABLE number_totals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    total_2_top INTEGER DEFAULT 0,
    total_2_bottom INTEGER DEFAULT 0,
    total_3_top INTEGER DEFAULT 0,
    total_tote INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number, date)
);

-- Indexes
CREATE INDEX idx_number_totals_number ON number_totals(number);
CREATE INDEX idx_number_totals_date ON number_totals(date);
CREATE INDEX idx_number_totals_number_date ON number_totals(number, date);
```

**คำอธิบายฟิลด์:**
- `id`: Primary Key อัตโนมัติ
- `number`: หมายเลข
- `date`: วันที่ (สำหรับแยกยอดรายวัน)
- `total_2_top`: ยอดรวม 2 ตัวบน (สตางค์)
- `total_2_bottom`: ยอดรวม 2 ตัวล่าง (สตางค์)
- `total_3_top`: ยอดรวม 3 ตัวบน (สตางค์)
- `total_tote`: ยอดรวมโต๊ด (สตางค์)
- `updated_at`: วันที่แก้ไขล่าสุด

## 3. Relationships (ความสัมพันธ์)

### 3.1 One-to-Many Relationships

```
users (1) ←→ (N) orders
orders (1) ←→ (N) order_items
```

### 3.2 ER Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    users    │ 1   N │     orders      │ 1   N │  order_items    │
├─────────────┤←──────├─────────────────┤←──────├─────────────────┤
│ id (PK)     │       │ id (PK)         │       │ id (PK)         │
│ name        │       │ order_number    │       │ order_id(FK)    │
│ username    │       │ user_id(FK)     │       │ number          │
│ password_hash│       │ customer_name   │       │ buy_2_top       │
│ role        │       │ lottery_period  │       │ buy_2_bottom    │
│ is_active   │       │ total_amount    │       │ buy_3_top       │
│ created_at  │       │ status          │       │ buy_tote        │
│ updated_at  │       │ pdf_path        │       │ payout_2_top    │
└─────────────┘       │ notes           │       │ payout_2_bottom │
                      │ created_at      │       │ payout_3_top    │
                      │ updated_at      │       │ payout_tote     │
                      └─────────────────┘       │ created_at      │
                                                └─────────────────┘

┌─────────────┐       ┌─────────────┐
│   limits    │       │blocked_numbers│
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ category    │       │ number      │
│ limit_amount│       │ is_active   │
│ is_active   │       │ created_at  │
│ created_at  │       │ updated_at  │
│ updated_at  │       └─────────────┘
└─────────────┘

┌─────────────┐
│number_totals│
├─────────────┤
│ id (PK)     │
│ number      │
│ date        │
│ total_2_top │
│ total_2_bottom│
│ total_3_top │
│ total_tote  │
│ updated_at  │
└─────────────┘
```

## 4. Triggers และ Stored Procedures

### 4.1 Trigger สำหรับ updated_at

```sql
-- Trigger สำหรับ users
CREATE TRIGGER update_users_updated_at 
    AFTER UPDATE ON users
    FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger สำหรับ orders
CREATE TRIGGER update_orders_updated_at 
    AFTER UPDATE ON orders
    FOR EACH ROW
BEGIN
    UPDATE orders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger สำหรับ limits
CREATE TRIGGER update_limits_updated_at 
    AFTER UPDATE ON limits
    FOR EACH ROW
BEGIN
    UPDATE limits SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger สำหรับ blocked_numbers
CREATE TRIGGER update_blocked_numbers_updated_at 
    AFTER UPDATE ON blocked_numbers
    FOR EACH ROW
BEGIN
    UPDATE blocked_numbers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### 4.2 Trigger สำหรับอัพเดท number_totals

```sql
CREATE TRIGGER update_number_totals_after_insert
    AFTER INSERT ON order_items
    FOR EACH ROW
BEGIN
    INSERT OR REPLACE INTO number_totals (
        number, date, total_2_top, total_2_bottom, total_3_top, total_tote, updated_at
    )
    VALUES (
        NEW.number,
        DATE('now'),
        COALESCE((SELECT total_2_top FROM number_totals 
                  WHERE number = NEW.number AND date = DATE('now')), 0) + NEW.buy_2_top,
        COALESCE((SELECT total_2_bottom FROM number_totals 
                  WHERE number = NEW.number AND date = DATE('now')), 0) + NEW.buy_2_bottom,
        COALESCE((SELECT total_3_top FROM number_totals 
                  WHERE number = NEW.number AND date = DATE('now')), 0) + NEW.buy_3_top,
        COALESCE((SELECT total_tote FROM number_totals 
                  WHERE number = NEW.number AND date = DATE('now')), 0) + NEW.buy_tote,
        CURRENT_TIMESTAMP
    );
END;
```

## 5. Views (มุมมองข้อมูล)

### 5.1 View สำหรับ Dashboard Admin

```sql
CREATE VIEW admin_dashboard_view AS
SELECT 
    DATE(o.created_at) as order_date,
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT o.user_id) as active_users,
    SUM(o.total_amount) as total_revenue,
    COUNT(oi.id) as total_items
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status = 'completed'
GROUP BY DATE(o.created_at)
ORDER BY order_date DESC;
```

### 5.2 View สำหรับยอดรวมแต่ละเลข

```sql
CREATE VIEW number_summary_view AS
SELECT 
    oi.number,
    SUM(oi.buy_2_top) as total_2_top,
    SUM(oi.buy_2_bottom) as total_2_bottom,
    SUM(oi.buy_3_top) as total_3_top,
    SUM(oi.buy_tote) as total_tote,
    COUNT(*) as order_count,
    MAX(o.created_at) as last_order_date
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'completed'
  AND DATE(o.created_at) = DATE('now')
GROUP BY oi.number
ORDER BY (SUM(oi.buy_2_top) + SUM(oi.buy_2_bottom) + 
          SUM(oi.buy_3_top) + SUM(oi.buy_tote)) DESC;
```

### 5.3 View สำหรับรายงาน User

```sql
CREATE VIEW user_order_summary_view AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.username,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_amount,
    MAX(o.created_at) as last_order_date,
    MIN(o.created_at) as first_order_date
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed'
WHERE u.role = 'user' AND u.is_active = 1
GROUP BY u.id, u.name, u.username
ORDER BY total_amount DESC;
```

## 6. Indexes สำหรับ Performance

### 6.1 Composite Indexes

```sql
-- สำหรับการค้นหารายการสั่งซื้อของ User
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- สำหรับการค้นหา order_items ตามเลขและวันที่
CREATE INDEX idx_order_items_number_date ON order_items(number, created_at);

-- สำหรับการรวมยอดรายวัน
CREATE INDEX idx_order_items_date_number ON order_items(
    (SELECT DATE(created_at)), number
);

-- สำหรับการค้นหา number_totals
CREATE INDEX idx_number_totals_date_desc ON number_totals(date DESC, number);
```

### 6.2 Partial Indexes

```sql
-- Index เฉพาะ orders ที่ completed
CREATE INDEX idx_orders_completed ON orders(created_at DESC) 
WHERE status = 'completed';

-- Index เฉพาะ users ที่ active
CREATE INDEX idx_users_active_role ON users(role, username) 
WHERE is_active = 1;

-- Index เฉพาะ blocked_numbers ที่ active
CREATE INDEX idx_blocked_numbers_active_only ON blocked_numbers(number) 
WHERE is_active = 1;
```

## 7. Data Migration Scripts

### 7.1 Initial Database Setup

```sql
-- Create all tables
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    customer_name VARCHAR(100),
    total_amount INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'completed',
    pdf_path VARCHAR(255),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    number VARCHAR(10) NOT NULL,
    buy_2_top INTEGER DEFAULT 0,
    buy_2_bottom INTEGER DEFAULT 0,
    buy_3_top INTEGER DEFAULT 0,
    buy_tote INTEGER DEFAULT 0,
    payout_2_top DECIMAL(3,1) DEFAULT 1.0,
    payout_2_bottom DECIMAL(3,1) DEFAULT 1.0,
    payout_3_top DECIMAL(3,1) DEFAULT 1.0,
    payout_tote DECIMAL(3,1) DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Limits table
CREATE TABLE IF NOT EXISTS limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(20) NOT NULL UNIQUE,
    limit_amount INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Blocked numbers table
CREATE TABLE IF NOT EXISTS blocked_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(10) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Number totals table
CREATE TABLE IF NOT EXISTS number_totals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    total_2_top INTEGER DEFAULT 0,
    total_2_bottom INTEGER DEFAULT 0,
    total_3_top INTEGER DEFAULT 0,
    total_tote INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number, date)
);
```

### 7.2 Seed Data

```sql
-- Insert default admin user
INSERT OR IGNORE INTO users (name, username, password_hash, role) VALUES 
('Administrator', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'admin');

-- Insert default limits
INSERT OR IGNORE INTO limits (category, limit_amount) VALUES
('2_top', 50000),      -- 500 บาท
('2_bottom', 50000),   -- 500 บาท  
('3_top', 100000),     -- 1,000 บาท
('tote', 75000);       -- 750 บาท

-- Insert sample blocked numbers
INSERT OR IGNORE INTO blocked_numbers (number) VALUES
('999'),
('000'),
('123');
```

## 8. Backup และ Maintenance

### 8.1 Backup Script

```sql
-- Daily backup
.backup data/backups/lottery_backup_$(date +%Y%m%d).db

-- Vacuum database (optimize)
VACUUM;

-- Analyze statistics
ANALYZE;

-- Check integrity
PRAGMA integrity_check;
```

### 8.2 Cleanup Script

```sql
-- Delete old backups (keep last 30 days)
DELETE FROM number_totals 
WHERE date < DATE('now', '-30 days');

-- Archive old orders (optional)
-- CREATE TABLE orders_archive AS 
-- SELECT * FROM orders WHERE created_at < DATE('now', '-1 year');
-- DELETE FROM orders WHERE created_at < DATE('now', '-1 year');
```

## 9. Performance Optimization

### 9.1 Query Optimization

```sql
-- Use EXPLAIN QUERY PLAN to analyze queries
EXPLAIN QUERY PLAN 
SELECT * FROM orders o 
JOIN order_items oi ON o.id = oi.order_id 
WHERE o.user_id = ? AND DATE(o.created_at) = DATE('now');

-- Optimize with proper indexes
CREATE INDEX idx_orders_user_date_status ON orders(user_id, created_at, status);
```

### 9.2 Connection Optimization

```python
# SQLite connection settings for better performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
```

## 10. Security Considerations

### 10.1 Data Protection

```sql
-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Set secure permissions on database file
-- chmod 600 data/lottery.db

-- Regular backup encryption (if needed)
-- gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
--     --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric \
--     --output lottery_backup.db.gpg lottery_backup.db
```

### 10.2 SQL Injection Prevention

```python
# Always use parameterized queries
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

# Never use string concatenation
# BAD: cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

## 11. Monitoring และ Analytics

### 11.1 Performance Monitoring Queries

```sql
-- Check table sizes
SELECT name, COUNT(*) as row_count 
FROM sqlite_master sm
JOIN (
    SELECT 'users' as name, COUNT(*) as cnt FROM users
    UNION ALL
    SELECT 'orders' as name, COUNT(*) as cnt FROM orders
    UNION ALL
    SELECT 'order_items' as name, COUNT(*) as cnt FROM order_items
) t ON sm.name = t.name;

-- Check index usage
SELECT name, sql FROM sqlite_master WHERE type = 'index';

-- Database size
SELECT page_count * page_size as size_bytes FROM pragma_page_count(), pragma_page_size();
```

### 11.2 Business Analytics Queries

```sql
-- Daily revenue report
SELECT 
    DATE(created_at) as date,
    COUNT(*) as orders,
    SUM(total_amount) as revenue
FROM orders 
WHERE status = 'completed'
  AND created_at >= DATE('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Top numbers by volume
SELECT 
    number,
    SUM(buy_2_top + buy_2_bottom + buy_3_top + buy_tote) as total_volume,
    COUNT(*) as frequency
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'completed'
  AND DATE(o.created_at) = DATE('now')
GROUP BY number
ORDER BY total_volume DESC
LIMIT 10;

-- User activity report
SELECT 
    u.username,
    COUNT(o.id) as orders_today,
    SUM(o.total_amount) as revenue_today
FROM users u
LEFT JOIN orders o ON u.id = o.user_id 
    AND DATE(o.created_at) = DATE('now')
    AND o.status = 'completed'
WHERE u.role = 'user' AND u.is_active = 1
GROUP BY u.id, u.username
ORDER BY revenue_today DESC;
```

## 12. สรุป

ฐานข้อมูลนี้ออกแบบมาเพื่อ:

1. **ประสิทธิภาพ**: ใช้ Indexes ที่เหมาะสม
2. **ความปลอดภัย**: Foreign Keys และ Constraints
3. **ความสมบูรณ์**: Triggers สำหรับ Data Integrity
4. **การขยาย**: สามารถเพิ่มตารางใหม่ได้ง่าย
5. **การบำรุงรักษา**: มี Backup และ Cleanup Scripts
6. **การวิเคราะห์**: Views และ Analytics Queries

โครงสร้างนี้รองรับการใช้งานจริงและสามารถรองรับผู้ใช้หลายร้อยคนได้อย่างมีประสิทธิภาพ



## การคำนวณงวดวันที่ (Lottery Period Calculation)

### กฎการคำนวณ
หวยออกทุกวันที่ 1 และ 16 ของเดือน การคำนวณงวดวันที่จะขึ้นอยู่กับวันที่สั่งซื้อ:

- **วันที่ 1-16 ของเดือน** → งวดวันที่ 16 ของเดือนเดียวกัน
- **วันที่ 17-31 ของเดือน** → งวดวันที่ 1 ของเดือนถัดไป

### ตัวอย่างการคำนวณ

| วันที่สั่งซื้อ | งวดวันที่ |
|---------------|-----------|
| 5 กันยายน 2568 | 16 กันยายน 2568 |
| 15 กันยายน 2568 | 16 กันยายน 2568 |
| 16 กันยายน 2568 | 16 กันยายน 2568 |
| 17 กันยายน 2568 | 1 ตุลาคม 2568 |
| 25 กันยายน 2568 | 1 ตุลาคม 2568 |
| 31 ธันวาคม 2568 | 1 มกราคม 2569 |

### ฟังก์ชันคำนวณ (Python)

```python
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def calculate_lottery_period(order_date):
    """
    คำนวณงวดวันที่จากวันที่สั่งซื้อ
    
    Args:
        order_date (date): วันที่สั่งซื้อ
        
    Returns:
        date: งวดวันที่ (วันที่หวยออก)
    """
    day = order_date.day
    
    if day <= 16:
        # งวดวันที่ 16 ของเดือนเดียวกัน
        return date(order_date.year, order_date.month, 16)
    else:
        # งวดวันที่ 1 ของเดือนถัดไป
        next_month = order_date + relativedelta(months=1)
        return date(next_month.year, next_month.month, 1)

# ตัวอย่างการใช้งาน
order_date = date(2024, 9, 16)  # 16 กันยายน 2568
lottery_period = calculate_lottery_period(order_date)
print(f"สั่งซื้อวันที่: {order_date}")
print(f"งวดวันที่: {lottery_period}")  # 16 กันยายน 2568
```

### SQL Function สำหรับ SQLite

```sql
-- ฟังก์ชันคำนวณงวดวันที่ใน SQLite
CREATE VIEW lottery_period_calculator AS
SELECT 
    DATE('now') as order_date,
    CASE 
        WHEN CAST(strftime('%d', DATE('now')) AS INTEGER) <= 16 THEN
            DATE(strftime('%Y-%m-16', DATE('now')))
        ELSE
            DATE(strftime('%Y-%m-01', DATE('now', '+1 month')))
    END as lottery_period;

-- ตัวอย่างการใช้งาน
SELECT 
    order_date,
    CASE 
        WHEN CAST(strftime('%d', order_date) AS INTEGER) <= 16 THEN
            DATE(strftime('%Y-%m-16', order_date))
        ELSE
            DATE(strftime('%Y-%m-01', order_date, '+1 month'))
    END as lottery_period
FROM orders;
```

### การใช้งานในระบบ

1. **เมื่อสร้าง Order ใหม่:** ระบบจะคำนวณ lottery_period อัตโนมัติจาก created_at
2. **ในหน้า Dashboard:** แสดงข้อมูลแยกตามงวด
3. **ในรายงาน:** สามารถดูยอดขายแยกตามงวดได้
4. **ในใบสั่งซื้อ PDF:** แสดงงวดวันที่ที่ชัดเจน

### ข้อดีของการเพิ่มฟิลด์นี้

- **การจัดกลุ่มข้อมูล:** สามารถแยกข้อมูลตามงวดได้ชัดเจน
- **การรายงาน:** สร้างรายงานยอดขายแยกตามงวด
- **การตรวจสอบ:** ตรวจสอบยอดขายก่อนหวยออกแต่ละงวด
- **การวิเคราะห์:** วิเคราะห์แนวโน้มการซื้อในแต่ละงวด

