from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Order, OrderItem, Rule, BlockedNumber, NumberTotal
from app.services.limit_service import LimitService
from app import db
from decimal import Decimal, InvalidOperation
import json
import uuid
from datetime import datetime, date

api_bp = Blueprint('api', __name__)

def get_base_payout_rate(field):
    """Get base payout rate for a field from database"""
    try:
        payout_rates = LimitService.get_base_payout_rates()
        return payout_rates.get(field, 0)
    except Exception:
        # Fallback default rates
        default_rates = {
            '2_top': 90,
            '2_bottom': 90,
            '3_top': 900,
            'tote': 150
        }
        return default_rates.get(field, 0)

@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@api_bp.route('/rules/<field>')
@login_required
def get_rules(field):
    """Get rules for a specific field"""
    payout_rule = Rule.query.filter_by(
        rule_type='payout', 
        field=field, 
        is_active=True
    ).first()
    
    limit_rule = Rule.query.filter_by(
        rule_type='limit', 
        field=field, 
        is_active=True
    ).first()
    
    return jsonify({
        'payout_rate': float(payout_rule.value) if payout_rule else 0,
        'limit': float(limit_rule.value) if limit_rule else 0
    })

@api_bp.route('/blocked_numbers/<field>')
@login_required
def get_blocked_numbers(field):
    """Get blocked numbers for a specific field"""
    blocked = BlockedNumber.query.filter_by(
        field=field, 
        is_active=True
    ).all()
    
    return jsonify({
        'blocked_numbers': [b.number_norm for b in blocked]
    })

@api_bp.route('/number_totals/<field>/<number>')
@login_required
def get_number_total(field, number):
    """Get current total for a specific number"""
    # Get current batch_id (this would be calculated based on lottery period)
    batch_id = "20240901"  # Placeholder
    
    total = NumberTotal.query.filter_by(
        batch_id=batch_id,
        field=field,
        number_norm=number
    ).first()
    
    return jsonify({
        'current_total': float(total.total_amount) if total else 0,
        'order_count': total.order_count if total else 0
    })

@api_bp.route('/validate_bulk_order', methods=['POST'])
@login_required
def validate_bulk_order():
    """
    Comprehensive validation for bulk order
    Returns current totals, limits, and validation results for each item
    """
    try:
        data = request.get_json()
        print(f"DEBUG BULK: Raw request data: {request.data}")  # Debug raw data
        print(f"DEBUG BULK: Parsed JSON data: {data}")  # Debug log
        
        if not data:
            print("DEBUG BULK: No JSON data received")  # Debug log
            return jsonify({
                'success': False,
                'error': 'No JSON data received'
            }), 400
            
        if 'orders' not in data:
            print(f"DEBUG BULK: Missing orders key. Keys: {list(data.keys()) if data else 'None'}")  # Debug log
            return jsonify({
                'success': False,
                'error': 'Missing orders key'
            }), 400
        
        orders = data['orders']
        print(f"DEBUG BULK: Number of orders: {len(orders)}")  # Debug log
        batch_id = LimitService._get_current_batch_id()
        
        validation_results = []
        summary = {
            'total_amount': Decimal('0'),
            'total_items': 0,
            'normal_payout_items': 0,
            'reduced_payout_items': 0,
            'blocked_items': 0,
            'over_limit_items': 0,
            'estimated_payout': Decimal('0')
        }
        
        # Payout rates from database
        payout_rates = LimitService.get_base_payout_rates()
        
        for order in orders:
            number = order.get('number', '').strip()
            amount_2_top = Decimal(str(order.get('amount_2_top', 0)))
            amount_2_bottom = Decimal(str(order.get('amount_2_bottom', 0)))
            amount_tote = Decimal(str(order.get('amount_tote', 0)))
            
            # Validate number format
            clean_number = ''.join(filter(str.isdigit, number))
            if not clean_number or len(clean_number) not in [2, 3]:
                validation_results.append({
                    'number': number,
                    'status': 'error',
                    'message': 'รูปแบบเลขไม่ถูกต้อง',
                    'details': []
                })
                continue
            
            row_result = {
                'number': number,
                'status': 'success',
                'message': 'ตรวจสอบเรียบร้อย',
                'details': [],
                'total_amount': Decimal('0'),
                'estimated_payout': Decimal('0')
            }
            
            # Check each field that has amount > 0
            fields_to_check = []
            
            if len(clean_number) == 2:
                # 2 digits: can buy 2_top and 2_bottom
                if amount_2_top > 0:
                    fields_to_check.append(('2_top', amount_2_top))
                if amount_2_bottom > 0:
                    fields_to_check.append(('2_bottom', amount_2_bottom))
            elif len(clean_number) == 3:
                # 3 digits: can buy 3_top (mapped from amount_2_top) and tote
                if amount_2_top > 0:  # For 3 digits, "ซื้อบน" means 3_top
                    fields_to_check.append(('3_top', amount_2_top))
                if amount_tote > 0:
                    fields_to_check.append(('tote', amount_tote))
            
            if not fields_to_check:
                validation_results.append({
                    'number': number,
                    'status': 'warning',
                    'message': 'ไม่มีจำนวนเงินที่จะซื้อ',
                    'details': []
                })
                continue
            
            # Validate each field
            for field, amount in fields_to_check:
                # ⭐ แก้ไข: สำหรับโต๊ด ต้องใช้ normalized number ในการตรวจสอบ limits
                lookup_number = clean_number
                if field == 'tote' and len(clean_number) == 3:
                    # สำหรับโต๊ด: เรียงหลักจากเล็กไปใหญ่ (123, 231, 312 → 123)
                    from app.utils.number_utils import generate_tote_number
                    lookup_number = generate_tote_number(clean_number)
                
                # Get current usage and limits
                current_usage = LimitService.get_current_usage(field, lookup_number, batch_id)
                limit = LimitService.get_individual_limit(field, lookup_number)
                is_blocked = LimitService.is_blocked_number(field, lookup_number)
                
                # Calculate new total after this purchase
                new_total = current_usage + amount
                
                # Determine payout rate
                payout_rate = 1.0
                reason = 'ปกติ'
                status_class = 'success'
                
                if is_blocked:
                    payout_rate = 0.5
                    reason = 'เลขอั้น - จ่ายครึ่งเท่า'
                    status_class = 'warning'
                    summary['blocked_items'] += 1
                elif new_total > limit:
                    payout_rate = 0.5
                    reason = 'มียอดซื้อเกินโควต้า - จ่ายครึ่งเท่า'
                    status_class = 'warning'
                    summary['over_limit_items'] += 1
                else:
                    summary['normal_payout_items'] += 1
                
                # Calculate payout
                base_payout = amount * payout_rates[field]
                actual_payout = base_payout * Decimal(str(payout_rate))
                
                # Add to row details
                field_display = LimitService._get_field_display_name(field)
                row_result['details'].append({
                    'field': field,
                    'field_display': field_display,
                    'amount': float(amount),
                    'current_usage': float(current_usage),
                    'new_total': float(new_total),
                    'limit': float(limit),
                    'is_blocked': is_blocked,
                    'payout_rate': payout_rate,
                    'reason': reason,
                    'status_class': status_class,
                    'estimated_payout': float(actual_payout)
                })
                
                # Add to row totals
                row_result['total_amount'] += amount
                row_result['estimated_payout'] += actual_payout
                
                # Add to summary
                summary['total_amount'] += amount
                summary['estimated_payout'] += actual_payout
                summary['total_items'] += 1
                
                if payout_rate < 1.0:
                    summary['reduced_payout_items'] += 1
            
            # Set row status based on details
            if any(d['status_class'] == 'warning' for d in row_result['details']):
                row_result['status'] = 'warning'
                row_result['message'] = 'มีการจ่ายลดลง'
            
            validation_results.append(row_result)
        
        return jsonify({
            'success': True,
            'validation_results': [
                {
                    **result,
                    'total_amount': float(result['total_amount']),
                    'estimated_payout': float(result['estimated_payout'])
                } for result in validation_results
            ],
            'summary': {
                **summary,
                'total_amount': float(summary['total_amount']),
                'estimated_payout': float(summary['estimated_payout'])
            },
            'batch_id': batch_id,
            'validated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"DEBUG BULK: Exception occurred: {str(e)}")  # Debug log
        print(f"DEBUG BULK: Exception type: {type(e).__name__}")  # Debug log
        import traceback
        print(f"DEBUG BULK: Traceback: {traceback.format_exc()}")  # Debug log
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}'
        }), 500

@api_bp.route('/validate_single_item', methods=['POST'])
@login_required 
def validate_single_item():
    """
    Validate single order item
    Returns current usage, limits, and payout calculation
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'ไม่มีข้อมูลที่ส่งมา'
            }), 400
        
        print(f"DEBUG: Received data: {data}")  # Debug log
        
        number = data.get('number', '').strip()
        amount_2_top = Decimal(str(data.get('amount_2_top', 0)))
        amount_2_bottom = Decimal(str(data.get('amount_2_bottom', 0)))
        amount_tote = Decimal(str(data.get('amount_tote', 0)))
        
        print(f"DEBUG: Parsed - number: {number}, top: {amount_2_top}, bottom: {amount_2_bottom}, tote: {amount_tote}")
        
        # Validate number format
        clean_number = ''.join(filter(str.isdigit, number))
        if not clean_number or len(clean_number) not in [2, 3]:
            return jsonify({
                'success': False,
                'error': 'รูปแบบเลขไม่ถูกต้อง'
            }), 400
        
        batch_id = LimitService._get_current_batch_id()
        
        # Determine which fields to check
        fields_to_check = []
        if len(clean_number) == 2:
            if amount_2_top > 0:
                fields_to_check.append(('2_top', amount_2_top))
            if amount_2_bottom > 0:
                fields_to_check.append(('2_bottom', amount_2_bottom))
        elif len(clean_number) == 3:
            if amount_2_top > 0:
                fields_to_check.append(('3_top', amount_2_top))
            if amount_tote > 0:
                fields_to_check.append(('tote', amount_tote))
        
        if not fields_to_check:
            return jsonify({
                'success': False,
                'error': 'ไม่มีจำนวนเงินที่จะซื้อ'
            }), 400
        
        # Validate and calculate for each field
        results = []
        for field, amount in fields_to_check:
            # ⭐ แก้ไข: สำหรับโต๊ด ต้องใช้ normalized number ในการตรวจสอบ limits
            lookup_number = clean_number
            if field == 'tote' and len(clean_number) == 3:
                # สำหรับโต๊ด: เรียงหลักจากเล็กไปใหญ่ (123, 231, 312 → 123)
                from app.utils.number_utils import generate_tote_number
                lookup_number = generate_tote_number(clean_number)
            
            validation = LimitService.validate_order_item(field, lookup_number, amount, batch_id)
            
            # Add display information
            validation['field_display'] = LimitService._get_field_display_name(field)
            validation['amount'] = float(amount)
            validation['current_usage'] = float(validation['current_usage'])
            validation['limit'] = float(validation['limit'])
            
            results.append(validation)
        
        return jsonify({
            'success': True,
            'number': number,
            'clean_number': clean_number,
            'results': results,
            'batch_id': batch_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}'
        }), 500

@api_bp.route('/get_current_totals/<field>/<number>')
@login_required
def get_current_totals(field, number):
    """
    Get current sales totals for specific number and field
    Includes breakdown by time periods
    """
    try:
        clean_number = ''.join(filter(str.isdigit, number))
        batch_id = LimitService._get_current_batch_id()
        
        # Get current usage
        current_usage = LimitService.get_current_usage(field, clean_number, batch_id)
        limit = LimitService.get_individual_limit(field, clean_number)
        default_limit = LimitService.get_default_group_limits().get(field, Decimal('0'))
        is_blocked = LimitService.is_blocked_number(field, clean_number)
        
        # Get detailed breakdown (if needed)
        total_record = NumberTotal.query.filter(
            NumberTotal.batch_id == batch_id,
            NumberTotal.field == field,
            NumberTotal.number_norm == clean_number
        ).first()
        
        return jsonify({
            'success': True,
            'field': field,
            'field_display': LimitService._get_field_display_name(field),
            'number': clean_number,
            'current_usage': float(current_usage),
            'limit': float(limit),
            'default_limit': float(default_limit),
            'remaining': float(limit - current_usage),
            'usage_percent': float((current_usage / limit * 100)) if limit > 0 else 0,
            'is_blocked': is_blocked,
            'order_count': total_record.order_count if total_record else 0,
            'batch_id': batch_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}'
        }), 500

@api_bp.route('/submit_bulk_order', methods=['POST'])
@login_required
def submit_bulk_order():
    """
    Submit bulk order with validation factors
    Records validation factors for external payout calculation
    """
    try:
        data = request.get_json()
        
        if not data or 'orders' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request data'
            }), 400
        
        orders = data['orders']
        customer_name = data.get('customer_name', '').strip()
        batch_id = LimitService._get_current_batch_id()
        
        # Get base payout rates for calculation
        payout_rates = LimitService.get_base_payout_rates()
        
        # Re-validate before submission to ensure data integrity
        validation_response = validate_bulk_order_internal(orders, batch_id)
        if not validation_response['success']:
            return jsonify(validation_response), 400
        
        validation_results = validation_response['validation_results']
        
        # Create main order record
        total_amount = sum(
            sum(detail['amount'] for detail in result['details'])
            for result in validation_results
            if result['status'] != 'error'
        )
        
        # Generate unique order number
        order_number = f"ORD{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Set lottery period (default to today)
        lottery_period = date.today()
        
        new_order = Order(
            order_number=order_number,
            user_id=current_user.id,
            customer_name=customer_name,
            total_amount=Decimal(str(total_amount)),
            batch_id=batch_id,
            lottery_period=lottery_period,
            status='confirmed'
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get order ID
        
        # Create order items with validation factors
        # ⭐ แก้ปัญหา UNIQUE constraint: รวมยอด tote ที่ normalize เหมือนกันก่อน
        consolidated_items = {}  # Key: (field, number_norm), Value: item_data
        
        for result in validation_results:
            if result['status'] == 'error':
                continue
                
            clean_number = ''.join(filter(str.isdigit, result['number']))
            
            for detail in result['details']:
                # ⭐ แก้ไข: สำหรับโต๊ด ต้องใช้ tote normalization (เรียงหลักจากเล็กไปใหญ่)
                normalized_number = clean_number
                if detail['field'] == 'tote' and len(clean_number) == 3:
                    # สำหรับโต๊ด: เรียงหลักจากเล็กไปใหญ่ (123, 231, 312 → 123)
                    from app.utils.number_utils import generate_tote_number
                    normalized_number = generate_tote_number(clean_number)
                
                # สร้าง key สำหรับ consolidation
                key = (detail['field'], normalized_number)
                
                # Calculate actual payout for this item
                base_payout = Decimal(str(detail['amount'])) * payout_rates[detail['field']]
                actual_payout = base_payout * Decimal(str(detail['payout_rate']))
                
                if key in consolidated_items:
                    # รวมยอดกับรายการที่มีอยู่แล้ว
                    existing = consolidated_items[key]
                    existing['amount'] += Decimal(str(detail['amount']))
                    existing['potential_payout'] += actual_payout
                    # เก็บหมายเลขทั้งหมดที่รวมมา (สำหรับ display)
                    existing['numbers'].append(result['number'])
                    existing['details'].append(detail)
                else:
                    # สร้างรายการใหม่
                    consolidated_items[key] = {
                        'field': detail['field'],
                        'number_norm': normalized_number,
                        'amount': Decimal(str(detail['amount'])),
                        'potential_payout': actual_payout,
                        'validation_factor': Decimal(str(detail['payout_rate'])),
                        'validation_reason': detail['reason'],
                        'current_usage_at_time': Decimal(str(detail['current_usage'])),
                        'limit_at_time': Decimal(str(detail['limit'])),
                        'is_blocked': detail['is_blocked'],
                        'numbers': [result['number']],  # เก็บหมายเลขต้นฉบับทั้งหมด
                        'details': [detail]
                    }
        
        # สร้าง OrderItem จาก consolidated data
        order_items = []
        for (field, number_norm), item_data in consolidated_items.items():
            # สำหรับ display: ใช้หมายเลขแรกหรือรวมหมายเลข
            display_numbers = ', '.join(item_data['numbers'])
            
            order_item = OrderItem(
                order_id=new_order.id,
                number=display_numbers,  # new field - แสดงหมายเลขทั้งหมดที่รวมมา
                number_input=display_numbers,  # legacy field (NOT NULL)
                number_norm=number_norm,  # normalized number
                field=field,
                amount=item_data['amount'],  # new field - ยอดรวม
                buy_amount=item_data['amount'],  # legacy field (NOT NULL) - ยอดรวม
                validation_factor=item_data['validation_factor'],  # ⭐ สำคัญ!
                validation_reason=item_data['validation_reason'],
                current_usage_at_time=item_data['current_usage_at_time'],
                limit_at_time=item_data['limit_at_time'],
                is_blocked=item_data['is_blocked'],
                # ⭐ แก้ปัญหา: ใส่ค่าเริ่มต้นสำหรับ legacy fields (NOT NULL constraint)
                payout_rate=item_data['validation_factor'],  # ใช้ค่าเดียวกับ validation_factor
                potential_payout=item_data['potential_payout']  # คำนวณจากข้อมูลจริง
            )
            
            order_items.append(order_item)
            db.session.add(order_item)
        
        # Update NumberTotal for tracking
        for item in order_items:
            # Find or create NumberTotal record
            number_total = NumberTotal.query.filter(
                NumberTotal.batch_id == batch_id,
                NumberTotal.field == item.field,
                NumberTotal.number_norm == item.number_norm
            ).first()
            
            if number_total:
                number_total.total_amount += item.amount
                number_total.order_count += 1
            else:
                number_total = NumberTotal(
                    batch_id=batch_id,
                    field=item.field,
                    number_norm=item.number_norm,
                    total_amount=item.amount,
                    order_count=1
                )
                db.session.add(number_total)
        
        # Commit transaction
        db.session.commit()
        
        # Prepare response with validation factors for external calculation
        external_calculation_data = []
        
        for item in order_items:
            external_calculation_data.append({
                'order_item_id': item.id,
                'number': item.number,
                'field': item.field,
                'field_display': LimitService._get_field_display_name(item.field),
                'amount': float(item.amount),
                'validation_factor': float(item.validation_factor),  # ⭐ สำคัญ!
                'validation_reason': item.validation_reason,
                'for_external_calculation': {
                    'base_rate': get_base_payout_rate(item.field),
                    'suggested_payout': float(item.amount) * get_base_payout_rate(item.field) * float(item.validation_factor)
                }
            })
        
        return jsonify({
            'success': True,
            'message': 'บันทึกคำสั่งซื้อเรียบร้อย',
            'order_id': new_order.id,
            'total_amount': float(total_amount),
            'total_items': len(order_items),
            'customer_name': customer_name,
            'batch_id': batch_id,
            'external_calculation_data': external_calculation_data,  # ⭐ สำหรับคำนวณภายนอก
            'validation_factors_recorded': True
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}'
        }), 500

def validate_bulk_order_internal(orders, batch_id):
    """Internal validation function for reuse"""
    validation_results = []
    
    for order in orders:
        number = order.get('number', '').strip()
        amount_2_top = Decimal(str(order.get('amount_2_top', 0)))
        amount_2_bottom = Decimal(str(order.get('amount_2_bottom', 0)))
        amount_tote = Decimal(str(order.get('amount_tote', 0)))
        
        # Validate number format
        clean_number = ''.join(filter(str.isdigit, number))
        if not clean_number or len(clean_number) not in [2, 3]:
            validation_results.append({
                'number': number,
                'status': 'error',
                'message': 'รูปแบบเลขไม่ถูกต้อง',
                'details': []
            })
            continue
        
        row_result = {
            'number': number,
            'status': 'success',
            'message': 'ตรวจสอบเรียบร้อย',
            'details': []
        }
        
        # Check each field that has amount > 0
        fields_to_check = []
        
        if len(clean_number) == 2:
            if amount_2_top > 0:
                fields_to_check.append(('2_top', amount_2_top))
            if amount_2_bottom > 0:
                fields_to_check.append(('2_bottom', amount_2_bottom))
        elif len(clean_number) == 3:
            if amount_2_top > 0:
                fields_to_check.append(('3_top', amount_2_top))
            if amount_tote > 0:
                fields_to_check.append(('tote', amount_tote))
        
        if not fields_to_check:
            validation_results.append({
                'number': number,
                'status': 'warning',
                'message': 'ไม่มีจำนวนเงินที่จะซื้อ',
                'details': []
            })
            continue
        
        # Validate each field
        for field, amount in fields_to_check:
            current_usage = LimitService.get_current_usage(field, clean_number, batch_id)
            limit = LimitService.get_individual_limit(field, clean_number)
            is_blocked = LimitService.is_blocked_number(field, clean_number)
            
            new_total = current_usage + amount
            
            # Determine validation factor
            payout_rate = 1.0
            reason = 'ปกติ'
            
            if is_blocked:
                payout_rate = 0.5
                reason = 'เลขอั้น - Factor 0.5x'
            elif new_total > limit:
                payout_rate = 0.5
                reason = 'มียอดซื้อเกินโควต้า - Factor 0.5x'
            
            row_result['details'].append({
                'field': field,
                'field_display': LimitService._get_field_display_name(field),
                'amount': float(amount),
                'current_usage': float(current_usage),
                'new_total': float(new_total),
                'limit': float(limit),
                'is_blocked': is_blocked,
                'payout_rate': payout_rate,  # ⭐ Validation Factor
                'reason': reason
            })
        
        validation_results.append(row_result)
    
    return {
        'success': True,
        'validation_results': validation_results
    }

def get_base_payout_rate(field):
    """Get base payout rate from database for external calculation reference"""
    return LimitService.get_base_payout_rate(field)

@api_bp.route('/get_payout_rates')
@login_required
def get_payout_rates():
    """Get all base payout rates from database"""
    try:
        rates = LimitService.get_base_payout_rates()
        return jsonify({
            'success': True,
            'rates': rates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการโหลดอัตราจ่าย: {str(e)}'
        }), 500

