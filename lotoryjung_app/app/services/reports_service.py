"""
Reports Service - ระบบรายงานภาพรวมการซื้อสลาก
"""

from sqlalchemy import func, text, and_, or_, desc, case
from app import db
from app.models import Order, OrderItem, User, Rule
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class ReportsService:
    """Service สำหรับสร้างรายงานและวิเคราะห์ข้อมูล"""
    
    @staticmethod
    def get_batch_summary(batch_id: str) -> Dict:
        """
        สร้างรายงานสรุปภาพรวมสำหรับ batch ที่กำหนด
        
        Args:
            batch_id: รหัส batch ที่ต้องการรายงาน
            
        Returns:
            Dict: ข้อมูลสรุปภาพรวม
        """
        try:
            # ข้อมูลพื้นฐานของ batch
            batch_info = db.session.query(
                Order.batch_id,
                Order.lottery_period,
                func.count(Order.id).label('total_orders'),
                func.count(func.distinct(Order.user_id)).label('unique_users'),
                func.sum(Order.total_amount).label('grand_total')
            ).filter(Order.batch_id == batch_id).first()
            
            if not batch_info:
                return {"success": False, "error": "ไม่พบข้อมูล batch"}
            
            # สรุปตามประเภทสลาก
            field_summary = db.session.query(
                OrderItem.field,
                func.sum(OrderItem.amount).label('total_amount'),
                func.count(OrderItem.id).label('total_items'),
                func.count(func.distinct(Order.user_id)).label('unique_users'),
                func.avg(OrderItem.validation_factor).label('avg_factor'),
                func.sum(
                    case((OrderItem.validation_factor == 1.0, OrderItem.amount), else_=0)
                ).label('normal_amount'),
                func.sum(
                    case((OrderItem.validation_factor == 0.5, OrderItem.amount), else_=0)
                ).label('reduced_amount'),
                func.sum(
                    case((OrderItem.is_blocked == True, OrderItem.amount), else_=0)
                ).label('blocked_amount')
            ).join(Order).filter(Order.batch_id == batch_id).group_by(OrderItem.field).all()
            
            # Top 20 เลขที่มียอดสูงสุด
            top_numbers = db.session.query(
                OrderItem.field,
                OrderItem.number_norm,
                func.sum(OrderItem.amount).label('total_amount'),
                func.count(OrderItem.id).label('order_count'),
                func.count(func.distinct(Order.user_id)).label('buyer_count'),
                func.avg(OrderItem.validation_factor).label('avg_factor')
            ).join(Order).filter(
                Order.batch_id == batch_id
            ).group_by(
                OrderItem.field, OrderItem.number_norm
            ).order_by(
                desc(func.sum(OrderItem.amount))
            ).limit(20).all()
            
            # จัดรูปแบบข้อมูล
            summary_by_field = {}
            for field in field_summary:
                summary_by_field[field.field] = {
                    'total_amount': float(field.total_amount or 0),
                    'total_items': field.total_items or 0,
                    'unique_users': field.unique_users or 0,
                    'avg_factor': round(float(field.avg_factor or 1.0), 3),
                    'normal_amount': float(field.normal_amount or 0),
                    'reduced_amount': float(field.reduced_amount or 0),
                    'blocked_amount': float(field.blocked_amount or 0)
                }
            
            top_numbers_list = []
            for num in top_numbers:
                top_numbers_list.append({
                    'field': num.field,
                    'number': num.number_norm,
                    'total_amount': float(num.total_amount),
                    'order_count': num.order_count,
                    'buyer_count': num.buyer_count,
                    'avg_factor': round(float(num.avg_factor), 3)
                })
            
            return {
                "success": True,
                "data": {
                    "batch_id": batch_id,
                    "lottery_period": batch_info.lottery_period.isoformat() if batch_info.lottery_period else None,
                    "overview": {
                        "total_orders": batch_info.total_orders or 0,
                        "unique_users": batch_info.unique_users or 0,
                        "grand_total": float(batch_info.grand_total or 0)
                    },
                    "summary_by_field": summary_by_field,
                    "top_numbers": top_numbers_list
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def get_number_analysis(field: str, number: str, batch_id: str) -> Dict:
        """
        วิเคราะห์เลขเฉพาะตัวอย่างละเอียด
        
        Args:
            field: ประเภทสลาก (2_top, 2_bottom, 3_top, tote)
            number: หมายเลข
            batch_id: รหัส batch
            
        Returns:
            Dict: ข้อมูลวิเคราะห์เลขนั้น
        """
        try:
            # ข้อมูลรวมของเลขนี้
            total_data = db.session.query(
                func.sum(OrderItem.amount).label('total_amount'),
                func.count(OrderItem.id).label('total_orders'),
                func.count(func.distinct(Order.user_id)).label('unique_users'),
                func.avg(OrderItem.validation_factor).label('avg_factor'),
                func.min(OrderItem.created_at).label('first_order'),
                func.max(OrderItem.created_at).label('last_order')
            ).join(Order).filter(
                and_(
                    Order.batch_id == batch_id,
                    OrderItem.field == field,
                    OrderItem.number_norm == number
                )
            ).first()
            
            if not total_data or not total_data.total_amount:
                return {"success": False, "error": "ไม่พบข้อมูลเลขนี้"}
            
            # การกระจายตัวของ validation factor
            factor_breakdown = db.session.query(
                OrderItem.validation_factor,
                OrderItem.validation_reason,
                func.sum(OrderItem.amount).label('amount'),
                func.count(OrderItem.id).label('count')
            ).join(Order).filter(
                and_(
                    Order.batch_id == batch_id,
                    OrderItem.field == field,
                    OrderItem.number_norm == number
                )
            ).group_by(
                OrderItem.validation_factor, OrderItem.validation_reason
            ).all()
            
            # รายละเอียดผู้ซื้อ
            user_details = db.session.query(
                User.username,
                User.name,
                func.sum(OrderItem.amount).label('total_amount'),
                func.count(OrderItem.id).label('order_count'),
                func.avg(OrderItem.validation_factor).label('avg_factor')
            ).join(Order).join(OrderItem).filter(
                and_(
                    Order.batch_id == batch_id,
                    OrderItem.field == field,
                    OrderItem.number_norm == number
                )
            ).group_by(User.id, User.username, User.name).order_by(
                desc(func.sum(OrderItem.amount))
            ).limit(10).all()
            
            # Timeline การสั่งซื้อ (รายชั่วโมง)
            timeline = db.session.query(
                func.strftime('%Y-%m-%d %H:00:00', OrderItem.created_at).label('hour'),
                func.sum(OrderItem.amount).label('amount'),
                func.count(OrderItem.id).label('orders')
            ).join(Order).filter(
                and_(
                    Order.batch_id == batch_id,
                    OrderItem.field == field,
                    OrderItem.number_norm == number
                )
            ).group_by(
                func.strftime('%Y-%m-%d %H:00:00', OrderItem.created_at)
            ).order_by('hour').all()
            
            # จัดรูปแบบข้อมูล
            breakdown_list = []
            for factor in factor_breakdown:
                breakdown_list.append({
                    'validation_factor': float(factor.validation_factor),
                    'validation_reason': factor.validation_reason,
                    'amount': float(factor.amount),
                    'count': factor.count
                })
            
            user_list = []
            for user in user_details:
                user_list.append({
                    'username': user.username,
                    'name': user.name,
                    'total_amount': float(user.total_amount),
                    'order_count': user.order_count,
                    'avg_factor': round(float(user.avg_factor), 3)
                })
            
            timeline_list = []
            for t in timeline:
                timeline_list.append({
                    'hour': str(t.hour),
                    'amount': float(t.amount),
                    'orders': t.orders
                })
            
            return {
                "success": True,
                "data": {
                    "field": field,
                    "number": number,
                    "batch_id": batch_id,
                    "summary": {
                        "total_amount": float(total_data.total_amount),
                        "total_orders": total_data.total_orders,
                        "unique_users": total_data.unique_users,
                        "avg_factor": round(float(total_data.avg_factor), 3),
                        "first_order": total_data.first_order.isoformat() if total_data.first_order else None,
                        "last_order": total_data.last_order.isoformat() if total_data.last_order else None
                    },
                    "factor_breakdown": breakdown_list,
                    "top_users": user_list,
                    "timeline": timeline_list
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def get_risk_analysis(batch_id: str, concentration_threshold: float = 0.1) -> Dict:
        """
        วิเคราะห์ความเสี่ยงจากการกระจุกตัวของยอดซื้อ
        
        Args:
            batch_id: รหัส batch
            concentration_threshold: เกณฑ์การกระจุกตัว (เช่น 0.1 = 10%)
            
        Returns:
            Dict: ข้อมูลวิเคราะห์ความเสี่ยง
        """
        try:
            # ยอดรวมทั้งหมด
            grand_total = db.session.query(
                func.sum(OrderItem.amount).label('total')
            ).join(Order).filter(Order.batch_id == batch_id).scalar() or 0
            
            if grand_total == 0:
                return {"success": False, "error": "ไม่พบข้อมูลการซื้อ"}
            
            # เลขที่มีการกระจุกตัวสูง
            high_concentration = db.session.query(
                OrderItem.field,
                OrderItem.number_norm,
                func.sum(OrderItem.amount).label('total_amount'),
                (func.sum(OrderItem.amount) / grand_total * 100).label('percentage')
            ).join(Order).filter(
                Order.batch_id == batch_id
            ).group_by(
                OrderItem.field, OrderItem.number_norm
            ).having(
                (func.sum(OrderItem.amount) / grand_total) > concentration_threshold
            ).order_by(
                desc(func.sum(OrderItem.amount))
            ).all()
            
            # ความเสี่ยงตาม validation factor
            factor_risk = db.session.query(
                OrderItem.field,
                func.sum(
                    case((OrderItem.validation_factor < 1.0, OrderItem.amount), else_=0)
                ).label('reduced_amount'),
                func.sum(OrderItem.amount).label('total_amount')
            ).join(Order).filter(
                Order.batch_id == batch_id
            ).group_by(OrderItem.field).all()
            
            # จัดรูปแบบข้อมูล
            high_risk_numbers = []
            for item in high_concentration:
                risk_level = "HIGH" if item.percentage > 20 else "MEDIUM" if item.percentage > 10 else "LOW"
                high_risk_numbers.append({
                    'field': item.field,
                    'number': item.number_norm,
                    'total_amount': float(item.total_amount),
                    'percentage': round(float(item.percentage), 2),
                    'risk_level': risk_level
                })
            
            field_risks = {}
            for risk in factor_risk:
                reduced_percentage = (float(risk.reduced_amount) / float(risk.total_amount) * 100) if risk.total_amount > 0 else 0
                field_risks[risk.field] = {
                    'total_amount': float(risk.total_amount),
                    'reduced_amount': float(risk.reduced_amount),
                    'reduced_percentage': round(reduced_percentage, 2)
                }
            
            return {
                "success": True,
                "data": {
                    "batch_id": batch_id,
                    "grand_total": float(grand_total),
                    "concentration_threshold": concentration_threshold * 100,
                    "high_risk_numbers": high_risk_numbers,
                    "field_risks": field_risks,
                    "summary": {
                        "high_risk_count": len(high_risk_numbers),
                        "total_high_risk_amount": sum([item['total_amount'] for item in high_risk_numbers]),
                        "high_risk_percentage": round(
                            sum([item['total_amount'] for item in high_risk_numbers]) / float(grand_total) * 100, 2
                        )
                    }
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def get_chart_data(batch_id: str, chart_type: str = "field_distribution") -> Dict:
        """
        สร้างข้อมูลสำหรับแสดงกราฟ
        
        Args:
            batch_id: รหัส batch
            chart_type: ประเภทกราฟ (field_distribution, top_numbers, factor_analysis)
            
        Returns:
            Dict: ข้อมูลสำหรับกราฟ
        """
        try:
            if chart_type == "field_distribution":
                # กราฟแสดงการกระจายตามประเภทสลาก
                data = db.session.query(
                    OrderItem.field,
                    func.sum(OrderItem.amount).label('total_amount'),
                    func.count(OrderItem.id).label('total_orders')
                ).join(Order).filter(
                    Order.batch_id == batch_id
                ).group_by(OrderItem.field).all()
                
                labels = []
                amounts = []
                counts = []
                
                field_names = {
                    '2_top': '2 ตัวบน',
                    '2_bottom': '2 ตัวล่าง', 
                    '3_top': '3 ตัวบน',
                    'tote': 'โต๊ด'
                }
                
                for item in data:
                    labels.append(field_names.get(item.field, item.field))
                    amounts.append(float(item.total_amount))
                    counts.append(item.total_orders)
                
                return {
                    "success": True,
                    "chart_data": {
                        "type": "pie",
                        "labels": labels,
                        "datasets": [{
                            "label": "ยอดซื้อ (บาท)",
                            "data": amounts,
                            "backgroundColor": ["#007bff", "#28a745", "#ffc107", "#dc3545"]
                        }]
                    }
                }
                
            elif chart_type == "top_numbers":
                # กราฟแสดง Top 10 เลขยอดสูงสุด
                data = db.session.query(
                    OrderItem.field,
                    OrderItem.number_norm,
                    func.sum(OrderItem.amount).label('total_amount')
                ).join(Order).filter(
                    Order.batch_id == batch_id
                ).group_by(
                    OrderItem.field, OrderItem.number_norm
                ).order_by(
                    desc(func.sum(OrderItem.amount))
                ).limit(10).all()
                
                labels = []
                amounts = []
                colors = []
                
                color_map = {
                    '2_top': '#007bff',
                    '2_bottom': '#28a745',
                    '3_top': '#ffc107', 
                    'tote': '#dc3545'
                }
                
                for item in data:
                    labels.append(f"{item.number_norm} ({item.field})")
                    amounts.append(float(item.total_amount))
                    colors.append(color_map.get(item.field, '#6c757d'))
                
                return {
                    "success": True,
                    "chart_data": {
                        "type": "bar",
                        "labels": labels,
                        "datasets": [{
                            "label": "ยอดซื้อ (บาท)",
                            "data": amounts,
                            "backgroundColor": colors
                        }]
                    }
                }
                
            elif chart_type == "factor_analysis":
                # กราฟแสดงการกระจายของ validation factor
                data = db.session.query(
                    OrderItem.validation_factor,
                    OrderItem.validation_reason,
                    func.sum(OrderItem.amount).label('total_amount'),
                    func.count(OrderItem.id).label('count')
                ).join(Order).filter(
                    Order.batch_id == batch_id
                ).group_by(
                    OrderItem.validation_factor, OrderItem.validation_reason
                ).order_by(OrderItem.validation_factor.desc()).all()
                
                labels = []
                amounts = []
                colors = []
                
                for item in data:
                    factor_text = f"Factor {item.validation_factor}"
                    if item.validation_reason != 'ปกติ':
                        factor_text += f" ({item.validation_reason})"
                    
                    labels.append(factor_text)
                    amounts.append(float(item.total_amount))
                    
                    if item.validation_factor == 1.0:
                        colors.append('#28a745')  # เขียว - ปกติ
                    else:
                        colors.append('#ffc107')  # เหลือง - ลดครึ่ง
                
                return {
                    "success": True,
                    "chart_data": {
                        "type": "doughnut",
                        "labels": labels,
                        "datasets": [{
                            "label": "ยอดซื้อ (บาท)",
                            "data": amounts,
                            "backgroundColor": colors
                        }]
                    }
                }
            
            else:
                return {"success": False, "error": "ประเภทกราฟไม่ถูกต้อง"}
                
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def get_available_batches() -> List[Dict]:
        """
        ดึงรายการ batch ที่มีข้อมูล
        
        Returns:
            List[Dict]: รายการ batch
        """
        try:
            batches = db.session.query(
                Order.batch_id,
                Order.lottery_period,
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_amount'),
                func.min(Order.created_at).label('first_order'),
                func.max(Order.created_at).label('last_order')
            ).group_by(
                Order.batch_id, Order.lottery_period
            ).order_by(
                desc(Order.lottery_period)
            ).all()
            
            batch_list = []
            for batch in batches:
                batch_list.append({
                    'batch_id': batch.batch_id,
                    'lottery_period': batch.lottery_period.isoformat() if batch.lottery_period else None,
                    'order_count': batch.order_count,
                    'total_amount': float(batch.total_amount or 0),
                    'first_order': batch.first_order.isoformat() if batch.first_order else None,
                    'last_order': batch.last_order.isoformat() if batch.last_order else None
                })
            
            return batch_list
            
        except Exception as e:
            return []
