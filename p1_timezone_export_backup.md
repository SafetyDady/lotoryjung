# P1 Implementation: Timezone, Export, and Backup Systems

## ภาพรวม
เอกสารนี้กำหนดการ implement P1 requirements สำหรับระบบ Lotoryjung รวมถึงการจัดการ Timezone, CSV-safe Export, และระบบ Backup/Retention ตาม Review Report

## 1. Timezone Management

### 1.1 Asia/Bangkok Timezone Configuration
การตั้งค่า timezone ให้ถูกต้องเป็นสิ่งสำคัญสำหรับระบบที่ทำงานในประเทศไทย เนื่องจากการคำนวณงวดวันที่และเวลา cut-off ต้องอิงตามเวลาท้องถิ่น

```python
# config.py
import os
from datetime import datetime, timezone, timedelta
import pytz

class Config:
    # Timezone Configuration
    TIMEZONE = pytz.timezone('Asia/Bangkok')
    
    # Cut-off Configuration
    LOTTERY_CUTOFF_HOUR = 15  # 15:30 (3:30 PM)
    LOTTERY_CUTOFF_MINUTE = 30
    
    # Admin Override Settings
    ADMIN_CAN_OVERRIDE_CUTOFF = True
    OVERRIDE_GRACE_PERIOD_MINUTES = 60  # 1 ชั่วโมงหลัง cut-off
    
    @classmethod
    def get_current_time(cls):
        """ดึงเวลาปัจจุบันในเขตเวลาไทย"""
        return datetime.now(cls.TIMEZONE)
    
    @classmethod
    def localize_datetime(cls, dt):
        """แปลง datetime ให้เป็นเขตเวลาไทย"""
        if dt.tzinfo is None:
            return cls.TIMEZONE.localize(dt)
        return dt.astimezone(cls.TIMEZONE)

# utils/timezone_utils.py
from datetime import datetime, date, time, timedelta
import pytz
from config import Config

def get_thai_time():
    """ดึงเวลาปัจจุบันในเขตเวลาไทย"""
    return datetime.now(Config.TIMEZONE)

def convert_to_thai_time(dt):
    """แปลง datetime เป็นเขตเวลาไทย"""
    if dt.tzinfo is None:
        # ถ้าไม่มี timezone info ให้ถือว่าเป็น UTC
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(Config.TIMEZONE)

def format_thai_datetime(dt, format_str='%d/%m/%Y %H:%M:%S'):
    """จัดรูปแบบ datetime ในเขตเวลาไทย"""
    thai_dt = convert_to_thai_time(dt)
    return thai_dt.strftime(format_str)

def get_lottery_periods():
    """ดึงงวดหวยสำหรับเดือนปัจจุบันและเดือนถัดไป"""
    now = get_thai_time()
    current_month = now.replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    periods = []
    
    # งวดวันที่ 1 และ 16 ของเดือนปัจจุบัน
    period_1 = current_month.replace(day=1)
    period_16 = current_month.replace(day=16)
    
    # งวดวันที่ 1 ของเดือนถัดไป
    next_period_1 = next_month.replace(day=1)
    
    periods.extend([period_1, period_16, next_period_1])
    
    return sorted(periods)

def calculate_lottery_period_with_cutoff(order_date=None):
    """
    คำนวณงวดหวยพร้อมตรวจสอบ cut-off time
    
    Args:
        order_date: วันที่สั่งซื้อ (ถ้าไม่ระบุจะใช้เวลาปัจจุบัน)
    
    Returns:
        dict: ข้อมูลงวดและสถานะ cut-off
    """
    
    if order_date is None:
        order_datetime = get_thai_time()
        order_date = order_datetime.date()
    else:
        order_datetime = get_thai_time()
    
    # คำนวณงวดตามกฎเดิม
    if order_date.day <= 16:
        lottery_date = order_date.replace(day=16)
    else:
        # เดือนถัดไป วันที่ 1
        next_month = order_date.replace(day=1) + timedelta(days=32)
        lottery_date = next_month.replace(day=1)
    
    # ตรวจสอบ cut-off time
    cutoff_datetime = datetime.combine(
        lottery_date - timedelta(days=1),  # วันก่อนหวยออก
        time(Config.LOTTERY_CUTOFF_HOUR, Config.LOTTERY_CUTOFF_MINUTE)
    )
    cutoff_datetime = Config.TIMEZONE.localize(cutoff_datetime)
    
    is_past_cutoff = order_datetime > cutoff_datetime
    
    # คำนวณเวลาที่เหลือจนถึง cut-off
    if not is_past_cutoff:
        time_until_cutoff = cutoff_datetime - order_datetime
    else:
        time_until_cutoff = timedelta(0)
    
    return {
        'lottery_date': lottery_date,
        'lottery_period': lottery_date.strftime('%Y-%m-%d'),
        'cutoff_datetime': cutoff_datetime,
        'is_past_cutoff': is_past_cutoff,
        'time_until_cutoff': time_until_cutoff,
        'can_order': not is_past_cutoff,
        'cutoff_message': get_cutoff_message(cutoff_datetime, is_past_cutoff, time_until_cutoff)
    }

def get_cutoff_message(cutoff_datetime, is_past_cutoff, time_until_cutoff):
    """สร้างข้อความแจ้งเตือนเกี่ยวกับ cut-off"""
    
    cutoff_str = format_thai_datetime(cutoff_datetime, '%d/%m/%Y เวลา %H:%M น.')
    
    if is_past_cutoff:
        return f"หมดเวลาสั่งซื้อแล้ว (cut-off: {cutoff_str})"
    
    hours = int(time_until_cutoff.total_seconds() // 3600)
    minutes = int((time_until_cutoff.total_seconds() % 3600) // 60)
    
    if hours > 0:
        return f"เหลือเวลาสั่งซื้อ {hours} ชั่วโมง {minutes} นาที (cut-off: {cutoff_str})"
    else:
        return f"เหลือเวลาสั่งซื้อ {minutes} นาที (cut-off: {cutoff_str})"

def check_admin_override_allowed(user_role, order_datetime=None):
    """
    ตรวจสอบว่า admin สามารถ override cut-off ได้หรือไม่
    
    Args:
        user_role: บทบาทของผู้ใช้
        order_datetime: เวลาที่ต้องการสั่งซื้อ
    
    Returns:
        dict: ข้อมูลการ override
    """
    
    if user_role != 'admin':
        return {'allowed': False, 'reason': 'ไม่ใช่ admin'}
    
    if not Config.ADMIN_CAN_OVERRIDE_CUTOFF:
        return {'allowed': False, 'reason': 'ระบบไม่อนุญาตให้ override'}
    
    if order_datetime is None:
        order_datetime = get_thai_time()
    
    period_info = calculate_lottery_period_with_cutoff()
    cutoff_datetime = period_info['cutoff_datetime']
    
    # ตรวจสอบว่าอยู่ในช่วง grace period หรือไม่
    grace_end = cutoff_datetime + timedelta(minutes=Config.OVERRIDE_GRACE_PERIOD_MINUTES)
    
    if order_datetime <= grace_end:
        remaining_grace = grace_end - order_datetime
        hours = int(remaining_grace.total_seconds() // 3600)
        minutes = int((remaining_grace.total_seconds() % 3600) // 60)
        
        return {
            'allowed': True,
            'reason': f'อยู่ในช่วง grace period (เหลือ {hours}:{minutes:02d})',
            'grace_end': grace_end
        }
    
    return {
        'allowed': False,
        'reason': 'เกินช่วง grace period แล้ว',
        'grace_end': grace_end
    }
```

### 1.2 Database Timezone Handling
```python
# models/base.py
from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declarative_base
from utils.timezone_utils import get_thai_time, convert_to_thai_time

Base = declarative_base()

class TimestampMixin:
    """Mixin สำหรับจัดการ timestamp ในเขตเวลาไทย"""
    
    created_at = Column(DateTime, default=get_thai_time)
    updated_at = Column(DateTime, default=get_thai_time, onupdate=get_thai_time)
    
    def get_created_at_thai(self):
        """ดึง created_at ในเขตเวลาไทย"""
        return convert_to_thai_time(self.created_at)
    
    def get_updated_at_thai(self):
        """ดึง updated_at ในเขตเวลาไทย"""
        return convert_to_thai_time(self.updated_at)
    
    def format_created_at(self, format_str='%d/%m/%Y %H:%M:%S'):
        """จัดรูปแบบ created_at"""
        return format_thai_datetime(self.created_at, format_str)
    
    def format_updated_at(self, format_str='%d/%m/%Y %H:%M:%S'):
        """จัดรูปแบบ updated_at"""
        return format_thai_datetime(self.updated_at, format_str)

# อัพเดท models ให้ใช้ TimestampMixin
class Order(Base, TimestampMixin):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    # ... other fields ...
    
    def get_lottery_period_info(self):
        """ดึงข้อมูลงวดของ order นี้"""
        return calculate_lottery_period_with_cutoff(self.created_at.date())
    
    def is_past_cutoff(self):
        """ตรวจสอบว่า order นี้สั่งหลัง cut-off หรือไม่"""
        period_info = self.get_lottery_period_info()
        return self.created_at > period_info['cutoff_datetime']

class OrderItem(Base, TimestampMixin):
    __tablename__ = 'order_items'
    # ... fields ...
    pass

class AuditLog(Base, TimestampMixin):
    __tablename__ = 'audit_logs'
    # ... fields ...
    pass
```

### 1.3 Frontend Timezone Display
```javascript
// static/js/timezone.js

class ThaiTimezone {
    constructor() {
        this.timezone = 'Asia/Bangkok';
        this.locale = 'th-TH';
    }
    
    getCurrentTime() {
        return new Date().toLocaleString(this.locale, {
            timeZone: this.timezone,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString(this.locale, {
            timeZone: this.timezone,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    updateCutoffCountdown(cutoffDateTime) {
        const cutoff = new Date(cutoffDateTime);
        const now = new Date();
        
        const timeDiff = cutoff - now;
        
        if (timeDiff <= 0) {
            return {
                expired: true,
                message: 'หมดเวลาสั่งซื้อแล้ว'
            };
        }
        
        const hours = Math.floor(timeDiff / (1000 * 60 * 60));
        const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
        
        return {
            expired: false,
            hours: hours,
            minutes: minutes,
            seconds: seconds,
            message: `เหลือเวลา ${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
        };
    }
    
    startCutoffTimer(cutoffDateTime, elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const updateTimer = () => {
            const countdown = this.updateCutoffCountdown(cutoffDateTime);
            
            if (countdown.expired) {
                element.innerHTML = '<span class="text-danger">' + countdown.message + '</span>';
                element.classList.add('expired');
                
                // แจ้งเตือนผู้ใช้
                this.showCutoffExpiredAlert();
                
                return; // หยุด timer
            }
            
            element.innerHTML = `
                <span class="text-warning">
                    <i class="fas fa-clock"></i> ${countdown.message}
                </span>
            `;
            
            // เปลี่ยนสีเมื่อเหลือเวลาน้อย
            if (countdown.hours === 0 && countdown.minutes < 30) {
                element.classList.add('text-danger');
                element.classList.remove('text-warning');
            }
        };
        
        // อัพเดททันที
        updateTimer();
        
        // อัพเดททุกวินาที
        const interval = setInterval(updateTimer, 1000);
        
        // เก็บ interval ID ไว้สำหรับหยุด timer
        element.dataset.intervalId = interval;
        
        return interval;
    }
    
    showCutoffExpiredAlert() {
        // แสดง modal หรือ alert
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'หมดเวลาสั่งซื้อ',
                text: 'หมดเวลาสั่งซื้อสำหรับงวดนี้แล้ว กรุณารองวดถัดไป',
                icon: 'warning',
                confirmButtonText: 'ตกลง'
            }).then(() => {
                // รีเฟรชหน้าหรือ redirect
                window.location.reload();
            });
        } else {
            alert('หมดเวลาสั่งซื้อสำหรับงวดนี้แล้ว');
            window.location.reload();
        }
    }
}

// สร้าง instance
const thaiTime = new ThaiTimezone();

// อัพเดทเวลาปัจจุบันทุก 1 วินาที
function updateCurrentTime() {
    const timeElements = document.querySelectorAll('.current-time');
    timeElements.forEach(element => {
        element.textContent = thaiTime.getCurrentTime();
    });
}

// เริ่ม timer เมื่อโหลดหน้า
document.addEventListener('DOMContentLoaded', function() {
    // อัพเดทเวลาปัจจุบัน
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // เริ่ม cutoff timer ถ้ามี
    const cutoffElement = document.getElementById('cutoff-timer');
    if (cutoffElement && cutoffElement.dataset.cutoffTime) {
        thaiTime.startCutoffTimer(
            cutoffElement.dataset.cutoffTime,
            'cutoff-timer'
        );
    }
});
```

## 2. CSV-Safe Export System

### 2.1 CSV Injection Prevention
CSV injection เป็นช่องโหว่ที่เกิดขึ้นเมื่อข้อมูลที่ export ออกมาเป็น CSV มีตัวอักษรพิเศษที่สามารถถูกตีความเป็นสูตรใน Excel หรือ spreadsheet อื่นๆ

```python
# utils/csv_export.py
import csv
import io
import re
from typing import List, Dict, Any
from datetime import datetime
from utils.timezone_utils import format_thai_datetime

class SafeCSVExporter:
    """CSV Exporter ที่ปลอดภัยจาก CSV injection"""
    
    def __init__(self):
        # ตัวอักษรที่อันตรายใน CSV
        self.dangerous_prefixes = ['=', '+', '-', '@', '\t', '\r', '\n']
        
        # การตั้งค่า CSV
        self.csv_dialect = csv.excel
        self.encoding = 'utf-8-sig'  # UTF-8 with BOM สำหรับ Excel
    
    def sanitize_cell_value(self, value: Any) -> str:
        """
        ทำความสะอาดค่าในเซลล์เพื่อป้องกัน CSV injection
        
        Args:
            value: ค่าที่ต้องการทำความสะอาด
        
        Returns:
            ค่าที่ปลอดภัยแล้ว
        """
        
        if value is None:
            return ''
        
        # แปลงเป็น string
        str_value = str(value).strip()
        
        if not str_value:
            return ''
        
        # ตรวจสอบตัวอักษรอันตราย
        if any(str_value.startswith(prefix) for prefix in self.dangerous_prefixes):
            # เพิ่ม single quote ข้างหน้าเพื่อป้องกัน formula execution
            str_value = "'" + str_value
        
        # ลบ control characters
        str_value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str_value)
        
        # แทนที่ quotes ที่อาจทำให้เกิดปัญหา
        str_value = str_value.replace('"', '""')
        
        return str_value
    
    def export_orders_to_csv(self, orders: List[Dict], filename: str = None) -> str:
        """
        Export รายการ orders เป็น CSV
        
        Args:
            orders: รายการ orders
            filename: ชื่อไฟล์ (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
        
        Returns:
            เนื้อหา CSV
        """
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'orders_export_{timestamp}.csv'
        
        # สร้าง CSV content
        output = io.StringIO()
        
        # Headers
        headers = [
            'หมายเลขคำสั่งซื้อ',
            'ชื่อลูกค้า',
            'ผู้ใช้',
            'จำนวนเงินรวม',
            'งวดวันที่',
            'สถานะ',
            'วันที่สั่งซื้อ',
            'หมายเหตุ'
        ]
        
        writer = csv.writer(output, dialect=self.csv_dialect)
        writer.writerow(headers)
        
        # Data rows
        for order in orders:
            row = [
                self.sanitize_cell_value(order.get('order_number', '')),
                self.sanitize_cell_value(order.get('customer_name', '')),
                self.sanitize_cell_value(order.get('user_name', '')),
                self.sanitize_cell_value(f"{order.get('total_amount', 0):.2f}"),
                self.sanitize_cell_value(order.get('lottery_period', '')),
                self.sanitize_cell_value(order.get('status', '')),
                self.sanitize_cell_value(format_thai_datetime(order.get('created_at'))),
                self.sanitize_cell_value(order.get('notes', ''))
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def export_order_items_to_csv(self, order_items: List[Dict], filename: str = None) -> str:
        """
        Export รายการ order items เป็น CSV
        
        Args:
            order_items: รายการ order items
            filename: ชื่อไฟล์
        
        Returns:
            เนื้อหา CSV
        """
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'order_items_export_{timestamp}.csv'
        
        output = io.StringIO()
        
        headers = [
            'หมายเลขคำสั่งซื้อ',
            'เลข',
            'เลขที่ปรับมาตรฐาน',
            'ประเภท',
            'จำนวนเงินซื้อ',
            'อัตราจ่าย',
            'จำนวนเงินที่จะได้',
            'เลขอั้น',
            'วันที่สั่งซื้อ'
        ]
        
        writer = csv.writer(output, dialect=self.csv_dialect)
        writer.writerow(headers)
        
        for item in order_items:
            row = [
                self.sanitize_cell_value(item.get('order_number', '')),
                self.sanitize_cell_value(item.get('number', '')),
                self.sanitize_cell_value(item.get('number_norm', '')),
                self.sanitize_cell_value(item.get('field', '')),
                self.sanitize_cell_value(f"{item.get('buy_amount', 0):.2f}"),
                self.sanitize_cell_value(f"{item.get('payout_factor', 0):.2f}"),
                self.sanitize_cell_value(f"{item.get('payout_amount', 0):.2f}"),
                self.sanitize_cell_value('ใช่' if item.get('is_blocked') else 'ไม่'),
                self.sanitize_cell_value(format_thai_datetime(item.get('created_at')))
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def export_number_summary_to_csv(self, summary_data: List[Dict], filename: str = None) -> str:
        """
        Export สรุปยอดตามเลขเป็น CSV
        
        Args:
            summary_data: ข้อมูลสรุป
            filename: ชื่อไฟล์
        
        Returns:
            เนื้อหา CSV
        """
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'number_summary_export_{timestamp}.csv'
        
        output = io.StringIO()
        
        headers = [
            'เลข',
            'ประเภท',
            'จำนวนครั้งที่ซื้อ',
            'จำนวนเงินรวม',
            'จำนวนเงินเฉลี่ย',
            'จำนวนเงินสูงสุด',
            'จำนวนผู้ซื้อ',
            'งวดวันที่'
        ]
        
        writer = csv.writer(output, dialect=self.csv_dialect)
        writer.writerow(headers)
        
        for item in summary_data:
            row = [
                self.sanitize_cell_value(item.get('number_norm', '')),
                self.sanitize_cell_value(item.get('field', '')),
                self.sanitize_cell_value(item.get('order_count', 0)),
                self.sanitize_cell_value(f"{item.get('total_amount', 0):.2f}"),
                self.sanitize_cell_value(f"{item.get('avg_amount', 0):.2f}"),
                self.sanitize_cell_value(f"{item.get('max_amount', 0):.2f}"),
                self.sanitize_cell_value(item.get('unique_users', 0)),
                self.sanitize_cell_value(item.get('batch_id', ''))
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def create_download_response(self, csv_content: str, filename: str):
        """
        สร้าง HTTP response สำหรับดาวน์โหลด CSV
        
        Args:
            csv_content: เนื้อหา CSV
            filename: ชื่อไฟล์
        
        Returns:
            Flask Response object
        """
        
        from flask import Response
        
        # เพิ่ม .csv extension ถ้าไม่มี
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response

# Integration กับ Flask routes
from flask import request, jsonify
from services.data_service import DataService

@app.route('/admin/export/orders')
@admin_required
@rate_limit_by_user("10 per minute")
def export_orders():
    """Export orders เป็น CSV"""
    
    try:
        # ดึงพารามิเตอร์
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        batch_id = request.args.get('batch_id')
        user_id = request.args.get('user_id')
        
        # ดึงข้อมูล
        data_service = DataService(db.session)
        orders = data_service.get_orders_for_export(
            start_date=start_date,
            end_date=end_date,
            batch_id=batch_id,
            user_id=user_id
        )
        
        # Export เป็น CSV
        exporter = SafeCSVExporter()
        csv_content = exporter.export_orders_to_csv(orders)
        
        # สร้างชื่อไฟล์
        filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if batch_id:
            filename += f"_batch_{batch_id}"
        
        # บันทึก audit log
        log_audit_event(
            action='export_orders',
            new_values={
                'filename': filename,
                'record_count': len(orders),
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'batch_id': batch_id,
                    'user_id': user_id
                }
            }
        )
        
        return exporter.create_download_response(csv_content, filename)
        
    except Exception as e:
        log_audit_event(
            action='export_orders_error',
            old_values={'error': str(e)}
        )
        
        return jsonify({
            'success': False,
            'error': 'เกิดข้อผิดพลาดในการ export ข้อมูล'
        }), 500

@app.route('/admin/export/order-items')
@admin_required
@rate_limit_by_user("10 per minute")
def export_order_items():
    """Export order items เป็น CSV"""
    
    try:
        # ดึงพารามิเตอร์
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        batch_id = request.args.get('batch_id')
        field = request.args.get('field')
        number = request.args.get('number')
        
        # ดึงข้อมูล
        data_service = DataService(db.session)
        order_items = data_service.get_order_items_for_export(
            start_date=start_date,
            end_date=end_date,
            batch_id=batch_id,
            field=field,
            number=number
        )
        
        # Export เป็น CSV
        exporter = SafeCSVExporter()
        csv_content = exporter.export_order_items_to_csv(order_items)
        
        # สร้างชื่อไฟล์
        filename = f"order_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if field:
            filename += f"_{field}"
        if number:
            filename += f"_{number}"
        
        # บันทึก audit log
        log_audit_event(
            action='export_order_items',
            new_values={
                'filename': filename,
                'record_count': len(order_items),
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'batch_id': batch_id,
                    'field': field,
                    'number': number
                }
            }
        )
        
        return exporter.create_download_response(csv_content, filename)
        
    except Exception as e:
        log_audit_event(
            action='export_order_items_error',
            old_values={'error': str(e)}
        )
        
        return jsonify({
            'success': False,
            'error': 'เกิดข้อผิดพลาดในการ export ข้อมูล'
        }), 500
```

### 2.2 Advanced Export Features
```python
# services/export_service.py
from typing import Optional, List, Dict
import zipfile
import tempfile
import os

class AdvancedExportService:
    """บริการ export ขั้นสูง"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.csv_exporter = SafeCSVExporter()
    
    def export_complete_batch(self, batch_id: str, include_pdfs: bool = False) -> bytes:
        """
        Export ข้อมูลครบชุดสำหรับ batch
        
        Args:
            batch_id: ID ของ batch
            include_pdfs: รวม PDF files หรือไม่
        
        Returns:
            ZIP file content
        """
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f'batch_{batch_id}_export.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                # Export orders
                orders = self.get_batch_orders(batch_id)
                orders_csv = self.csv_exporter.export_orders_to_csv(orders)
                zip_file.writestr('orders.csv', orders_csv)
                
                # Export order items
                order_items = self.get_batch_order_items(batch_id)
                items_csv = self.csv_exporter.export_order_items_to_csv(order_items)
                zip_file.writestr('order_items.csv', items_csv)
                
                # Export number summary
                summary = self.get_batch_number_summary(batch_id)
                summary_csv = self.csv_exporter.export_number_summary_to_csv(summary)
                zip_file.writestr('number_summary.csv', summary_csv)
                
                # Export statistics
                stats = self.get_batch_statistics(batch_id)
                stats_csv = self.export_statistics_to_csv(stats)
                zip_file.writestr('statistics.csv', stats_csv)
                
                # Include PDF files if requested
                if include_pdfs:
                    pdf_dir = 'receipts'
                    for order in orders:
                        if order.get('pdf_path') and os.path.exists(order['pdf_path']):
                            pdf_filename = f"{order['order_number']}.pdf"
                            zip_file.write(
                                order['pdf_path'],
                                f'{pdf_dir}/{pdf_filename}'
                            )
                
                # Add metadata
                metadata = self.create_export_metadata(batch_id, include_pdfs)
                zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # อ่านไฟล์ ZIP
            with open(zip_path, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            return zip_content
    
    def get_batch_orders(self, batch_id: str) -> List[Dict]:
        """ดึงข้อมูล orders ของ batch"""
        
        orders = self.db.query(Order).filter_by(batch_id=batch_id).all()
        
        result = []
        for order in orders:
            user = self.db.query(User).get(order.user_id)
            result.append({
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'user_name': user.name if user else '',
                'total_amount': float(order.total_amount),
                'lottery_period': order.lottery_period.strftime('%Y-%m-%d'),
                'status': order.status,
                'created_at': order.created_at,
                'notes': order.notes,
                'pdf_path': order.pdf_path
            })
        
        return result
    
    def get_batch_order_items(self, batch_id: str) -> List[Dict]:
        """ดึงข้อมูล order items ของ batch"""
        
        items = self.db.query(OrderItem).join(Order).filter(
            Order.batch_id == batch_id
        ).all()
        
        result = []
        for item in items:
            result.append({
                'order_number': item.order.order_number,
                'number': item.number,
                'number_norm': item.number_norm,
                'field': item.field,
                'buy_amount': float(item.buy_amount),
                'payout_factor': float(item.payout_factor),
                'payout_amount': float(item.payout_amount),
                'is_blocked': item.is_blocked,
                'created_at': item.created_at
            })
        
        return result
    
    def get_batch_number_summary(self, batch_id: str) -> List[Dict]:
        """ดึงสรุปยอดตามเลขของ batch"""
        
        summary = self.db.query(
            OrderItem.number_norm,
            OrderItem.field,
            func.count(OrderItem.id).label('order_count'),
            func.sum(OrderItem.buy_amount).label('total_amount'),
            func.avg(OrderItem.buy_amount).label('avg_amount'),
            func.max(OrderItem.buy_amount).label('max_amount'),
            func.count(func.distinct(Order.user_id)).label('unique_users')
        ).join(Order).filter(
            Order.batch_id == batch_id
        ).group_by(
            OrderItem.number_norm,
            OrderItem.field
        ).all()
        
        result = []
        for item in summary:
            result.append({
                'number_norm': item.number_norm,
                'field': item.field,
                'order_count': item.order_count,
                'total_amount': float(item.total_amount),
                'avg_amount': float(item.avg_amount),
                'max_amount': float(item.max_amount),
                'unique_users': item.unique_users,
                'batch_id': batch_id
            })
        
        return result
    
    def create_export_metadata(self, batch_id: str, include_pdfs: bool) -> Dict:
        """สร้าง metadata สำหรับ export"""
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'batch_id': batch_id,
            'include_pdfs': include_pdfs,
            'exported_by': session.get('username', 'system'),
            'timezone': 'Asia/Bangkok',
            'files': {
                'orders.csv': 'รายการคำสั่งซื้อทั้งหมด',
                'order_items.csv': 'รายการสินค้าในคำสั่งซื้อ',
                'number_summary.csv': 'สรุปยอดตามเลข',
                'statistics.csv': 'สถิติการซื้อ',
                'receipts/': 'ใบเสร็จ PDF (ถ้ามี)'
            },
            'notes': 'ไฟล์นี้ถูกสร้างโดยระบบ Lotoryjung Export System'
        }
```

## 3. Backup and Retention System

### 3.1 Automated Backup System
```python
# services/backup_service.py
import os
import shutil
import sqlite3
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path

class BackupService:
    """บริการสำรองข้อมูลอัตโนมัติ"""
    
    def __init__(self):
        self.backup_dir = Path('data/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = 30  # เก็บ backup ไว้ 30 วัน
        self.database_path = 'data/lottery.db'
        self.pdf_dir = Path('static/receipts')
    
    def create_full_backup(self) -> Dict:
        """สร้าง backup ครบชุด"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'full_backup_{timestamp}'
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        results = {
            'timestamp': timestamp,
            'backup_name': backup_name,
            'backup_path': str(backup_path),
            'files': {},
            'success': True,
            'errors': []
        }
        
        try:
            # Backup database
            db_backup_path = backup_path / 'lottery.db'
            self.backup_database(db_backup_path)
            results['files']['database'] = str(db_backup_path)
            
            # Backup PDF files
            if self.pdf_dir.exists():
                pdf_backup_path = backup_path / 'receipts'
                self.backup_pdf_files(pdf_backup_path)
                results['files']['pdf_files'] = str(pdf_backup_path)
            
            # Create backup manifest
            manifest = self.create_backup_manifest(backup_path)
            manifest_path = backup_path / 'manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            results['files']['manifest'] = str(manifest_path)
            
            # Compress backup
            compressed_path = self.compress_backup(backup_path)
            results['compressed_file'] = str(compressed_path)
            
            # Clean up uncompressed files
            shutil.rmtree(backup_path)
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def backup_database(self, backup_path: Path):
        """สำรองฐานข้อมูล"""
        
        # ใช้ SQLite backup API
        source_conn = sqlite3.connect(self.database_path)
        backup_conn = sqlite3.connect(str(backup_path))
        
        try:
            source_conn.backup(backup_conn)
        finally:
            source_conn.close()
            backup_conn.close()
    
    def backup_pdf_files(self, backup_path: Path):
        """สำรอง PDF files"""
        
        if not self.pdf_dir.exists():
            return
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy PDF files
        for pdf_file in self.pdf_dir.rglob('*.pdf'):
            relative_path = pdf_file.relative_to(self.pdf_dir)
            dest_path = backup_path / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf_file, dest_path)
    
    def create_backup_manifest(self, backup_path: Path) -> Dict:
        """สร้าง manifest ของ backup"""
        
        manifest = {
            'created_at': datetime.now().isoformat(),
            'backup_type': 'full',
            'database_file': 'lottery.db',
            'pdf_directory': 'receipts',
            'files': [],
            'statistics': {}
        }
        
        # นับไฟล์ต่างๆ
        total_files = 0
        total_size = 0
        
        for file_path in backup_path.rglob('*'):
            if file_path.is_file() and file_path.name != 'manifest.json':
                file_info = {
                    'path': str(file_path.relative_to(backup_path)),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                manifest['files'].append(file_info)
                total_files += 1
                total_size += file_info['size']
        
        manifest['statistics'] = {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
        
        return manifest
    
    def compress_backup(self, backup_path: Path) -> Path:
        """บีบอัด backup"""
        
        compressed_path = backup_path.with_suffix('.tar.gz')
        
        import tarfile
        with tarfile.open(compressed_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        return compressed_path
    
    def cleanup_old_backups(self) -> Dict:
        """ลบ backup เก่า"""
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        deleted_files = []
        total_size_freed = 0
        
        for backup_file in self.backup_dir.glob('full_backup_*.tar.gz'):
            # ดึงวันที่จากชื่อไฟล์
            try:
                timestamp_str = backup_file.stem.split('_', 2)[2]  # full_backup_YYYYMMDD_HHMMSS
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if file_date < cutoff_date:
                    file_size = backup_file.stat().st_size
                    backup_file.unlink()
                    
                    deleted_files.append({
                        'filename': backup_file.name,
                        'date': file_date.isoformat(),
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
                    total_size_freed += file_size
                    
            except (ValueError, IndexError):
                # ไฟล์ที่ชื่อไม่ตรงรูปแบบ
                continue
        
        return {
            'deleted_files': deleted_files,
            'total_files_deleted': len(deleted_files),
            'total_size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
            'retention_days': self.retention_days
        }
    
    def restore_from_backup(self, backup_file: str) -> Dict:
        """กู้คืนข้อมูลจาก backup"""
        
        backup_path = self.backup_dir / backup_file
        
        if not backup_path.exists():
            return {
                'success': False,
                'error': f'Backup file not found: {backup_file}'
            }
        
        results = {
            'backup_file': backup_file,
            'success': True,
            'restored_files': [],
            'errors': []
        }
        
        try:
            # สร้าง temporary directory
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # แตกไฟล์ backup
                import tarfile
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(temp_path)
                
                # หา directory ที่แตกออกมา
                extracted_dir = None
                for item in temp_path.iterdir():
                    if item.is_dir():
                        extracted_dir = item
                        break
                
                if not extracted_dir:
                    raise ValueError("No directory found in backup file")
                
                # Restore database
                db_backup = extracted_dir / 'lottery.db'
                if db_backup.exists():
                    # สำรอง database ปัจจุบันก่อน
                    current_db = Path(self.database_path)
                    if current_db.exists():
                        backup_current = current_db.with_suffix('.db.backup')
                        shutil.copy2(current_db, backup_current)
                    
                    # Restore database
                    shutil.copy2(db_backup, current_db)
                    results['restored_files'].append('database')
                
                # Restore PDF files
                pdf_backup = extracted_dir / 'receipts'
                if pdf_backup.exists():
                    # สำรอง PDF directory ปัจจุบันก่อน
                    if self.pdf_dir.exists():
                        backup_pdf_dir = self.pdf_dir.with_suffix('.backup')
                        if backup_pdf_dir.exists():
                            shutil.rmtree(backup_pdf_dir)
                        shutil.move(self.pdf_dir, backup_pdf_dir)
                    
                    # Restore PDF files
                    shutil.copytree(pdf_backup, self.pdf_dir)
                    results['restored_files'].append('pdf_files')
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def list_available_backups(self) -> List[Dict]:
        """แสดงรายการ backup ที่มี"""
        
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob('full_backup_*.tar.gz')):
            try:
                timestamp_str = backup_file.stem.split('_', 2)[2]
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                file_size = backup_file.stat().st_size
                
                backups.append({
                    'filename': backup_file.name,
                    'date': file_date.isoformat(),
                    'date_formatted': format_thai_datetime(file_date),
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'age_days': (datetime.now() - file_date).days
                })
                
            except (ValueError, IndexError):
                continue
        
        return backups

# Scheduled tasks
from celery import Celery

app = Celery('backup_tasks')

@app.task
def daily_backup():
    """สำรองข้อมูลรายวัน"""
    
    backup_service = BackupService()
    
    # สร้าง backup
    backup_result = backup_service.create_full_backup()
    
    # ลบ backup เก่า
    cleanup_result = backup_service.cleanup_old_backups()
    
    # บันทึก audit log
    log_audit_event(
        action='daily_backup',
        new_values={
            'backup_result': backup_result,
            'cleanup_result': cleanup_result
        }
    )
    
    return {
        'backup': backup_result,
        'cleanup': cleanup_result
    }

@app.task
def weekly_backup_verification():
    """ตรวจสอบความถูกต้องของ backup รายสัปดาห์"""
    
    backup_service = BackupService()
    backups = backup_service.list_available_backups()
    
    verification_results = []
    
    for backup in backups[-3:]:  # ตรวจสอบ 3 backup ล่าสุด
        # ตรวจสอบว่าไฟล์ไม่เสียหาย
        backup_path = backup_service.backup_dir / backup['filename']
        
        try:
            import tarfile
            with tarfile.open(backup_path, 'r:gz') as tar:
                # ลองแตกไฟล์ดู
                tar.getmembers()
            
            verification_results.append({
                'filename': backup['filename'],
                'status': 'valid',
                'error': None
            })
            
        except Exception as e:
            verification_results.append({
                'filename': backup['filename'],
                'status': 'corrupted',
                'error': str(e)
            })
    
    # บันทึกผลการตรวจสอบ
    log_audit_event(
        action='backup_verification',
        new_values={
            'verification_results': verification_results,
            'total_backups_checked': len(verification_results)
        }
    )
    
    return verification_results
```

### 3.2 Data Retention and Purge System
```python
# services/retention_service.py
from datetime import datetime, timedelta
from typing import Dict, List
import os

class RetentionService:
    """บริการจัดการการเก็บรักษาข้อมูล"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.retention_days = 5  # เก็บข้อมูลไว้ 5 วัน
        self.backup_service = BackupService()
    
    def purge_old_data(self, dry_run: bool = True) -> Dict:
        """
        ลบข้อมูลเก่าตามนีโอบายการเก็บรักษา
        
        Args:
            dry_run: ถ้า True จะไม่ลบจริง แค่แสดงผลที่จะลบ
        
        Returns:
            ผลการลบข้อมูล
        """
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        results = {
            'dry_run': dry_run,
            'cutoff_date': cutoff_date.isoformat(),
            'retention_days': self.retention_days,
            'deleted_data': {},
            'backup_created': False,
            'errors': []
        }
        
        try:
            # สร้าง backup ก่อนลบ (ถ้าไม่ใช่ dry run)
            if not dry_run:
                backup_result = self.backup_service.create_full_backup()
                results['backup_created'] = backup_result['success']
                if not backup_result['success']:
                    results['errors'].extend(backup_result['errors'])
                    return results  # หยุดถ้า backup ไม่สำเร็จ
            
            # ลบ orders และ order_items เก่า
            old_orders = self.db.query(Order).filter(
                Order.created_at < cutoff_date
            ).all()
            
            order_count = len(old_orders)
            item_count = 0
            pdf_count = 0
            pdf_size_mb = 0
            
            for order in old_orders:
                # นับ order items
                items = self.db.query(OrderItem).filter_by(order_id=order.id).all()
                item_count += len(items)
                
                # ลบ PDF file
                if order.pdf_path and os.path.exists(order.pdf_path):
                    file_size = os.path.getsize(order.pdf_path)
                    pdf_size_mb += file_size / (1024 * 1024)
                    
                    if not dry_run:
                        os.remove(order.pdf_path)
                    pdf_count += 1
                
                # ลบ order items
                if not dry_run:
                    for item in items:
                        self.db.delete(item)
                
                # ลบ order
                if not dry_run:
                    self.db.delete(order)
            
            results['deleted_data']['orders'] = order_count
            results['deleted_data']['order_items'] = item_count
            results['deleted_data']['pdf_files'] = pdf_count
            results['deleted_data']['pdf_size_mb'] = round(pdf_size_mb, 2)
            
            # ลบ download tokens เก่า
            old_tokens = self.db.query(DownloadToken).filter(
                DownloadToken.created_at < cutoff_date
            ).all()
            
            token_count = len(old_tokens)
            
            if not dry_run:
                for token in old_tokens:
                    self.db.delete(token)
            
            results['deleted_data']['download_tokens'] = token_count
            
            # ลบ audit logs เก่า (เก็บไว้นานกว่า - 30 วัน)
            audit_cutoff = datetime.now() - timedelta(days=30)
            old_logs = self.db.query(AuditLog).filter(
                AuditLog.created_at < audit_cutoff
            ).all()
            
            log_count = len(old_logs)
            
            if not dry_run:
                for log in old_logs:
                    self.db.delete(log)
            
            results['deleted_data']['audit_logs'] = log_count
            
            # ลบ number_totals เก่า
            old_totals = self.db.query(NumberTotal).join(Order).filter(
                Order.created_at < cutoff_date
            ).all()
            
            total_count = len(old_totals)
            
            if not dry_run:
                for total in old_totals:
                    self.db.delete(total)
            
            results['deleted_data']['number_totals'] = total_count
            
            # Commit การเปลี่ยนแปลง
            if not dry_run:
                self.db.commit()
            
            # คำนวณพื้นที่ที่ประหยัดได้
            total_records = order_count + item_count + token_count + log_count + total_count
            results['total_records_deleted'] = total_records
            
        except Exception as e:
            if not dry_run:
                self.db.rollback()
            results['errors'].append(str(e))
        
        return results
    
    def get_retention_statistics(self) -> Dict:
        """ดึงสถิติข้อมูลที่จะถูกลบ"""
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # นับข้อมูลที่จะถูกลบ
        orders_to_delete = self.db.query(Order).filter(
            Order.created_at < cutoff_date
        ).count()
        
        items_to_delete = self.db.query(OrderItem).join(Order).filter(
            Order.created_at < cutoff_date
        ).count()
        
        tokens_to_delete = self.db.query(DownloadToken).filter(
            DownloadToken.created_at < cutoff_date
        ).count()
        
        # นับข้อมูลทั้งหมด
        total_orders = self.db.query(Order).count()
        total_items = self.db.query(OrderItem).count()
        total_tokens = self.db.query(DownloadToken).count()
        
        return {
            'cutoff_date': cutoff_date.isoformat(),
            'retention_days': self.retention_days,
            'to_delete': {
                'orders': orders_to_delete,
                'order_items': items_to_delete,
                'download_tokens': tokens_to_delete
            },
            'totals': {
                'orders': total_orders,
                'order_items': total_items,
                'download_tokens': total_tokens
            },
            'percentages': {
                'orders': round((orders_to_delete / total_orders * 100) if total_orders > 0 else 0, 2),
                'order_items': round((items_to_delete / total_items * 100) if total_items > 0 else 0, 2),
                'download_tokens': round((tokens_to_delete / total_tokens * 100) if total_tokens > 0 else 0, 2)
            }
        }
    
    def schedule_purge_job(self, days_from_now: int = 1) -> Dict:
        """กำหนดเวลาลบข้อมูลอัตโนมัติ"""
        
        from celery import current_app
        
        # กำหนดเวลาที่จะรัน
        eta = datetime.now() + timedelta(days=days_from_now)
        
        # สร้าง task
        task = current_app.send_task(
            'retention_service.scheduled_purge',
            eta=eta
        )
        
        return {
            'task_id': task.id,
            'scheduled_time': eta.isoformat(),
            'days_from_now': days_from_now
        }

# Celery tasks
@app.task
def scheduled_purge():
    """ลบข้อมูลเก่าตามกำหนดเวลา"""
    
    retention_service = RetentionService(db.session)
    
    # ลบข้อมูลจริง
    purge_result = retention_service.purge_old_data(dry_run=False)
    
    # บันทึก audit log
    log_audit_event(
        action='scheduled_data_purge',
        new_values=purge_result
    )
    
    return purge_result

@app.task
def retention_report():
    """สร้างรายงานการเก็บรักษาข้อมูล"""
    
    retention_service = RetentionService(db.session)
    stats = retention_service.get_retention_statistics()
    
    # บันทึก audit log
    log_audit_event(
        action='retention_report_generated',
        new_values=stats
    )
    
    return stats
```

## สรุป
การ implement P1 requirements นี้จะช่วยให้ระบบมีความสมบูรณ์และพร้อมใช้งานจริงมากขึ้น ผ่านการจัดการ timezone ที่ถูกต้อง การ export ข้อมูลที่ปลอดภัย และระบบ backup/retention ที่เชื่อถือได้ ระบบเหล่านี้จะช่วยลดความเสี่ยงและเพิ่มประสิทธิภาพในการจัดการข้อมูล

