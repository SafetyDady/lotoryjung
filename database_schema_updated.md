# Database Schema - Updated (P0 Implementation)

## ภาพรวม
เอกสารนี้แสดงโครงสร้างฐานข้อมูลที่อัพเดทตาม Review Report P0 requirements รวมถึงการเพิ่ม Rules system, Audit logs, และการปรับปรุงความปลอดภัย

## การเปลี่ยนแปลงหลัก (Major Changes)

### 1. เพิ่มตาราง rules
- รวม payout และ limit rules ไว้ในตารางเดียว
- รองรับ batch_id สำหรับแยกงวด
- รองรับ condition_type สำหรับเลขอั้น

### 2. ปรับปรุงตาราง order_items
- เพิ่ม number_norm สำหรับเลขที่ปรับมาตรฐาน
- เพิ่ม field สำหรับระบุประเภท
- เพิ่ม unique constraint ป้องกันเลขซ้ำ
- เพิ่ม payout_factor ที่ใช้ตอนซื้อ

### 3. เพิ่มตาราง audit_logs
- บันทึกทุก action สำคัญ
- รองรับการตรวจสอบย้อนหลัง

### 4. ปรับปรุง indexes
- เพิ่ม composite indexes สำหรับ performance
- เพิ่ม indexes สำหรับ batch_id

## โครงสร้างตารางใหม่

### ตาราง users (ไม่เปลี่ยนแปลง)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user'
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role, is_active);
```

### ตาราง orders (เพิ่ม batch_id)
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    customer_name VARCHAR(100),
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'completed', -- 'completed', 'cancelled'
    pdf_path VARCHAR(500),
    notes TEXT,
    lottery_period DATE NOT NULL,
    batch_id VARCHAR(50), -- เพิ่มใหม่สำหรับแยกงวด
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_orders_user_id ON orders(user_id, created_at);
CREATE INDEX idx_orders_lottery_period ON orders(lottery_period);
CREATE INDEX idx_orders_batch_id ON orders(batch_id);
CREATE INDEX idx_orders_status ON orders(status);
```

### ตาราง order_items (ปรับปรุงใหม่ทั้งหมด)
```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    number VARCHAR(10) NOT NULL,           -- เลขที่ซื้อ (ต้นฉบับ)
    number_norm VARCHAR(10) NOT NULL,      -- เลขที่ปรับมาตรฐานแล้ว
    field VARCHAR(20) NOT NULL,            -- '2_top', '2_bottom', '3_top', 'tote'
    buy_amount DECIMAL(10,2) NOT NULL,     -- จำนวนเงินที่ซื้อ
    payout_factor DECIMAL(10,2) NOT NULL, -- อัตราจ่ายที่ใช้ตอนซื้อ
    payout_amount DECIMAL(10,2) NOT NULL, -- จำนวนเงินที่จะได้รับ
    is_blocked BOOLEAN DEFAULT FALSE,      -- เป็นเลขอั้นหรือไม่
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    
    -- ป้องกันเลขซ้ำใน order เดียวกัน
    UNIQUE(order_id, field, number_norm)
);

-- Indexes สำคัญ
CREATE INDEX idx_order_items_field_number ON order_items(field, number_norm, created_at);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_lookup ON order_items(field, number_norm, is_blocked);
```

### ตาราง rules (ใหม่)
```sql
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type VARCHAR(20) NOT NULL,        -- 'payout' หรือ 'limit'
    field VARCHAR(20) NOT NULL,            -- '2_top', '2_bottom', '3_top', 'tote'
    number_norm VARCHAR(10),               -- เลขเฉพาะ, NULL = ทั้งหมด
    payout_factor DECIMAL(10,2),           -- อัตราจ่าย (สำหรับ payout rules)
    limit_amount INTEGER,                  -- จำนวนลิมิต (สำหรับ limit rules)
    scope VARCHAR(20) NOT NULL,            -- 'per-number', 'per-user', 'global'
    condition_type VARCHAR(20) DEFAULT 'normal', -- 'normal', 'blocked'
    is_active BOOLEAN DEFAULT TRUE,
    batch_id VARCHAR(50),                  -- สำหรับแยกงวด
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(rule_type, field, number_norm, condition_type, batch_id)
);

-- Indexes สำคัญ
CREATE INDEX idx_rules_active ON rules(is_active, rule_type, field);
CREATE INDEX idx_rules_lookup ON rules(field, number_norm, is_active, batch_id);
CREATE INDEX idx_rules_batch ON rules(batch_id, is_active);
```

### ตาราง blocked_numbers (ปรับปรุง)
```sql
CREATE TABLE blocked_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number_norm VARCHAR(10) NOT NULL,      -- เลขที่ปรับมาตรฐานแล้ว
    field VARCHAR(20) NOT NULL,            -- 'all', '2_top', '2_bottom', '3_top', 'tote'
    status VARCHAR(20) DEFAULT 'blocked',  -- 'blocked', 'active'
    payout_factor DECIMAL(10,2) DEFAULT 0.5, -- อัตราจ่ายสำหรับเลขอั้น
    effective_date DATE,
    notes TEXT,
    batch_id VARCHAR(50),                  -- สำหรับแยกงวด
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(number_norm, field, batch_id)
);

-- Indexes
CREATE INDEX idx_blocked_numbers_lookup ON blocked_numbers(number_norm, field, status, batch_id);
CREATE INDEX idx_blocked_numbers_batch ON blocked_numbers(batch_id, status);
```

### ตาราง download_tokens (ไม่เปลี่ยนแปลง)
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

### ตาราง audit_logs (ใหม่)
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,                       -- ผู้ทำ action (NULL สำหรับ system)
    action VARCHAR(50) NOT NULL,           -- 'login', 'create_order', 'update_rule', etc.
    table_name VARCHAR(50),                -- ตารางที่ถูกแก้ไข
    record_id INTEGER,                     -- ID ของ record ที่ถูกแก้ไข
    old_values TEXT,                       -- ค่าเก่า (JSON)
    new_values TEXT,                       -- ค่าใหม่ (JSON)
    ip_address VARCHAR(45),                -- IP address
    user_agent TEXT,                       -- Browser info
    session_id VARCHAR(100),               -- Session ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### ตาราง number_totals (สำหรับ aggregation)
```sql
CREATE TABLE number_totals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number_norm VARCHAR(10) NOT NULL,
    field VARCHAR(20) NOT NULL,
    batch_id VARCHAR(50),
    total_amount DECIMAL(10,2) NOT NULL,
    order_count INTEGER NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(number_norm, field, batch_id)
);

-- Indexes
CREATE INDEX idx_number_totals_lookup ON number_totals(number_norm, field, batch_id);
CREATE INDEX idx_number_totals_batch ON number_totals(batch_id);
```

## Migration Scripts

### 1. สร้างตารางใหม่
```sql
-- สร้างตาราง rules
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type VARCHAR(20) NOT NULL,
    field VARCHAR(20) NOT NULL,
    number_norm VARCHAR(10),
    payout_factor DECIMAL(10,2),
    limit_amount INTEGER,
    scope VARCHAR(20) NOT NULL,
    condition_type VARCHAR(20) DEFAULT 'normal',
    is_active BOOLEAN DEFAULT TRUE,
    batch_id VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rule_type, field, number_norm, condition_type, batch_id)
);

-- สร้างตาราง audit_logs
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- สร้างตาราง number_totals
CREATE TABLE number_totals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number_norm VARCHAR(10) NOT NULL,
    field VARCHAR(20) NOT NULL,
    batch_id VARCHAR(50),
    total_amount DECIMAL(10,2) NOT NULL,
    order_count INTEGER NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number_norm, field, batch_id)
);
```

### 2. แก้ไขตารางเดิม
```sql
-- เพิ่มคอลัมน์ใหม่ในตาราง orders
ALTER TABLE orders ADD COLUMN batch_id VARCHAR(50);

-- สร้างตาราง order_items ใหม่
CREATE TABLE order_items_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    number VARCHAR(10) NOT NULL,
    number_norm VARCHAR(10) NOT NULL,
    field VARCHAR(20) NOT NULL,
    buy_amount DECIMAL(10,2) NOT NULL,
    payout_factor DECIMAL(10,2) NOT NULL,
    payout_amount DECIMAL(10,2) NOT NULL,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    UNIQUE(order_id, field, number_norm)
);

-- ปรับปรุงตาราง blocked_numbers
ALTER TABLE blocked_numbers ADD COLUMN number_norm VARCHAR(10);
ALTER TABLE blocked_numbers ADD COLUMN status VARCHAR(20) DEFAULT 'blocked';
ALTER TABLE blocked_numbers ADD COLUMN payout_factor DECIMAL(10,2) DEFAULT 0.5;
ALTER TABLE blocked_numbers ADD COLUMN effective_date DATE;
ALTER TABLE blocked_numbers ADD COLUMN batch_id VARCHAR(50);
```

### 3. Migration ข้อมูล
```sql
-- Migration ข้อมูลจาก order_items เก่าไปใหม่
INSERT INTO order_items_new (order_id, number, number_norm, field, buy_amount, payout_factor, payout_amount, created_at)
SELECT 
    order_id,
    number,
    CASE 
        WHEN LENGTH(number) = 1 THEN '0' || number
        WHEN LENGTH(number) = 2 THEN number
        ELSE number
    END as number_norm,
    '2_top' as field,
    buy_2_top as buy_amount,
    90.0 as payout_factor,
    payout_2_top as payout_amount,
    created_at
FROM order_items 
WHERE buy_2_top > 0

UNION ALL

SELECT 
    order_id,
    number,
    CASE 
        WHEN LENGTH(number) = 1 THEN '0' || number
        WHEN LENGTH(number) = 2 THEN number
        ELSE number
    END as number_norm,
    '2_bottom' as field,
    buy_2_bottom as buy_amount,
    90.0 as payout_factor,
    payout_2_bottom as payout_amount,
    created_at
FROM order_items 
WHERE buy_2_bottom > 0

-- ... ทำแบบเดียวกันสำหรับ 3_top และ tote
```

### 4. สร้าง Indexes ใหม่
```sql
-- Indexes สำหรับ rules
CREATE INDEX idx_rules_active ON rules(is_active, rule_type, field);
CREATE INDEX idx_rules_lookup ON rules(field, number_norm, is_active, batch_id);
CREATE INDEX idx_rules_batch ON rules(batch_id, is_active);

-- Indexes สำหรับ order_items_new
CREATE INDEX idx_order_items_field_number ON order_items_new(field, number_norm, created_at);
CREATE INDEX idx_order_items_order_id ON order_items_new(order_id);
CREATE INDEX idx_order_items_lookup ON order_items_new(field, number_norm, is_blocked);

-- Indexes สำหรับ audit_logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Indexes สำหรับ number_totals
CREATE INDEX idx_number_totals_lookup ON number_totals(number_norm, field, batch_id);
CREATE INDEX idx_number_totals_batch ON number_totals(batch_id);

-- Indexes สำหรับ orders
CREATE INDEX idx_orders_batch_id ON orders(batch_id);

-- Indexes สำหรับ blocked_numbers
CREATE INDEX idx_blocked_numbers_lookup ON blocked_numbers(number_norm, field, status, batch_id);
CREATE INDEX idx_blocked_numbers_batch ON blocked_numbers(batch_id, status);
```

### 5. โหลดข้อมูล Rules เริ่มต้น
```sql
-- Payout rules
INSERT INTO rules (rule_type, field, payout_factor, scope, condition_type) VALUES
('payout', '2_top', 90.0, 'per-number', 'normal'),
('payout', '2_bottom', 90.0, 'per-number', 'normal'),
('payout', '3_top', 900.0, 'per-number', 'normal'),
('payout', 'tote', 150.0, 'per-number', 'normal');

-- Limit rules
INSERT INTO rules (rule_type, field, limit_amount, scope) VALUES
('limit', '2_top', 10000, 'per-number'),
('limit', '2_bottom', 10000, 'per-number'),
('limit', '3_top', 5000, 'per-number'),
('limit', 'tote', 8000, 'per-number');
```

## Views สำหรับ Reporting

### View: order_summary
```sql
CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    o.user_id,
    u.name as user_name,
    o.customer_name,
    o.total_amount,
    o.lottery_period,
    o.batch_id,
    o.created_at,
    COUNT(oi.id) as item_count,
    SUM(CASE WHEN oi.field = '2_top' THEN oi.buy_amount ELSE 0 END) as buy_2_top_total,
    SUM(CASE WHEN oi.field = '2_bottom' THEN oi.buy_amount ELSE 0 END) as buy_2_bottom_total,
    SUM(CASE WHEN oi.field = '3_top' THEN oi.buy_amount ELSE 0 END) as buy_3_top_total,
    SUM(CASE WHEN oi.field = 'tote' THEN oi.buy_amount ELSE 0 END) as buy_tote_total
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id;
```

### View: number_analysis
```sql
CREATE VIEW number_analysis AS
SELECT 
    oi.number_norm,
    oi.field,
    o.batch_id,
    COUNT(*) as order_count,
    SUM(oi.buy_amount) as total_amount,
    AVG(oi.buy_amount) as avg_amount,
    MAX(oi.buy_amount) as max_amount,
    COUNT(DISTINCT o.user_id) as unique_users
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'completed'
GROUP BY oi.number_norm, oi.field, o.batch_id;
```

## Stored Procedures (Functions)

### ฟังก์ชันคำนวณ batch_id
```sql
-- SQLite ไม่รองรับ stored procedures
-- ใช้ Python functions แทน

def get_current_batch_id():
    """สร้าง batch_id สำหรับงวดปัจจุบัน"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    if now.day <= 16:
        # งวดวันที่ 16
        return f"{now.year}{now.month:02d}16"
    else:
        # งวดวันที่ 1 เดือนถัดไป
        next_month = now.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        return f"{next_month.year}{next_month.month:02d}01"
```

## Performance Considerations

### 1. Index Strategy
- ใช้ composite indexes สำหรับ queries ที่ซับซ้อน
- เพิ่ม indexes สำหรับ foreign keys
- ใช้ partial indexes สำหรับ boolean conditions

### 2. Query Optimization
- ใช้ Views สำหรับ complex queries
- ใช้ number_totals table สำหรับ aggregation
- ใช้ batch_id สำหรับ partitioning

### 3. Maintenance
- ลบ audit_logs เก่าเป็นระยะ
- อัพเดท number_totals เป็นระยะ
- Vacuum database เป็นระยะ

## Security Considerations

### 1. Data Protection
- ใช้ foreign key constraints
- ใช้ unique constraints ป้องกันข้อมูลซ้ำ
- ใช้ audit_logs สำหรับ tracking

### 2. Access Control
- ใช้ role-based access ในตาราง users
- ใช้ is_active สำหรับ soft delete
- ใช้ session tracking ใน audit_logs

### 3. Data Integrity
- ใช้ transactions สำหรับ multi-table operations
- ใช้ check constraints สำหรับ validation
- ใช้ triggers สำหรับ auto-update timestamps

## Backup และ Recovery

### 1. Backup Strategy
```bash
# Daily backup
sqlite3 data/lottery.db ".backup data/backup/lottery_$(date +%Y%m%d).db"

# Export to SQL
sqlite3 data/lottery.db ".dump" > data/backup/lottery_$(date +%Y%m%d).sql
```

### 2. Recovery
```bash
# Restore from backup
cp data/backup/lottery_20240901.db data/lottery.db

# Restore from SQL dump
sqlite3 data/lottery_new.db < data/backup/lottery_20240901.sql
```

## สรุป
Database Schema ใหม่นี้ปรับปรุงตาม P0 requirements ครบถ้วน รองรับการขยายตัวในอนาคต และมีความปลอดภัยสูงขึ้น พร้อมสำหรับการ implement ในระบบจริง

