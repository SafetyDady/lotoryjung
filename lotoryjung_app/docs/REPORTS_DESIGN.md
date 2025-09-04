# 📊 Reports System Design - ระบบรายงานภาพรวม

## 🎯 ความต้องการ (Requirements)

### 📈 รายงานที่ต้องการ:
1. **ยอดรวมของแต่ละเลขในแต่ละกลุ่ม** (2 บน, 2 ล่าง, 3 บน, โต๊ด)
2. **ยอดซื้อรวมทั้งหมด** ของแต่ละเลขจากผู้ใช้หลายคน
3. **Base Factor เฉลี่ย** (validation_factor เฉลี่ย) ของแต่ละเลข
4. **การแสดงผลแบบตารางและกราฟ**
5. **ฟิลเตอร์ตามช่วงเวลา, batch_id, ประเภทสลาก**

## 🏗️ Database Design เพิ่มเติม

### 📊 ตาราง Reports Summary (เพิ่มใหม่)
```sql
CREATE TABLE report_summaries (
    id INTEGER PRIMARY KEY,
    batch_id VARCHAR(20) NOT NULL,
    lottery_period DATE NOT NULL,
    field VARCHAR(20) NOT NULL,  -- 2_top, 2_bottom, 3_top, tote
    number_norm VARCHAR(10) NOT NULL,
    
    -- Summary Data
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,     -- ยอดซื้อรวมทั้งหมด
    total_orders INTEGER NOT NULL DEFAULT 0,           -- จำนวนคำสั่งซื้อ
    unique_users INTEGER NOT NULL DEFAULT 0,           -- จำนวนผู้ใช้ที่ซื้อ
    
    -- Validation Factor Analysis
    avg_validation_factor DECIMAL(3,2) NOT NULL DEFAULT 1.0,  -- factor เฉลี่ย
    normal_amount DECIMAL(12,2) NOT NULL DEFAULT 0,           -- ยอดปกติ (factor=1.0)
    reduced_amount DECIMAL(12,2) NOT NULL DEFAULT 0,          -- ยอดลดครึ่ง (factor=0.5)
    blocked_amount DECIMAL(12,2) NOT NULL DEFAULT 0,          -- ยอดเลขอั้น
    overlimit_amount DECIMAL(12,2) NOT NULL DEFAULT 0,        -- ยอดเกินขีด
    
    -- Risk Analysis
    risk_level VARCHAR(10) DEFAULT 'LOW',              -- LOW, MEDIUM, HIGH
    concentration_percentage DECIMAL(5,2) DEFAULT 0,   -- % ของยอดรวมทั้งหมด
    
    -- Metadata
    last_calculated DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(batch_id, field, number_norm),
    INDEX idx_summary_batch_field (batch_id, field),
    INDEX idx_summary_period (lottery_period),
    INDEX idx_summary_risk (risk_level, concentration_percentage)
);
```

## 🔧 Service Layer Design

### 📊 ReportsService Class
```python
class ReportsService:
    """Service for generating comprehensive reports"""
    
    @staticmethod
    def generate_batch_summary(batch_id: str) -> dict:
        """สร้างรายงานสรุปสำหรับ batch นั้นๆ"""
        
    @staticmethod
    def get_number_analysis(field: str, number: str, date_from: str, date_to: str) -> dict:
        """วิเคราะห์เลขเฉพาะตัว"""
        
    @staticmethod
    def get_field_summary(field: str, batch_id: str) -> list:
        """สรุปภาพรวมของประเภทสลาก"""
        
    @staticmethod
    def get_risk_analysis(batch_id: str) -> dict:
        """วิเคราะห์ความเสี่ยง"""
        
    @staticmethod
    def calculate_concentration_risk(batch_id: str) -> dict:
        """คำนวณความเสี่ยงจากการกระจุกตัว"""
```

## 📱 User Interface Design

### 🎯 หน้ารายงานหลัก: `/admin/reports`

#### 📊 Dashboard Overview
```
┌─────────────────────────────────────────────────────────────┐
│  📊 รายงานภาพรวมการซื้อสลาก - Batch: 20250902             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 ฟิลเตอร์                                               │
│  [Batch ID ▼] [วันที่ ▼] [ประเภท ▼] [🔍 ค้นหา]             │
│                                                             │
│  📈 สรุปภาพรวม                                             │
│  ┌─────────┬─────────┬─────────┬─────────┐                  │
│  │ 2 ตัวบน │ 2 ตัวล่าง│ 3 ตัวบน │  โต๊ด   │                  │
│  │ 125,000 │ 150,000 │ 80,000  │ 45,000  │                  │
│  │ (1,250) │ (1,500) │  (160)  │  (300)  │                  │
│  └─────────┴─────────┴─────────┴─────────┘                  │
│                                                             │
│  🎯 ตารางรายละเอียด                                        │
│  ┌──────┬────────┬─────────┬─────────┬─────────┬─────────┐  │
│  │ เลข  │ ประเภท │ ยอดรวม  │ คำสั่งซื้อ│ ผู้ซื้อ │ Factor │  │
│  ├──────┼────────┼─────────┼─────────┼─────────┼─────────┤  │
│  │  01  │ 2 บน   │ 25,000  │   50    │   25    │  0.85   │  │
│  │  01  │ 2 ล่าง │ 30,000  │   60    │   30    │  0.90   │  │
│  │ 123  │ 3 บน   │ 15,000  │   15    │   12    │  0.60   │  │
│  └──────┴────────┴─────────┴─────────┴─────────┴─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 📈 กราฟวิเคราะห์
```
┌─────────────────────────────────────────────────────────────┐
│  📊 การกระจายตัวของยอดซื้อ                                │
│                                                             │
│  🔵 ปกติ (Factor 1.0)     🔴 ลดครึ่ง (Factor 0.5)          │
│  🟡 เลขอั้น              🟠 เกินขีด                        │
│                                                             │
│  [Bar Chart showing distribution by number]                 │
│                                                             │
│  📈 Top 10 เลขที่มียอดสูงสุด                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. เลข 01 (2ล่าง): 30,000 บาท (60 คำสั่งซื้อ)      │    │
│  │ 2. เลข 01 (2บน):  25,000 บาท (50 คำสั่งซื้อ)       │    │
│  │ 3. เลข 123 (3บน): 15,000 บาท (15 คำสั่งซื้อ)       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔍 API Endpoints Design

### 📊 Reports API Routes
```python
# รายงานสรุปภาพรวม
GET /admin/api/reports/summary?batch_id=20250902&field=all
Response: {
    "success": true,
    "data": {
        "batch_id": "20250902",
        "lottery_period": "2025-09-02",
        "summary_by_field": {
            "2_top": {"total_amount": 125000, "total_orders": 1250, "avg_factor": 0.85},
            "2_bottom": {"total_amount": 150000, "total_orders": 1500, "avg_factor": 0.90},
            "3_top": {"total_amount": 80000, "total_orders": 160, "avg_factor": 0.75},
            "tote": {"total_amount": 45000, "total_orders": 300, "avg_factor": 0.80}
        },
        "top_numbers": [...],
        "risk_analysis": {...}
    }
}

# รายละเอียดเลขเฉพาะตัว
GET /admin/api/reports/number_detail?number=01&field=2_top&batch_id=20250902
Response: {
    "success": true,
    "data": {
        "number": "01",
        "field": "2_top",
        "total_amount": 25000,
        "total_orders": 50,
        "unique_users": 25,
        "avg_validation_factor": 0.85,
        "breakdown": {
            "normal_amount": 20000,   // factor 1.0
            "reduced_amount": 5000,   // factor 0.5
            "blocked_amount": 0,
            "overlimit_amount": 5000
        },
        "orders_timeline": [...],
        "user_distribution": [...]
    }
}

# ข้อมูลสำหรับกราฟ
GET /admin/api/reports/charts?batch_id=20250902&type=distribution
Response: {
    "success": true,
    "chart_data": {
        "labels": ["01", "02", "03", ...],
        "datasets": [
            {
                "label": "2 ตัวบน",
                "data": [25000, 15000, 10000, ...],
                "backgroundColor": "#007bff"
            },
            {
                "label": "2 ตัวล่าง", 
                "data": [30000, 18000, 12000, ...],
                "backgroundColor": "#28a745"
            }
        ]
    }
}
```

## 💻 Implementation Plan

### Phase 1: Core Reporting Infrastructure
1. **สร้าง ReportsService class**
2. **เพิ่ม API endpoints สำหรับดึงข้อมูล**
3. **สร้างหน้า admin reports พื้นฐาน**

### Phase 2: Advanced Analytics
1. **เพิ่มการวิเคราะห์ความเสี่ยง**
2. **สร้างกราฟแบบ interactive**
3. **เพิ่ม export เป็น Excel/PDF**

### Phase 3: Real-time Dashboard
1. **Auto-refresh ข้อมูล**
2. **Alert สำหรับเลขที่มีความเสี่ยงสูง**
3. **Mobile responsive design**

## 📋 SQL Queries ตัวอย่าง

### 📊 Query สำหรับยอดรวมแต่ละเลข
```sql
-- สรุปยอดรวมแต่ละเลขแยกตามประเภท
SELECT 
    oi.field,
    oi.number_norm,
    SUM(oi.amount) as total_amount,
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT o.user_id) as unique_users,
    AVG(oi.validation_factor) as avg_validation_factor,
    SUM(CASE WHEN oi.validation_factor = 1.0 THEN oi.amount ELSE 0 END) as normal_amount,
    SUM(CASE WHEN oi.validation_factor = 0.5 THEN oi.amount ELSE 0 END) as reduced_amount,
    SUM(CASE WHEN oi.is_blocked = 1 THEN oi.amount ELSE 0 END) as blocked_amount
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.batch_id = ?
GROUP BY oi.field, oi.number_norm
ORDER BY total_amount DESC;

-- Top 10 เลขที่มียอดสูงสุด
SELECT 
    oi.field,
    oi.number_norm,
    SUM(oi.amount) as total_amount,
    COUNT(DISTINCT o.user_id) as buyer_count
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.batch_id = ?
GROUP BY oi.field, oi.number_norm
ORDER BY total_amount DESC
LIMIT 10;

-- การกระจายตัวของ validation factor
SELECT 
    oi.field,
    oi.validation_factor,
    oi.validation_reason,
    COUNT(*) as item_count,
    SUM(oi.amount) as total_amount
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.batch_id = ?
GROUP BY oi.field, oi.validation_factor, oi.validation_reason
ORDER BY oi.field, oi.validation_factor DESC;
```

## 🎨 UI Components

### 📊 สีสำหรับแต่ละประเภท
- **2 ตัวบน**: `#007bff` (น้ำเงิน)
- **2 ตัวล่าง**: `#28a745` (เขียว)  
- **3 ตัวบน**: `#ffc107` (เหลือง)
- **โต๊ด**: `#dc3545` (แดง)

### 🎯 Status Indicators
- **🟢 ปกติ (Factor 1.0)**: เขียว
- **🟡 ลดครึ่ง (Factor 0.5)**: เหลือง
- **🔴 เลขอั้น**: แดง
- **🟠 เกินขีด**: ส้ม

## 🔐 Security & Performance

### 🛡️ Access Control
- เฉพาะ admin เท่านั้นที่เข้าถึงได้
- Rate limiting สำหรับ API calls
- Audit log การเข้าถึงรายงาน

### ⚡ Performance Optimization
- Caching ผลลัพธ์รายงาน (15 นาที)
- Pagination สำหรับข้อมูลจำนวนมาก
- Database indexing สำหรับ queries ที่ใช้บ่อย
- Background job สำหรับ pre-calculate reports

## 📈 Future Enhancements

1. **Machine Learning Prediction**: ทำนายเลขที่อาจเสี่ยงสูง
2. **Real-time Alerts**: แจ้งเตือนเมื่อเลขใดมียอดผิดปกติ  
3. **Comparative Analysis**: เปรียบเทียบกับงวดก่อนหน้า
4. **User Behavior Analysis**: วิเคราะห์พฤติกรรมการซื้อของผู้ใช้
5. **Export Automation**: ส่งรายงานอัตโนมัติทาง email

---

**📊 ระบบรายงานนี้จะให้ข้อมูลครบครันสำหรับการตัดสินใจและการจัดการความเสี่ยงอย่างมีประสิทธิภาพ**
