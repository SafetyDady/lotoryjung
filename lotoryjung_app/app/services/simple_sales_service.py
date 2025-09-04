"""
Simple Sales Report Service - รายงานยอดขายแบบง่าย ไม่แยก batch
"""

from sqlalchemy import func, desc, and_
from app import db
from app.models import Order, OrderItem, Rule
from typing import Dict, List
from decimal import Decimal

class SimpleSalesService:
    """Service สำหรับรายงานยอดขายแบบง่าย"""
    
    @staticmethod
    def get_all_sales_report() -> Dict:
        """
        ดึงรายงานยอดขายทั้งหมด ไม่แยก batch
        เรียงจากยอดขายมากไปน้อย ตามตัวอย่าง
        """
        try:
            # ดึงข้อมูลยอดขายรวมของแต่ละเลข
            sales_data = db.session.query(
                OrderItem.field,
                OrderItem.number_norm,
                func.sum(OrderItem.amount).label('total_sales'),
                func.count(OrderItem.id).label('order_count'),
                func.avg(OrderItem.validation_factor).label('avg_factor')
            ).join(Order).group_by(
                OrderItem.field, OrderItem.number_norm
            ).order_by(desc(func.sum(OrderItem.amount))).all()
            
            if not sales_data:
                return {"success": False, "error": "ไม่พบข้อมูルการขาย"}
            
            # ⭐ แก้ไข: รวมข้อมูลโต๊ดที่มีหลักเดียวกัน (เฉพาะข้อมูลเก่า)
            processed_data = []
            tote_groups = {}  # สำหรับรวมโต๊ดที่มีหลักเดียวกัน
            
            for item in sales_data:
                if item.field == 'tote':
                    # สำหรับโต๊ด: ใช้ normalized key
                    from app.utils.number_utils import generate_tote_number
                    normalized_key = generate_tote_number(item.number_norm)
                    
                    if normalized_key not in tote_groups:
                        tote_groups[normalized_key] = {
                            'field': 'tote',
                            'number_norm': normalized_key,
                            'total_sales': 0,
                            'order_count': 0,
                            'validation_factors': []
                        }
                    
                    tote_groups[normalized_key]['total_sales'] += float(item.total_sales)
                    tote_groups[normalized_key]['order_count'] += item.order_count
                    tote_groups[normalized_key]['validation_factors'].append(float(item.avg_factor) * item.order_count)
                else:
                    # สำหรับ field อื่น: ใช้ข้อมูลเดิม
                    processed_data.append(item)
            
            # เพิ่มโต๊ดที่รวมแล้วเข้าไปในข้อมูล
            for normalized_key, group_data in tote_groups.items():
                # คำนวณ avg_factor ใหม่
                total_weighted_factors = sum(group_data['validation_factors'])
                avg_factor = total_weighted_factors / group_data['order_count'] if group_data['order_count'] > 0 else 1.0
                
                # สร้าง mock object เพื่อให้เข้ากับ logic เดิม
                class MockItem:
                    def __init__(self, field, number_norm, total_sales, order_count, avg_factor):
                        self.field = field
                        self.number_norm = number_norm
                        self.total_sales = total_sales
                        self.order_count = order_count
                        self.avg_factor = avg_factor
                
                processed_data.append(MockItem(
                    'tote', normalized_key, group_data['total_sales'],
                    group_data['order_count'], avg_factor
                ))
            
            # เรียงข้อมูลใหม่ตามยอดขาย
            processed_data.sort(key=lambda x: float(x.total_sales), reverse=True)
            
            # คำนวณยอดรวมทั้งหมด (ใช้ข้อมูลหลังรวมแล้ว)
            grand_total = sum(float(item.total_sales) for item in processed_data)
            
            # จัดกลุ่มตามประเภท
            field_groups = {}
            all_numbers = []
            
            for item in processed_data:
                field = item.field
                number = item.number_norm
                total_sales = float(item.total_sales)
                avg_factor = float(item.avg_factor)
                
                # คำนวณยอดคาดว่าจะจ่าย
                payout_rate = SimpleSalesService._get_payout_rate(field)
                estimated_payout = total_sales * payout_rate * avg_factor
                
                number_data = {
                    'field': field,
                    'number': number,
                    'total_sales': total_sales,
                    'order_count': item.order_count,
                    'avg_factor': round(avg_factor, 3),
                    'estimated_payout': round(estimated_payout, 2),
                    'payout_rate': payout_rate,
                    'profit_loss': round(total_sales - estimated_payout, 2)
                }
                
                # เพิ่มในกลุ่มประเภท
                if field not in field_groups:
                    field_groups[field] = []
                field_groups[field].append(number_data)
                
                # เพิ่มในรายการทั้งหมด
                all_numbers.append(number_data)
            
            # คำนวณสรุปตามประเภท
            field_summary = {}
            for field, numbers in field_groups.items():
                field_total_sales = sum(n['total_sales'] for n in numbers)
                field_total_payout = sum(n['estimated_payout'] for n in numbers)
                
                field_summary[field] = {
                    'count': len(numbers),
                    'total_sales': round(field_total_sales, 2),
                    'total_estimated_payout': round(field_total_payout, 2),
                    'profit_loss': round(field_total_sales - field_total_payout, 2),
                    'percentage': round((field_total_sales / grand_total) * 100, 2) if grand_total > 0 else 0
                }
            
            # คำนวณสรุปรวม
            total_estimated_payout = sum(n['estimated_payout'] for n in all_numbers)
            total_profit_loss = grand_total - total_estimated_payout
            
            return {
                "success": True,
                "data": {
                    "overview": {
                        "grand_total": round(grand_total, 2),
                        "total_estimated_payout": round(total_estimated_payout, 2),
                        "total_profit_loss": round(total_profit_loss, 2),
                        "total_numbers": len(all_numbers),
                        "profit_margin_pct": round((total_profit_loss / grand_total) * 100, 2) if grand_total > 0 else 0
                    },
                    "field_summary": field_summary,
                    "field_groups": field_groups,
                    "all_numbers": all_numbers[:100]  # จำกัด 100 อันดับแรก
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def get_top_sales_by_field() -> Dict:
        """
        ดึงยอดขายสูงสุดแยกตามประเภท ไม่แยก batch
        เหมือนตารางในตัวอย่าง
        """
        try:
            # ดึงข้อมูลสำหรับแต่ละประเภท
            fields = ['2_top', '2_bottom', '3_top', 'tote']
            result_data = {}
            
            for field in fields:
                # ดึงข้อมูล top sales ของแต่ละประเภท
                field_data = db.session.query(
                    OrderItem.number_norm,
                    func.sum(OrderItem.amount).label('total_sales'),
                    func.count(OrderItem.id).label('order_count'),
                    func.avg(OrderItem.validation_factor).label('avg_factor')
                ).join(Order).filter(
                    OrderItem.field == field
                ).group_by(
                    OrderItem.number_norm
                ).order_by(desc(func.sum(OrderItem.amount))).limit(20).all()
                
                # คำนวณยอดคาดว่าจะจ่าย
                payout_rate = SimpleSalesService._get_payout_rate(field)
                
                field_numbers = []
                for item in field_data:
                    total_sales = float(item.total_sales)
                    avg_factor = float(item.avg_factor)
                    estimated_payout = total_sales * payout_rate * avg_factor
                    
                    field_numbers.append({
                        'number': item.number_norm,
                        'total_sales': total_sales,
                        'order_count': item.order_count,
                        'avg_factor': round(avg_factor, 3),
                        'estimated_payout': round(estimated_payout, 2),
                        'profit_loss': round(total_sales - estimated_payout, 2)
                    })
                
                result_data[field] = field_numbers
            
            return {
                "success": True,
                "data": result_data
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def _get_payout_rate(field: str) -> float:
        """ดึงอัตราการจ่ายของแต่ละประเภทจากฐานข้อมูล"""
        try:
            # ดึงจาก database ก่อน
            rate = db.session.query(Rule.value).filter(
                and_(Rule.rule_type == 'payout', Rule.field == field, Rule.is_active == True)
            ).scalar()
            
            if rate:
                return float(rate)
            
            # ถ้าไม่มีในฐานข้อมูล ใช้ค่า default ตามมาตรฐานจริง
            default_rates = {
                '2_top': 90,
                '2_bottom': 90, 
                '3_top': 900,
                'tote': 150
            }
            return default_rates.get(field, 90)
            
        except Exception as e:
            print(f"Error getting payout rate for {field}: {e}")
            # กรณีมีข้อผิดพลาด ใช้ค่า default
            default_rates = {
                '2_top': 90,
                '2_bottom': 90, 
                '3_top': 900,
                'tote': 150
            }
            return default_rates.get(field, 90)
    
    @staticmethod
    def get_field_label(field: str) -> str:
        """แปลชื่อประเภท"""
        labels = {
            '2_top': '2ตัวบน',
            '2_bottom': '2ตัวล่าง',
            '3_top': '3ตัวบน', 
            'tote': 'โต๊ด'
        }
        return labels.get(field, field)
