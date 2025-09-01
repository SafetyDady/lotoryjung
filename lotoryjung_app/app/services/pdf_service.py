"""
PDF service for generating receipts
"""

import os
from typing import Optional
from datetime import datetime, timedelta
import secrets
import pytz

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app import db
from app.models import Order, DownloadToken
from app.utils.number_utils import format_currency

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class PDFService:
    """Service class for PDF operations"""
    
    @staticmethod
    def generate_receipt(order: Order) -> str:
        """
        Generate PDF receipt for order
        
        Args:
            order: Order object
        
        Returns:
            PDF file path
        """
        # Create receipts directory if not exists
        receipts_dir = os.path.join('static', 'receipts', str(order.user_id))
        os.makedirs(receipts_dir, exist_ok=True)
        
        # Generate filename
        filename = f"{order.order_number}.pdf"
        filepath = os.path.join(receipts_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 12
        
        # Title
        story.append(Paragraph("ใบสั่งซื้อหวย", title_style))
        story.append(Spacer(1, 12))
        
        # Order information
        order_info = [
            f"เลขที่ใบสั่งซื้อ: {order.order_number}",
            f"วันที่สั่งซื้อ: {order.created_at.strftime('%d/%m/%Y %H:%M:%S')}",
            f"งวดวันที่: {order.lottery_period.strftime('%d/%m/%Y')}",
            f"ชื่อลูกค้า: {order.customer_name or 'ไม่ระบุ'}",
            f"สถานะ: {PDFService._get_status_text(order.status)}"
        ]
        
        for info in order_info:
            story.append(Paragraph(info, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Order items table
        story.append(Paragraph("รายการสั่งซื้อ", header_style))
        
        # Table data
        table_data = [
            ['ประเภท', 'เลข', 'จำนวนเงิน', 'อัตราจ่าย', 'จ่ายได้สูงสุด']
        ]
        
        for item in order.items:
            table_data.append([
                PDFService._get_field_text(item.field),
                item.number_norm,
                format_currency(float(item.buy_amount)),
                f"{item.payout_rate:g}x",
                format_currency(float(item.potential_payout))
            ])
        
        # Add total row
        table_data.append([
            'รวม', '', format_currency(float(order.total_amount)), '', ''
        ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Notes
        if order.notes:
            story.append(Paragraph("หมายเหตุ", header_style))
            story.append(Paragraph(order.notes, normal_style))
            story.append(Spacer(1, 20))
        
        # Footer
        footer_text = [
            "** ใบสั่งซื้อนี้ไม่ใช่ใบเสร็จรับเงิน **",
            "กรุณาเก็บใบสั่งซื้อนี้ไว้เป็นหลักฐาน",
            f"พิมพ์เมื่อ: {datetime.now(BANGKOK_TZ).strftime('%d/%m/%Y %H:%M:%S')}"
        ]
        
        for text in footer_text:
            story.append(Paragraph(text, normal_style))
        
        # Build PDF
        doc.build(story)
        
        # Update order with PDF path
        order.pdf_path = filepath
        db.session.commit()
        
        return filepath
    
    @staticmethod
    def _get_field_text(field: str) -> str:
        """Get Thai text for field"""
        field_map = {
            '2_top': '2 ตัวบน',
            '2_bottom': '2 ตัวล่าง',
            '3_top': '3 ตัวบน',
            'tote': 'โต๊ด'
        }
        return field_map.get(field, field)
    
    @staticmethod
    def _get_status_text(status: str) -> str:
        """Get Thai text for status"""
        status_map = {
            'pending': 'รอดำเนินการ',
            'confirmed': 'ยืนยันแล้ว',
            'cancelled': 'ยกเลิก'
        }
        return status_map.get(status, status)
    
    @staticmethod
    def create_download_token(order_id: int, user_id: int, expires_hours: int = 24) -> str:
        """
        Create secure download token for PDF
        
        Args:
            order_id: Order ID
            user_id: User ID
            expires_hours: Token expiration hours
        
        Returns:
            Download token
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = datetime.now(BANGKOK_TZ) + timedelta(hours=expires_hours)
        
        # Create token record
        download_token = DownloadToken(
            token=token,
            order_id=order_id,
            user_id=user_id,
            expires_at=expires_at
        )
        
        db.session.add(download_token)
        db.session.commit()
        
        return token
    
    @staticmethod
    def validate_download_token(token: str, user_id: int) -> Optional[Order]:
        """
        Validate download token and return order
        
        Args:
            token: Download token
            user_id: User ID for authorization
        
        Returns:
            Order object if valid, None otherwise
        """
        download_token = DownloadToken.query.filter_by(
            token=token,
            user_id=user_id,
            is_used=False
        ).first()
        
        if not download_token:
            return None
        
        if download_token.is_expired():
            return None
        
        # Mark token as used
        download_token.is_used = True
        db.session.commit()
        
        return download_token.order
    
    @staticmethod
    def cleanup_expired_tokens():
        """Clean up expired download tokens"""
        expired_tokens = DownloadToken.query.filter(
            DownloadToken.expires_at < datetime.now(BANGKOK_TZ)
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        
        db.session.commit()
        
        return len(expired_tokens)

