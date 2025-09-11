"""
Improved Validation Flow for LotoJung Order System
ปรับปรุง validation flow และ business logic ตามการวิเคราะห์

Key Improvements:
1. Simplified API structure
2. Better error handling
3. Optimized validation logic
4. Mobile-friendly response format
5. Enhanced limit processing
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Order, OrderItem, Rule, BlockedNumber, NumberTotal
from app.services.limit_service import LimitService
from app import db
from decimal import Decimal, InvalidOperation
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any

# Create improved API blueprint
improved_api_bp = Blueprint('improved_api', __name__, url_prefix='/api/v2')

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, code: str = 'VALIDATION_ERROR'):
        self.message = message
        self.code = code
        super().__init__(self.message)

class OrderValidator:
    """Improved order validation class"""
    
    def __init__(self):
        self.blocked_numbers = self._load_blocked_numbers()
        self.payout_rates = LimitService.get_base_payout_rates()
    
    def _load_blocked_numbers(self) -> Dict[str, List[str]]:
        """Load blocked numbers from database"""
        blocked = {}
        for field in ['2_top', '2_bottom', '3_top', 'tote']:
            blocked_nums = BlockedNumber.query.filter_by(
                field=field, 
                is_active=True
            ).all()
            blocked[field] = [b.number_norm for b in blocked_nums]
        return blocked
    
    def validate_number_format(self, number: str) -> Tuple[bool, str, List[str]]:
        """
        Validate number format and determine applicable fields
        
        Returns:
            (is_valid, normalized_number, applicable_fields)
        """
        if not number or not number.strip():
            return False, '', []
        
        clean_number = ''.join(filter(str.isdigit, number.strip()))
        
        if len(clean_number) == 2:
            return True, clean_number, ['2_top', '2_bottom']
        elif len(clean_number) == 3:
            return True, clean_number, ['3_top', 'tote']
        else:
            return False, '', []
    
    def validate_amount(self, amount: str) -> Tuple[bool, Decimal]:
        """Validate amount format"""
        try:
            if not amount or not amount.strip():
                return True, Decimal('0')
            
            amount_decimal = Decimal(str(amount.strip()))
            if amount_decimal < 0:
                return False, Decimal('0')
            
            return True, amount_decimal
        except (InvalidOperation, ValueError):
            return False, Decimal('0')
    
    def check_blocked_status(self, number: str, field: str) -> bool:
        """Check if number is blocked for specific field"""
        return number in self.blocked_numbers.get(field, [])
    
    def validate_single_item(self, item_data: Dict) -> Dict[str, Any]:
        """
        Validate single order item with improved logic
        
        Args:
            item_data: {
                'number': str,
                'amount_top': str,
                'amount_bottom': str, 
                'amount_tote': str
            }
        
        Returns:
            Validation result dictionary
        """
        result = {
            'number': item_data.get('number', ''),
            'status': 'success',
            'message': 'ตรวจสอบเรียบร้อย',
            'details': [],
            'total_amount': Decimal('0'),
            'has_blocked': False,
            'has_warning': False
        }
        
        # Validate number format
        number = item_data.get('number', '').strip()
        is_valid, normalized_number, applicable_fields = self.validate_number_format(number)
        
        if not is_valid:
            result.update({
                'status': 'error',
                'message': 'รูปแบบเลขไม่ถูกต้อง (ต้องเป็น 2-3 หลัก)'
            })
            return result
        
        result['normalized_number'] = normalized_number
        
        # Validate amounts
        amounts = {
            'top': item_data.get('amount_top', '0'),
            'bottom': item_data.get('amount_bottom', '0'),
            'tote': item_data.get('amount_tote', '0')
        }
        
        validated_amounts = {}
        for key, amount_str in amounts.items():
            is_valid_amount, amount_decimal = self.validate_amount(amount_str)
            if not is_valid_amount:
                result.update({
                    'status': 'error',
                    'message': f'จำนวนเงิน{key}ไม่ถูกต้อง'
                })
                return result
            validated_amounts[key] = amount_decimal
        
        # Check if any amount > 0
        total_amount = sum(validated_amounts.values())
        if total_amount <= 0:
            result.update({
                'status': 'warning',
                'message': 'ไม่มีจำนวนเงินที่จะซื้อ'
            })
            return result
        
        result['total_amount'] = total_amount
        
        # Validate each field with amount > 0
        field_mapping = {
            'top': '3_top' if len(normalized_number) == 3 else '2_top',
            'bottom': '2_bottom' if len(normalized_number) == 2 else None,
            'tote': 'tote' if len(normalized_number) == 3 else None
        }
        
        for amount_key, field in field_mapping.items():
            if field and validated_amounts[amount_key] > 0:
                detail = self._validate_field_amount(
                    normalized_number, 
                    field, 
                    validated_amounts[amount_key]
                )
                result['details'].append(detail)
                
                if detail['is_blocked']:
                    result['has_blocked'] = True
                if detail['status_class'] == 'warning':
                    result['has_warning'] = True
        
        # Update overall status
        if result['has_blocked']:
            result['status'] = 'blocked'
            result['message'] = 'มีเลขอั้น'
        elif result['has_warning']:
            result['status'] = 'warning'
            result['message'] = 'มีการจ่ายลดลง'
        
        return result
    
    def _validate_field_amount(self, number: str, field: str, amount: Decimal) -> Dict[str, Any]:
        """Validate specific field amount"""
        batch_id = LimitService._get_current_batch_id()
        
        # Check blocked status
        is_blocked = self.check_blocked_status(number, field)
        
        # Get current usage and limit
        current_usage = LimitService.get_current_usage(field, number, batch_id)
        limit = LimitService.get_individual_limit(field, number)
        
        # Calculate new total
        new_total = current_usage + amount
        
        # Determine payout factor and reason
        payout_factor = 1.0
        reason = 'ปกติ'
        status_class = 'success'
        
        if is_blocked:
            payout_factor = 0.5
            reason = 'เลขอั้น - จ่ายครึ่งเท่า'
            status_class = 'blocked'
        elif new_total > limit:
            payout_factor = 0.5
            reason = 'เกินขีดจำกัด - จ่ายครึ่งเท่า'
            status_class = 'warning'
        
        # Calculate payout
        base_payout = amount * self.payout_rates.get(field, 0)
        actual_payout = base_payout * Decimal(str(payout_factor))
        
        return {
            'field': field,
            'field_display': self._get_field_display_name(field),
            'amount': float(amount),
            'current_usage': float(current_usage),
            'new_total': float(new_total),
            'limit': float(limit),
            'is_blocked': is_blocked,
            'payout_factor': payout_factor,
            'reason': reason,
            'status_class': status_class,
            'estimated_payout': float(actual_payout)
        }
    
    def _get_field_display_name(self, field: str) -> str:
        """Get display name for field"""
        field_names = {
            '2_top': '2 ตัวบน',
            '2_bottom': '2 ตัวล่าง', 
            '3_top': '3 ตัวบน',
            'tote': 'โต๊ด'
        }
        return field_names.get(field, field)

class OrderProcessor:
    """Improved order processing class"""
    
    def __init__(self):
        self.validator = OrderValidator()
    
    def process_limit_adjustments(self, validated_items: List[Dict]) -> Dict[str, Any]:
        """
        Process limit adjustments for validated items
        
        This simulates the limit processing that happens during actual order submission
        """
        batch_id = LimitService._get_current_batch_id()
        adjustments = []
        total_original = Decimal('0')
        total_adjusted = Decimal('0')
        
        for item in validated_items:
            if item['status'] == 'error':
                continue
                
            number = item['normalized_number']
            original_amount = item['total_amount']
            total_original += original_amount
            
            # Simulate limit checking for each field
            item_adjustments = []
            item_adjusted_amount = Decimal('0')
            
            for detail in item['details']:
                field = detail['field']
                amount = Decimal(str(detail['amount']))
                
                # Get current usage (simulate real-time data)
                current_usage = LimitService.get_current_usage(field, number, batch_id)
                limit = LimitService.get_individual_limit(field, number)
                
                # Calculate maximum allowed amount
                available_limit = max(Decimal('0'), limit - current_usage)
                adjusted_amount = min(amount, available_limit)
                
                if adjusted_amount < amount:
                    refund = amount - adjusted_amount
                    item_adjustments.append({
                        'field': field,
                        'field_display': detail['field_display'],
                        'original_amount': float(amount),
                        'adjusted_amount': float(adjusted_amount),
                        'refund': float(refund),
                        'reason': 'เกินขีดจำกัด'
                    })
                
                item_adjusted_amount += adjusted_amount
            
            if item_adjustments:
                adjustments.append({
                    'number': number,
                    'original_amount': float(original_amount),
                    'adjusted_amount': float(item_adjusted_amount),
                    'total_refund': float(original_amount - item_adjusted_amount),
                    'field_adjustments': item_adjustments
                })
            
            total_adjusted += item_adjusted_amount
        
        return {
            'total_original': float(total_original),
            'total_adjusted': float(total_adjusted),
            'total_refund': float(total_original - total_adjusted),
            'adjustments': adjustments,
            'has_adjustments': len(adjustments) > 0
        }

# API Endpoints

@improved_api_bp.route('/validate_order', methods=['POST'])
@login_required
def validate_order():
    """
    Unified validation endpoint for both single and bulk orders
    
    Request format:
    {
        "items": [
            {
                "number": "12",
                "amount_top": "500",
                "amount_bottom": "200", 
                "amount_tote": "0"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                'success': False,
                'error': 'ข้อมูลไม่ถูกต้อง: ต้องมี items'
            }), 400
        
        items = data['items']
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({
                'success': False,
                'error': 'ต้องมีรายการอย่างน้อย 1 รายการ'
            }), 400
        
        if len(items) > 20:
            return jsonify({
                'success': False,
                'error': 'รายการเกินจำนวนสูงสุด 20 รายการ'
            }), 400
        
        # Validate all items
        validator = OrderValidator()
        validation_results = []
        summary = {
            'total_items': 0,
            'valid_items': 0,
            'blocked_items': 0,
            'warning_items': 0,
            'error_items': 0,
            'total_amount': Decimal('0'),
            'estimated_payout': Decimal('0')
        }
        
        for item_data in items:
            result = validator.validate_single_item(item_data)
            validation_results.append(result)
            
            summary['total_items'] += 1
            
            if result['status'] == 'success':
                summary['valid_items'] += 1
            elif result['status'] == 'blocked':
                summary['blocked_items'] += 1
            elif result['status'] == 'warning':
                summary['warning_items'] += 1
            elif result['status'] == 'error':
                summary['error_items'] += 1
            
            if result['status'] != 'error':
                summary['total_amount'] += result['total_amount']
                
                # Calculate estimated payout
                for detail in result.get('details', []):
                    summary['estimated_payout'] += Decimal(str(detail['estimated_payout']))
        
        # Convert Decimal to float for JSON serialization
        summary_json = {
            **summary,
            'total_amount': float(summary['total_amount']),
            'estimated_payout': float(summary['estimated_payout'])
        }
        
        # Convert validation results for JSON
        results_json = []
        for result in validation_results:
            result_copy = result.copy()
            result_copy['total_amount'] = float(result['total_amount'])
            results_json.append(result_copy)
        
        return jsonify({
            'success': True,
            'validation_results': results_json,
            'summary': summary_json,
            'batch_id': LimitService._get_current_batch_id(),
            'validated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500

@improved_api_bp.route('/submit_order', methods=['POST'])
@login_required
def submit_order():
    """
    Submit order with limit processing
    
    Request format:
    {
        "customer_name": "ชื่อลูกค้า",
        "items": [...],  // Same format as validate_order
        "validation_token": "token_from_validation"  // Optional for extra security
    }
    """
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                'success': False,
                'error': 'ข้อมูลไม่ถูกต้อง'
            }), 400
        
        # Re-validate items (security measure)
        validator = OrderValidator()
        processor = OrderProcessor()
        
        validated_items = []
        for item_data in data['items']:
            result = validator.validate_single_item(item_data)
            if result['status'] != 'error':
                validated_items.append(result)
        
        if not validated_items:
            return jsonify({
                'success': False,
                'error': 'ไม่มีรายการที่ถูกต้อง'
            }), 400
        
        # Process limit adjustments
        limit_results = processor.process_limit_adjustments(validated_items)
        
        # Generate order (simulation)
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # In real implementation, this would save to database
        # order = Order(...)
        # db.session.add(order)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'customer_name': data.get('customer_name', ''),
            'total_amount': limit_results['total_adjusted'],
            'limit_processing': limit_results,
            'created_at': datetime.now().isoformat(),
            'message': 'สั่งซื้อสำเร็จ' + (' (มีการปรับยอดตาม limit)' if limit_results['has_adjustments'] else '')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการสั่งซื้อ: {str(e)}'
        }), 500

@improved_api_bp.route('/blocked_numbers', methods=['GET'])
@login_required
def get_blocked_numbers():
    """Get all blocked numbers for real-time validation"""
    try:
        validator = OrderValidator()
        return jsonify({
            'success': True,
            'blocked_numbers': validator.blocked_numbers,
            'updated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500

@improved_api_bp.route('/payout_rates', methods=['GET'])
@login_required
def get_payout_rates():
    """Get current payout rates"""
    try:
        rates = LimitService.get_base_payout_rates()
        return jsonify({
            'success': True,
            'payout_rates': rates,
            'updated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500

# Error handlers
@improved_api_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({
        'success': False,
        'error': error.message,
        'code': error.code
    }), 400

@improved_api_bp.errorhandler(404)
def handle_not_found(error):
    return jsonify({
        'success': False,
        'error': 'ไม่พบ endpoint ที่ร้องขอ'
    }), 404

@improved_api_bp.errorhandler(500)
def handle_internal_error(error):
    return jsonify({
        'success': False,
        'error': 'เกิดข้อผิดพลาดภายในระบบ'
    }), 500

# Usage example for integration:
"""
# In app/__init__.py, register the improved blueprint:

from app.routes.improved_validation_flow import improved_api_bp
app.register_blueprint(improved_api_bp)

# Frontend JavaScript can then use:

// Validate order
fetch('/api/v2/validate_order', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        items: [
            {
                number: '12',
                amount_top: '500',
                amount_bottom: '200',
                amount_tote: '0'
            }
        ]
    })
})

// Submit order  
fetch('/api/v2/submit_order', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        customer_name: 'ลูกค้า A',
        items: [...]
    })
})
"""

