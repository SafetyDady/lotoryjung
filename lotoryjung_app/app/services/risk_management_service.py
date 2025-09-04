"""
Risk Management Service - ระบบบริหารความเสี่ยงสำหรับ Admin
เน้นการประเมินและจัดการความเสี่ยงเป็นหลัก
"""

from sqlalchemy import func, text, and_, or_, desc, case
from app import db
from app.models import Order, OrderItem, User, Rule
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import math

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class RiskManagementService:
    """Service สำหรับการบริหารความเสี่ยงของ Admin"""
    
    # เกณฑ์ความเสี่ยง
    RISK_THRESHOLDS = {
        'HIGH': 80,      # 80+ = ความเสี่ยงสูง
        'MEDIUM': 50,    # 50-79 = ความเสี่ยงปานกลาง
        'LOW': 0         # 0-49 = ความเสี่ยงต่ำ
    }
    
    # น้ำหนักการคำนวณความเสี่ยง
    RISK_WEIGHTS = {
        'concentration': 0.4,    # น้ำหนักการกระจุกตัว 40%
        'factor': 0.3,          # น้ำหนัก factor risk 30%
        'user_concentration': 0.2, # น้ำหนักการกระจุกตัวของผู้ใช้ 20%
        'trend': 0.1            # น้ำหนักแนวโน้ม 10%
    }
    
    @staticmethod
    def get_risk_dashboard(batch_id: str) -> Dict:
        """
        สร้าง Risk Management Dashboard สำหรับ Admin
        
        Args:
            batch_id: รหัส batch ที่ต้องการวิเคราะห์
            
        Returns:
            Dict: ข้อมูล risk dashboard ครบถ้วน
        """
        try:
            # ข้อมูลพื้นฐาน
            base_data = RiskManagementService._get_base_data(batch_id)
            if not base_data['success']:
                return base_data
            
            grand_total = base_data['grand_total']
            
            # คำนวณ Risk Score สำหรับแต่ละเลข
            risk_analysis = RiskManagementService._calculate_comprehensive_risk(batch_id, grand_total)
            
            # จัดกลุ่มตามระดับความเสี่ยง
            risk_summary = RiskManagementService._categorize_risk_levels(risk_analysis)
            
            # Top risk numbers (เรียงตามความเสี่ยงสูงสุด)
            top_risks = sorted(risk_analysis, key=lambda x: x['risk_score'], reverse=True)[:20]
            
            # Overall risk metrics
            overall_metrics = RiskManagementService._calculate_overall_metrics(risk_analysis, grand_total)
            
            # Risk breakdown by categories
            risk_breakdown = RiskManagementService._get_risk_breakdown(risk_analysis)
            
            return {
                "success": True,
                "data": {
                    "batch_id": batch_id,
                    "overall_metrics": overall_metrics,
                    "risk_summary": risk_summary,
                    "top_risks": top_risks,
                    "risk_breakdown": risk_breakdown,
                    "alerts": RiskManagementService._generate_alerts(top_risks),
                    "recommendations": RiskManagementService._generate_recommendations(top_risks)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
    
    @staticmethod
    def _get_base_data(batch_id: str) -> Dict:
        """ดึงข้อมูลพื้นฐานสำหรับการคำนวณ"""
        try:
            # ยอดรวมทั้งหมด
            grand_total = db.session.query(
                func.sum(OrderItem.amount).label('total')
            ).join(Order).filter(Order.batch_id == batch_id).scalar() or 0
            
            if grand_total == 0:
                return {"success": False, "error": "ไม่พบข้อมูลการซื้อ"}
            
            return {
                "success": True, 
                "grand_total": float(grand_total)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _calculate_comprehensive_risk(batch_id: str, grand_total: float) -> List[Dict]:
        """คำนวณความเสี่ยงแบบครบถ้วนสำหรับแต่ละเลข"""
        
        # ข้อมูลรวมของแต่ละเลข
        number_data = db.session.query(
            OrderItem.field,
            OrderItem.number_norm,
            func.sum(OrderItem.amount).label('total_amount'),
            func.count(OrderItem.id).label('order_count'),
            func.count(func.distinct(Order.user_id)).label('unique_users'),
            func.avg(OrderItem.validation_factor).label('avg_factor'),
            func.max(OrderItem.amount).label('max_single_order'),
            # ยอดรวมแยกตาม factor
            func.sum(
                case((OrderItem.validation_factor == 1.0, OrderItem.amount), else_=0)
            ).label('normal_amount'),
            func.sum(
                case((OrderItem.validation_factor < 1.0, OrderItem.amount), else_=0)
            ).label('reduced_amount'),
            # ข้อมูลผู้ใช้ที่ซื้อมากที่สุด
            func.max(
                func.sum(OrderItem.amount)
            ).label('max_user_amount')
        ).join(Order).filter(
            Order.batch_id == batch_id
        ).group_by(
            OrderItem.field, OrderItem.number_norm
        ).subquery()
        
        # ดึงข้อมูลผู้ใช้ที่ซื้อมากที่สุดในแต่ละเลข
        user_concentration_data = db.session.query(
            OrderItem.field,
            OrderItem.number_norm,
            func.sum(OrderItem.amount).label('user_total'),
            func.max(func.sum(OrderItem.amount)).label('max_user_total')
        ).join(Order).filter(
            Order.batch_id == batch_id
        ).group_by(
            OrderItem.field, OrderItem.number_norm, Order.user_id
        ).subquery()
        
        # รวมข้อมูลและคำนวณ max user amount ต่อเลข
        user_max_query = db.session.query(
            user_concentration_data.c.field,
            user_concentration_data.c.number_norm,
            func.max(user_concentration_data.c.user_total).label('max_user_amount')
        ).group_by(
            user_concentration_data.c.field,
            user_concentration_data.c.number_norm
        ).all()
        
        user_max_dict = {}
        for row in user_max_query:
            key = f"{row.field}_{row.number_norm}"
            user_max_dict[key] = float(row.max_user_amount)
        
        # ดึงข้อมูลหลักและรวมกับข้อมูลผู้ใช้
        main_query = db.session.query(number_data).all()
        
        risk_analysis = []
        
        for row in main_query:
            # คำนวณ Risk Components
            concentration_pct = (float(row.total_amount) / grand_total) * 100
            factor_risk_pct = (1.0 - float(row.avg_factor)) * 100
            
            # User concentration risk
            key = f"{row.field}_{row.number_norm}"
            max_user_amount = user_max_dict.get(key, 0)
            user_concentration_pct = (max_user_amount / float(row.total_amount)) * 100 if row.total_amount > 0 else 0
            
            # Trend risk (simplified - จะต้องมีข้อมูลเปรียบเทียบ)
            trend_risk_pct = 0  # TODO: implement trend analysis
            
            # คำนวณ Risk Score รวม
            risk_score = (
                concentration_pct * RiskManagementService.RISK_WEIGHTS['concentration'] +
                factor_risk_pct * RiskManagementService.RISK_WEIGHTS['factor'] +
                user_concentration_pct * RiskManagementService.RISK_WEIGHTS['user_concentration'] +
                trend_risk_pct * RiskManagementService.RISK_WEIGHTS['trend']
            )
            
            # คำนวณ Potential Payout
            base_payout_rate = RiskManagementService._get_base_payout_rate(row.field)
            potential_payout = float(row.total_amount) * base_payout_rate * float(row.avg_factor)
            
            # กำหนดระดับความเสี่ยง
            if risk_score >= RiskManagementService.RISK_THRESHOLDS['HIGH']:
                risk_level = 'HIGH'
                risk_color = 'danger'
                action_needed = 'STOP'
            elif risk_score >= RiskManagementService.RISK_THRESHOLDS['MEDIUM']:
                risk_level = 'MEDIUM'
                risk_color = 'warning'
                action_needed = 'WATCH'
            else:
                risk_level = 'LOW'
                risk_color = 'success'
                action_needed = 'OK'
            
            risk_analysis.append({
                'field': row.field,
                'number': row.number_norm,
                'total_amount': float(row.total_amount),
                'order_count': row.order_count,
                'unique_users': row.unique_users,
                'avg_factor': round(float(row.avg_factor), 3),
                'potential_payout': round(potential_payout, 2),
                'concentration_pct': round(concentration_pct, 2),
                'factor_risk_pct': round(factor_risk_pct, 2),
                'user_concentration_pct': round(user_concentration_pct, 2),
                'max_user_amount': max_user_amount,
                'risk_score': round(risk_score, 1),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'action_needed': action_needed,
                'normal_amount': float(row.normal_amount or 0),
                'reduced_amount': float(row.reduced_amount or 0)
            })
        
        return risk_analysis
    
    @staticmethod
    def _get_base_payout_rate(field: str) -> float:
        """ดึงอัตราการจ่ายพื้นฐาน"""
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
    def _categorize_risk_levels(risk_analysis: List[Dict]) -> Dict:
        """จัดกลุ่มตามระดับความเสี่ยง"""
        summary = {
            'HIGH': {'count': 0, 'total_amount': 0, 'total_payout': 0},
            'MEDIUM': {'count': 0, 'total_amount': 0, 'total_payout': 0},
            'LOW': {'count': 0, 'total_amount': 0, 'total_payout': 0}
        }
        
        for item in risk_analysis:
            level = item['risk_level']
            summary[level]['count'] += 1
            summary[level]['total_amount'] += item['total_amount']
            summary[level]['total_payout'] += item['potential_payout']
        
        return summary
    
    @staticmethod
    def _calculate_overall_metrics(risk_analysis: List[Dict], grand_total: float) -> Dict:
        """คำนวณ metrics โดยรวม"""
        total_potential_payout = sum(item['potential_payout'] for item in risk_analysis)
        total_reduced_amount = sum(item['reduced_amount'] for item in risk_analysis)
        total_normal_amount = sum(item['normal_amount'] for item in risk_analysis)
        
        high_risk_count = len([item for item in risk_analysis if item['risk_level'] == 'HIGH'])
        medium_risk_count = len([item for item in risk_analysis if item['risk_level'] == 'MEDIUM'])
        
        # คำนวณ concentration risk โดยรวม
        max_concentration = max((item['concentration_pct'] for item in risk_analysis), default=0)
        
        # คำนวณ average factor โดยรวม
        weighted_avg_factor = total_normal_amount / grand_total if grand_total > 0 else 0
        
        return {
            'grand_total': grand_total,
            'total_potential_payout': round(total_potential_payout, 2),
            'total_numbers': len(risk_analysis),
            'high_risk_count': high_risk_count,
            'medium_risk_count': medium_risk_count,
            'max_concentration_pct': round(max_concentration, 2),
            'factor_impact_pct': round((total_reduced_amount / grand_total) * 100, 2) if grand_total > 0 else 0,
            'weighted_avg_factor': round(weighted_avg_factor + (total_reduced_amount * 0.5 / grand_total), 3) if grand_total > 0 else 0
        }
    
    @staticmethod
    def _get_risk_breakdown(risk_analysis: List[Dict]) -> Dict:
        """แยกการวิเคราะห์ตามประเภทความเสี่ยง"""
        field_breakdown = {}
        
        for item in risk_analysis:
            field = item['field']
            if field not in field_breakdown:
                field_breakdown[field] = {
                    'high_risk': 0,
                    'medium_risk': 0,
                    'low_risk': 0,
                    'total_amount': 0,
                    'avg_risk_score': 0
                }
            
            if item['risk_level'] == 'HIGH':
                field_breakdown[field]['high_risk'] += 1
            elif item['risk_level'] == 'MEDIUM':
                field_breakdown[field]['medium_risk'] += 1
            else:
                field_breakdown[field]['low_risk'] += 1
            
            field_breakdown[field]['total_amount'] += item['total_amount']
        
        # คำนวณ average risk score ต่อ field
        for field in field_breakdown:
            field_items = [item for item in risk_analysis if item['field'] == field]
            if field_items:
                avg_score = sum(item['risk_score'] for item in field_items) / len(field_items)
                field_breakdown[field]['avg_risk_score'] = round(avg_score, 1)
        
        return field_breakdown
    
    @staticmethod
    def _generate_alerts(top_risks: List[Dict]) -> List[Dict]:
        """สร้างการแจ้งเตือน"""
        alerts = []
        
        for item in top_risks[:5]:  # Top 5 most risky
            if item['risk_level'] == 'HIGH':
                alerts.append({
                    'type': 'danger',
                    'title': f"⚠️ High Risk Alert",
                    'message': f"เลข {item['number']} ({item['field']}) มีความเสี่ยงสูง (Score: {item['risk_score']})",
                    'action': 'ควรหยุดรับซื้อหรือลดขีดจำกัดทันที',
                    'data': item
                })
            elif item['risk_level'] == 'MEDIUM' and item['concentration_pct'] > 8:
                alerts.append({
                    'type': 'warning',
                    'title': f"📊 Concentration Warning",
                    'message': f"เลข {item['number']} ({item['field']}) มียอดกระจุกตัว {item['concentration_pct']}%",
                    'action': 'ควรติดตามอย่างใกล้ชิด',
                    'data': item
                })
        
        return alerts
    
    @staticmethod
    def _generate_recommendations(top_risks: List[Dict]) -> List[Dict]:
        """สร้างคำแนะนำการจัดการความเสี่ยง"""
        recommendations = []
        
        high_risk_items = [item for item in top_risks if item['risk_level'] == 'HIGH']
        medium_risk_items = [item for item in top_risks if item['risk_level'] == 'MEDIUM']
        
        if high_risk_items:
            recommendations.append({
                'type': 'immediate',
                'title': '🚨 ดำเนินการทันที',
                'items': [
                    f"หยุดรับซื้อเลข {item['number']} ({item['field']}) - Risk Score: {item['risk_score']}"
                    for item in high_risk_items[:3]
                ]
            })
        
        if medium_risk_items:
            recommendations.append({
                'type': 'monitor',
                'title': '👁️ ติดตามอย่างใกล้ชิด',
                'items': [
                    f"ลดขีดจำกัดเลข {item['number']} ({item['field']}) ลง 25%"
                    for item in medium_risk_items[:5]
                ]
            })
        
        # แนะนำการจัดการโดยรวม
        total_high_risk = len(high_risk_items)
        if total_high_risk > 5:
            recommendations.append({
                'type': 'strategic',
                'title': '📋 การจัดการเชิงกลยุทธ์',
                'items': [
                    f"มีเลขความเสี่ยงสูง {total_high_risk} เลข - ควรทบทวนนโยบายขีดจำกัด",
                    "พิจารณาปรับเกณฑ์การรับซื้อให้เข้มงวดขึ้น",
                    "เพิ่มการติดตามแบบ real-time"
                ]
            })
        
        return recommendations
    
    @staticmethod
    def get_number_risk_detail(field: str, number: str, batch_id: str) -> Dict:
        """ดูรายละเอียดความเสี่ยงของเลขเฉพาะตัว"""
        try:
            # ดึงข้อมูลพื้นฐาน
            base_data = RiskManagementService._get_base_data(batch_id)
            if not base_data['success']:
                return base_data
            
            # คำนวณความเสี่ยงของเลขนี้
            risk_analysis = RiskManagementService._calculate_comprehensive_risk(batch_id, base_data['grand_total'])
            number_risk = next((item for item in risk_analysis if item['field'] == field and item['number'] == number), None)
            
            if not number_risk:
                return {"success": False, "error": "ไม่พบข้อมูลเลขที่ระบุ"}
            
            # ดึงข้อมูลผู้ใช้ที่ซื้อเลขนี้
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
            ).group_by(User.id).order_by(desc(func.sum(OrderItem.amount))).all()
            
            user_list = []
            for user in user_details:
                user_pct = (float(user.total_amount) / number_risk['total_amount']) * 100
                user_list.append({
                    'username': user.username,
                    'name': user.name,
                    'total_amount': float(user.total_amount),
                    'order_count': user.order_count,
                    'avg_factor': round(float(user.avg_factor), 3),
                    'percentage': round(user_pct, 2)
                })
            
            # สร้างคำแนะนำเฉพาะเลขนี้
            specific_recommendations = []
            
            if number_risk['risk_level'] == 'HIGH':
                specific_recommendations.extend([
                    "🛑 หยุดรับซื้อเลขนี้ทันที",
                    "📞 แจ้งผู้บริหารระดับสูง",
                    "🔍 ตรวจสอบประวัติการซื้อย้อนหลัง"
                ])
            elif number_risk['risk_level'] == 'MEDIUM':
                specific_recommendations.extend([
                    "⚠️ ลดขีดจำกัดลง 50%",
                    "👁️ เพิ่มการติดตามทุก 30 นาที",
                    "📊 ตรวจสอบ pattern การซื้อ"
                ])
            
            if number_risk['user_concentration_pct'] > 50:
                specific_recommendations.append(f"⚡ ผู้ใช้คนเดียวซื้อ {number_risk['user_concentration_pct']:.1f}% - ควรตรวจสอบ")
            
            return {
                "success": True,
                "data": {
                    "number_risk": number_risk,
                    "user_details": user_list,
                    "recommendations": specific_recommendations,
                    "risk_components": {
                        "concentration": {
                            "value": number_risk['concentration_pct'],
                            "status": "HIGH" if number_risk['concentration_pct'] > 10 else "MEDIUM" if number_risk['concentration_pct'] > 5 else "LOW"
                        },
                        "factor": {
                            "value": number_risk['factor_risk_pct'],
                            "status": "HIGH" if number_risk['factor_risk_pct'] > 20 else "MEDIUM" if number_risk['factor_risk_pct'] > 10 else "LOW"
                        },
                        "user_concentration": {
                            "value": number_risk['user_concentration_pct'],
                            "status": "HIGH" if number_risk['user_concentration_pct'] > 60 else "MEDIUM" if number_risk['user_concentration_pct'] > 30 else "LOW"
                        }
                    }
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"เกิดข้อผิดพลาด: {str(e)}"}
