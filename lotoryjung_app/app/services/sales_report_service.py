"""
Simple Sales Report Service - รายงานยอดขายและยอดที่คาดว่าจะจ่าย
เรียงจากมากไปหาน้อย ตามตัวอย่างที่ส่งมา
"""

from sqlalchemy import func, and_, desc, case
from app import db
from app.models import Order, OrderItem, Rule
from typing import Dict, List, Optional
from decimal import Decimal

class SalesReportService:
    """Service สำหรับรายงานยอดขายและยอดที่คาดว่าจะจ่าย"""
    
    @staticmethod
    def get_sales_summary_report(batch_id: str) -> Dict:
        """
        สร้างรายงานสรุปยอดขายและยอดที่คาดว่าจะจ่าย
        เรียงจากมากไปหาน้อยตามยอดขายรวม
        
        Args:
            batch_id: รหัส batch ที่ต้องการวิเคราะห์
            
        Returns:
            Dict: ข้อมูลรายงานครบถ้วน
        """
        try:
            # ดึงข้อมูลยอดรวมทั้งหมด
            grand_total = db.session.query(
                func.sum(OrderItem.amount).label('total')
            ).join(Order).filter(Order.batch_id == batch_id).scalar() or 0
            
            if grand_total == 0:
                return {"success": False, "error": "ไม่พบข้อมูลการซื้อ"}
            
            # ดึงข้อมูลแยกตามประเภท
            field_data = {}
            field_labels = {
                '2_top': '2ตัวบน',
                '2_bottom': '2ตัวล่าง', 
                '3_top': '3ตัวบน',
                'tote': 'โต๊ด'
            }
            
            for field, label in field_labels.items():
                numbers_data = SalesReportService._get_numbers_data_for_field(batch_id, field)
                if numbers_data:
                    field_data[field] = {
                        'label': label,
                        'numbers': numbers_data,
                        'total_sales': sum(item['total_amount'] for item in numbers_data),
                        'total_potential_payout': sum(item['potential_payout'] for item in numbers_data)
                    }
            
            return {
                "success": True,
                "data": {
                    "batch_id": batch_id,
                    "grand_total": float(grand_total),
                    "field_data": field_data,
                    "overall_potential_payout": sum(data['total_potential_payout'] for data in field_data.values())
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def _get_numbers_data_for_field(batch_id: str, field: str) -> List[Dict]:
        """ดึงข้อมูลเลขสำหรับประเภทเฉพาะ เรียงตามยอดขายสูงสุด"""
        
        # ดึงข้อมูลยอดรวมของแต่ละเลข
        numbers_query = db.session.query(
            OrderItem.number_norm,
            func.sum(OrderItem.amount).label('total_amount'),
            func.count(OrderItem.id).label('order_count'),
            func.count(func.distinct(Order.user_id)).label('unique_users'),
            func.avg(OrderItem.validation_factor).label('avg_factor')
        ).join(Order).filter(
            and_(
                Order.batch_id == batch_id,
                OrderItem.field == field
            )
        ).group_by(
            OrderItem.number_norm
        ).order_by(
            desc(func.sum(OrderItem.amount))  # เรียงจากมากไปหาน้อย
        ).all()
        
        if not numbers_query:
            return []
        
        # คำนวณยอดที่คาดว่าจะจ่าย
        base_payout_rate = SalesReportService._get_payout_rate(field)
        
        numbers_data = []
        for row in numbers_query:
            total_amount = float(row.total_amount)
            avg_factor = float(row.avg_factor)
            
            # คำนวณยอดที่คาดว่าจะจ่าย
            potential_payout = total_amount * base_payout_rate * avg_factor
            
            numbers_data.append({
                'number': row.number_norm,
                'total_amount': total_amount,
                'order_count': row.order_count,
                'unique_users': row.unique_users,
                'avg_factor': round(avg_factor, 3),
                'potential_payout': round(potential_payout, 2),
                'payout_rate': base_payout_rate
            })
        
        return numbers_data
    
    @staticmethod
    def _get_payout_rate(field: str) -> float:
        """ดึงอัตราการจ่ายสำหรับประเภทเฉพาะ"""
        default_rates = {
            '2_top': 90,
            '2_bottom': 90,
            '3_top': 900,
            'tote': 150
        }
        
        try:
            rate = db.session.query(Rule.value).filter(
                and_(Rule.rule_type == 'payout', Rule.field == field, Rule.is_active == True)
            ).scalar()
            return float(rate) if rate else default_rates.get(field, 90)
        except:
            return default_rates.get(field, 90)
    
    @staticmethod
    def get_top_sales_numbers(batch_id: str, limit: int = 50) -> Dict:
        """
        ดึงเลขที่มียอดขายสูงสุด ทุกประเภทรวมกัน
        
        Args:
            batch_id: รหัส batch
            limit: จำนวนเลขที่ต้องการ (default: 50)
            
        Returns:
            Dict: รายการเลขที่มียอดขายสูงสุด
        """
        try:
            # ดึงข้อมูลทุกเลขทุกประเภท เรียงตามยอดขาย
            top_numbers = db.session.query(
                OrderItem.field,
                OrderItem.number_norm,
                func.sum(OrderItem.amount).label('total_amount'),
                func.count(OrderItem.id).label('order_count'),
                func.avg(OrderItem.validation_factor).label('avg_factor')
            ).join(Order).filter(
                Order.batch_id == batch_id
            ).group_by(
                OrderItem.field, OrderItem.number_norm
            ).order_by(
                desc(func.sum(OrderItem.amount))
            ).limit(limit).all()
            
            if not top_numbers:
                return {"success": False, "error": "ไม่พบข้อมูล"}
            
            # คำนวณยอดที่คาดว่าจะจ่าย
            results = []
            for row in top_numbers:
                payout_rate = SalesReportService._get_payout_rate(row.field)
                total_amount = float(row.total_amount)
                avg_factor = float(row.avg_factor)
                potential_payout = total_amount * payout_rate * avg_factor
                
                results.append({
                    'field': row.field,
                    'field_label': SalesReportService._get_field_label(row.field),
                    'number': row.number_norm,
                    'total_amount': total_amount,
                    'order_count': row.order_count,
                    'avg_factor': round(avg_factor, 3),
                    'payout_rate': payout_rate,
                    'potential_payout': round(potential_payout, 2)
                })
            
            return {
                "success": True,
                "data": {
                    "top_numbers": results,
                    "total_sales": sum(item['total_amount'] for item in results),
                    "total_potential_payout": sum(item['potential_payout'] for item in results)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def _get_field_label(field: str) -> str:
        """แปลงรหัสประเภทเป็นข้อความ"""
        labels = {
            '2_top': '2ตัวบน',
            '2_bottom': '2ตัวล่าง',
            '3_top': '3ตัวบน', 
            'tote': 'โต๊ด'
        }
        return labels.get(field, field)
