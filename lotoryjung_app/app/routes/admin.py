from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, BooleanField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange
from functools import wraps
from decimal import Decimal
from sqlalchemy import func
from app.models import User, Order, OrderItem, Rule, BlockedNumber, AuditLog, NumberTotal
from app.utils.number_utils import (
    generate_blocked_numbers_for_field, 
    validate_bulk_numbers, 
    preview_bulk_blocked_numbers
)
from app.services.limit_service import LimitService
from app.services.reports_service import ReportsService
from app.services.risk_management_service import RiskManagementService
from app.services.order_service import OrderService
from app.services.simple_sales_service import SimpleSalesService
from app.services.sales_report_service import SalesReportService
from app import db

admin_bp = Blueprint('admin', __name__)

# Forms
class BlockedNumberForm(FlaskForm):
    field = SelectField('ประเภท', 
                       choices=[
                           ('2_top', '2 ตัวบน'),
                           ('2_bottom', '2 ตัวล่าง'),
                           ('3_top', '3 ตัวบน'),
                           ('tote', 'โต๊ด')
                       ],
                       validators=[DataRequired()])
    number_norm = StringField('หมายเลข', validators=[DataRequired(), Length(min=2, max=3)])
    reason = TextAreaField('เหตุผล', validators=[Length(max=255)])
    is_active = BooleanField('เปิดใช้งาน', default=True)
    submit = SubmitField('บันทึก')

class BulkBlockedNumberForm(FlaskForm):
    reason = TextAreaField('เหตุผลทั่วไป', validators=[Length(max=255)])
    is_active = BooleanField('เปิดใช้งานทั้งหมด', default=True)
    submit = SubmitField('บันทึกทั้งหมด')

class GroupLimitForm(FlaskForm):
    limit_2_top = DecimalField('ขีดจำกัด 2 ตัวบน (บาท)', 
                              validators=[DataRequired(), NumberRange(min=0)],
                              default=1000000)
    limit_2_bottom = DecimalField('ขีดจำกัด 2 ตัวล่าง (บาท)', 
                                 validators=[DataRequired(), NumberRange(min=0)],
                                 default=800000)
    limit_3_top = DecimalField('ขีดจำกัด 3 ตัวบน (บาท)', 
                              validators=[DataRequired(), NumberRange(min=0)],
                              default=500000)
    limit_tote = DecimalField('ขีดจำกัดโต๊ด (บาท)', 
                             validators=[DataRequired(), NumberRange(min=0)],
                             default=300000)
    submit = SubmitField('บันทึกการตั้งค่า')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def validate_bulk_numbers_new_format(numbers_data):
    """Validate bulk numbers data in new format (2_digit/3_digit type)"""
    errors = []
    valid_numbers = []
    
    for i, item in enumerate(numbers_data):
        if not isinstance(item, dict) or 'number' not in item or 'type' not in item:
            errors.append(f'รายการที่ {i+1}: รูปแบบข้อมูลไม่ถูกต้อง')
            continue
            
        number = str(item['number']).strip()
        number_type = item['type']
        
        if not number:
            errors.append(f'รายการที่ {i+1}: กรุณากรอกหมายเลข')
            continue
            
        if number_type not in ['2_digit', '3_digit']:
            errors.append(f'รายการที่ {i+1}: ประเภทไม่ถูกต้อง')
            continue
            
        # Validate number format
        if number_type == '2_digit':
            if not number.isdigit() or len(number) > 2 or len(number) < 1:
                errors.append(f'รายการที่ {i+1}: เลข 2 หลักต้องเป็นตัวเลข 1-2 หลัก')
                continue
        elif number_type == '3_digit':
            if not number.isdigit() or len(number) > 3 or len(number) < 1:
                errors.append(f'รายการที่ {i+1}: เลข 3 หลักต้องเป็นตัวเลข 1-3 หลัก')
                continue
        
        valid_numbers.append({
            'number': number,
            'type': number_type
        })
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'valid_numbers': valid_numbers
    }

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    try:
        # Get basic stats
        stats = {
            'total_orders': Order.query.count(),
            'total_amount': db.session.query(func.sum(Order.total_amount)).scalar() or 0,
            'total_users': User.query.count(),
            'blocked_numbers_count': BlockedNumber.query.filter(BlockedNumber.is_active == True).count()
        }
        
        # Get recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_orders=recent_orders)
    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}', 'error')
        # Return basic stats in case of error
        stats = {
            'total_orders': 0,
            'total_amount': 0,
            'total_users': 0,
            'blocked_numbers_count': 0
        }
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_orders=[])

@admin_bp.route('/blocked_numbers')
@login_required  
@admin_required
def blocked_numbers():
    """Blocked numbers list"""
    from flask_wtf import FlaskForm
    
    page = request.args.get('page', 1, type=int)
    field_filter = request.args.get('field', '')
    search = request.args.get('search', '')
    
    query = BlockedNumber.query
    
    if field_filter:
        query = query.filter_by(field=field_filter)
    
    if search:
        query = query.filter(BlockedNumber.number_norm.contains(search))
    
    blocked_numbers = query.order_by(BlockedNumber.created_at.desc())\
                          .paginate(page=page, per_page=100, error_out=False)
    
    # Get statistics
    stats = {
        'total': BlockedNumber.query.count(),
        'by_field': {}
    }
    
    field_counts = db.session.query(
        BlockedNumber.field,
        db.func.count(BlockedNumber.id)
    ).group_by(BlockedNumber.field).all()
    
    for field, count in field_counts:
        stats['by_field'][field] = count
    
    # DEBUG: Print info to console
    print(f"DEBUG blocked_numbers route:")
    print(f"  Total items: {len(blocked_numbers.items) if blocked_numbers else 'None'}")
    print(f"  Total pages: {blocked_numbers.total if blocked_numbers else 'None'}")
    print(f"  Stats: {stats}")
    if blocked_numbers and blocked_numbers.items:
        print(f"  First item: {blocked_numbers.items[0].field} - {blocked_numbers.items[0].number_norm}")
    
    # Create empty form for CSRF protection
    delete_form = FlaskForm()
    
    return render_template('admin/blocked_numbers.html', 
                         blocked_numbers=blocked_numbers,
                         field_filter=field_filter,
                         search=search,
                         stats=stats,
                         delete_form=delete_form)

@admin_bp.route('/blocked_numbers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_blocked_number():
    """Add new blocked number (single)"""
    form = BlockedNumberForm()
    
    if form.validate_on_submit():
        try:
            # Convert field to number_type
            number_str = str(form.number_norm.data).strip()
            if len(number_str) == 2:
                number_type = '2_digit'
            elif len(number_str) == 3:
                number_type = '3_digit'
            else:
                flash('เลขต้องเป็น 2 หรือ 3 หลัก', 'error')
                return render_template('admin/single_blocked_number_form.html', form=form, title='เพิ่มเลขอั้น')
            
            # Generate permutations
            records = generate_blocked_numbers_for_field(form.number_norm.data, number_type)
            
            for record in records:
                blocked_number = BlockedNumber(
                    field=record['field'],
                    number_norm=record['number_norm'],
                    reason=form.reason.data,
                    is_active=form.is_active.data
                )
                db.session.add(blocked_number)
            
            db.session.commit()
            flash(f'เพิ่มเลขอั้น {form.number_norm.data} เรียบร้อยแล้ว', 'success')
            return redirect(url_for('admin.blocked_numbers'))
            
        except Exception as e:
            db.session.rollback()
            flash('เกิดข้อผิดพลาดในการบันทึกข้อมูล', 'error')
    
    return render_template('admin/single_blocked_number_form.html', form=form, title='เพิ่มเลขอั้น')

@admin_bp.route('/blocked_numbers/bulk_add', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_add_blocked_numbers():
    """Bulk add blocked numbers with automatic permutation generation"""
    print(f"🎯 DEBUG: เข้า bulk_add_blocked_numbers route - method: {request.method}")
    
    form = BulkBlockedNumberForm()
    
    if request.method == 'POST':
        print(f"DEBUG BULK ADD POST:")
        print(f"  Content-Type: {request.content_type}")
        print(f"  Is JSON: {request.is_json}")
        print(f"  Form data keys: {list(request.form.keys())}")
        print(f"  Form validate: {form.validate_on_submit()}")
        
        if form.validate_on_submit():
            # Get numbers data from JSON
            numbers_data = request.get_json() if request.is_json else request.form.get('numbers_data')
            print(f"  Numbers data: {numbers_data}")
            
            if isinstance(numbers_data, str):
                import json
                try:
                    numbers_data = json.loads(numbers_data)
                    print(f"  Parsed JSON: {numbers_data}")
                except Exception as e:
                    print(f"  JSON parse error: {e}")
                    flash('ข้อมูลไม่ถูกต้อง', 'error')
                    return redirect(url_for('admin.bulk_add_blocked_numbers'))
        
        if isinstance(numbers_data, str):
            import json
            try:
                numbers_data = json.loads(numbers_data)
            except:
                flash('ข้อมูลไม่ถูกต้อง', 'error')
                return redirect(url_for('admin.bulk_add_blocked_numbers'))
        
        if not numbers_data or not isinstance(numbers_data, list):
            flash('กรุณากรอกข้อมูลเลขอั้น', 'error')
            return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้นหลายตัว')
        
        # Validate and process input data
        validation_result = validate_bulk_numbers_new_format(numbers_data)
        
        print(f"🔍 DEBUG VALIDATION:")
        print(f"  Input numbers_data: {numbers_data}")
        print(f"  Validation valid: {validation_result['valid']}")
        print(f"  Valid numbers: {validation_result['valid_numbers']}")
        print(f"  Errors: {validation_result['errors']}")
        
        if not validation_result['valid']:
            for error in validation_result['errors'][:5]:  # Show first 5 errors
                flash(error, 'error')
            return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้นหลายตัว')
        
        success_count = 0
        error_count = 0
        errors = []
        duplicate_count = 0
        
        try:
            # Clear all existing blocked numbers first
            deleted_count = BlockedNumber.query.delete()
            print(f"🗑️ DEBUG: ล้าง blocked numbers ทั้งหมด {deleted_count} รายการ")
            
            # Process each input number and generate all permutations
            all_records = []
            
            for item in validation_result['valid_numbers']:
                number = item['number']
                number_type = item['type']
                
                print(f"🎲 DEBUG PERMUTATION: {number} ({number_type})")
                
                # Generate permutations based on number type
                if number_type == '2_digit':
                    # For 2-digit, generate permutations for both 2_top and 2_bottom
                    records = generate_blocked_numbers_for_field(number, '2_digit')
                    print(f"  → Generated {len(records)} records for 2_digit: {[r['field'] + ':' + r['number_norm'] for r in records]}")
                    all_records.extend(records)
                elif number_type == '3_digit':
                    # For 3-digit, generate permutations for 3_top and tote
                    records = generate_blocked_numbers_for_field(number, '3_digit')
                    print(f"  → Generated {len(records)} records for 3_digit: {[r['field'] + ':' + r['number_norm'] for r in records]}")
                    all_records.extend(records)
            
            # Remove duplicates and apply global settings
            unique_records = []
            seen = set()
            
            print(f"📝 DEBUG UNIQUE FILTERING:")
            print(f"  Total records before filtering: {len(all_records)}")
            
            for record in all_records:
                key = (record['field'], record['number_norm'])
                if key not in seen:
                    seen.add(key)
                    # Apply global form settings
                    if form.reason.data:
                        record['reason'] = form.reason.data
                    record['is_active'] = form.is_active.data
                    unique_records.append(record)
                else:
                    print(f"  Skipping duplicate: {record['field']}:{record['number_norm']}")
            
            print(f"  Total unique records: {len(unique_records)}")
            print(f"  Unique records by field:")
            from collections import Counter
            field_counts = Counter([r['field'] for r in unique_records])
            for field, count in field_counts.items():
                print(f"    {field}: {count}")
            
            # Batch insert new records to database
            if unique_records:
                print(f"💾 DEBUG: เริ่มเพิ่ม {len(unique_records)} records ใหม่")
                for record in unique_records:
                    # ไม่ต้องเช็ค duplicate เพราะล้างไปแล้ว
                    try:
                        blocked_number = BlockedNumber(
                            field=record['field'],
                            number_norm=record['number_norm'],
                            reason=record.get('reason', ''),
                            is_active=record['is_active']
                        )
                        db.session.add(blocked_number)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"เลข {record['number_norm']}: {str(e)}")
                
                # Commit all changes (delete + insert)
                print(f"💾 DEBUG: Committing transaction...")
                db.session.commit()
                print(f"✅ DEBUG: Transaction committed สำเร็จ!")
        
        except Exception as e:
            print(f"❌ DEBUG: เกิด Exception: {str(e)}")
            print(f"❌ DEBUG: Type: {type(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}', 'error')
            return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้นหลายตัว')
        
        # Show results
        if success_count > 0:
            flash(f'✅ สำเร็จ! ล้างข้อมูลเก่า {deleted_count} รายการ และบันทึกข้อมูลใหม่ {success_count} รายการ', 'success')
            flash(f'📊 สถิติ: บันทึกจาก {len(validation_result["valid_numbers"])} เลขที่กรอก → สร้างเป็น {success_count} records ในฐานข้อมูล', 'info')
        
        # ไม่แสดง duplicate เพราะล้างไปแล้ว
        
        if error_count > 0:
            flash(f'⚠️ พบข้อผิดพลาด {error_count} รายการ', 'warning')
            for error in errors[:3]:  # Show first 3 errors
                flash(error, 'error')
        
        if success_count > 0:
            return redirect(url_for('admin.blocked_numbers'))
        
    print(f"🎯 DEBUG: bulk_add GET - แสดงฟอร์ม")
    return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้นหลายตัว')

@admin_bp.route('/blocked_numbers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blocked_number(id):
    """Edit blocked number"""
    blocked_number = BlockedNumber.query.get_or_404(id)
    form = BlockedNumberForm(obj=blocked_number)
    
    if form.validate_on_submit():
        try:
            blocked_number.field = form.field.data
            blocked_number.number_norm = form.number_norm.data
            blocked_number.reason = form.reason.data
            blocked_number.is_active = form.is_active.data
            
            db.session.commit()
            flash(f'แก้ไขเลขอั้น {blocked_number.number_norm} เรียบร้อยแล้ว', 'success')
            return redirect(url_for('admin.blocked_numbers'))
            
        except Exception as e:
            db.session.rollback()
            flash('เกิดข้อผิดพลาดในการบันทึกข้อมูล', 'error')
    
    return render_template('admin/bulk_blocked_number_form.html', 
                         form=form, 
                         blocked_number=blocked_number,
                         title='แก้ไขเลขอั้น')

@admin_bp.route('/blocked_numbers/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blocked_number(id):
    """Delete blocked number"""
    blocked_number = BlockedNumber.query.get_or_404(id)
    
    try:
        db.session.delete(blocked_number)
        db.session.commit()
        flash(f'ลบเลขอั้น {blocked_number.number_norm} เรียบร้อยแล้ว', 'success')
    except Exception as e:
        db.session.rollback()
        flash('เกิดข้อผิดพลาดในการลบข้อมูล', 'error')
    
    return redirect(url_for('admin.blocked_numbers'))


@admin_bp.route('/blocked_numbers/clear_all', methods=['POST'])
@login_required
@admin_required
def clear_all_blocked_numbers():
    """Clear all blocked numbers"""
    try:
        # Count before delete
        total_count = BlockedNumber.query.count()
        
        if total_count == 0:
            flash('ไม่มีข้อมูลเลขอั้นให้ลบ', 'info')
            return redirect(url_for('admin.blocked_numbers'))
        
        # Delete all records
        deleted_count = BlockedNumber.query.delete()
        db.session.commit()
        
        flash(f'🗑️ ล้างเลขอั้นทั้งหมดเรียบร้อย! ลบ {deleted_count} รายการ', 'success')
        flash('✅ ตอนนี้เลขทั้งหมดสามารถแทงได้แล้ว', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}', 'error')
    
    return redirect(url_for('admin.blocked_numbers'))

@admin_bp.route('/rules')
@login_required
@admin_required
def rules():
    """System rules"""
    return render_template('admin/rules.html')


@admin_bp.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    """Audit logs"""
    return render_template('admin/audit_logs.html')


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """System settings"""
    return render_template('admin/settings.html')


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management"""
    return render_template('admin/users.html')


# Group Limits Management
@admin_bp.route('/group_limits')
@login_required
@admin_required
def group_limits():
    """Group limits dashboard"""
    try:
        print("🎯 DEBUG: เข้า group_limits route")
        dashboard_data = LimitService.get_limits_dashboard_data()
        print(f"🎯 DEBUG: dashboard_data keys = {list(dashboard_data.keys())}")
        print(f"🎯 DEBUG: sample data = {list(dashboard_data.values())[0] if dashboard_data else 'No data'}")
        
        return render_template('admin/group_limits.html', 
                             dashboard_data=dashboard_data,
                             title='จัดการขีดจำกัดกลุ่มเลข')
    except Exception as e:
        print(f"🚨 ERROR in group_limits: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/group_limits/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_group_limits():
    """Edit group limits"""
    form = GroupLimitForm()
    
    if request.method == 'GET':
        # Load current limits
        current_limits = LimitService.get_default_group_limits()
        form.limit_2_top.data = current_limits.get('2_top', Decimal('700'))
        form.limit_2_bottom.data = current_limits.get('2_bottom', Decimal('600'))
        form.limit_3_top.data = current_limits.get('3_top', Decimal('500'))
        form.limit_tote.data = current_limits.get('tote', Decimal('400'))
    
    if form.validate_on_submit():
        try:
            # Update all limits
            updates = [
                ('2_top', form.limit_2_top.data),
                ('2_bottom', form.limit_2_bottom.data),
                ('3_top', form.limit_3_top.data),
                ('tote', form.limit_tote.data)
            ]
            
            success_count = 0
            for field, limit_value in updates:
                if LimitService.set_default_group_limit(field, limit_value):
                    success_count += 1
            
            if success_count == len(updates):
                flash('อัพเดตขีดจำกัดทั้งหมดเรียบร้อยแล้ว', 'success')
                return redirect(url_for('admin.group_limits'))
            else:
                flash(f'อัพเดตสำเร็จ {success_count}/{len(updates)} รายการ', 'warning')
                
        except Exception as e:
            flash(f'เกิดข้อผิดพลาดในการอัพเดต: {str(e)}', 'error')
    
    return render_template('admin/edit_group_limits.html', 
                          form=form,
                          title='แก้ไขขีดจำกัดกลุ่มเลข')


@admin_bp.route('/group_limits/api/dashboard_data')
@login_required
@admin_required
def api_group_limits_dashboard():
    """API endpoint for dashboard data (for AJAX updates)"""
    try:
        batch_id = request.args.get('batch_id')
        dashboard_data = LimitService.get_limits_dashboard_data(batch_id)
        return jsonify({
            'success': True,
            'data': {
                field: {
                    'field_name': data['field_name'],
                    'limit_amount': float(data['limit_amount']),
                    'used_amount': float(data['used_amount']),
                    'remaining_amount': float(data['remaining_amount']),
                    'usage_percent': data['usage_percent'],
                    'order_count': data['order_count'],
                    'number_count': data['number_count'],
                    'status': data['status'],
                    'is_exceeded': data['is_exceeded']
                }
                for field, data in dashboard_data.items()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/group_limits/api/validate_order', methods=['POST'])
@login_required
@admin_required
def api_validate_order_limits():
    """API endpoint to validate order against limits"""
    try:
        data = request.get_json()
        order_items = data.get('order_items', [])
        batch_id = data.get('batch_id')
        
        # Validate each order item
        results = []
        for item in order_items:
            validation = LimitService.validate_order_item(
                item['field'], 
                item['number_norm'], 
                item['buy_amount'], 
                batch_id
            )
            results.append(validation)
        
        # Check if any invalid
        is_valid = all(result['is_valid'] for result in results)
        errors = [result['reason'] for result in results if not result['is_valid']]
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'errors': errors,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/api/update_group_limit', methods=['POST'])
@login_required
@admin_required
def api_update_group_limit():
    """API endpoint to update group limit"""
    try:
        data = request.get_json()
        field = data.get('field')
        new_limit = Decimal(str(data.get('limit')))
        
        success = LimitService.set_default_group_limit(field, new_limit)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'อัปเดตขีดจำกัดเริ่มต้นสำหรับ {field} เรียบร้อยแล้ว'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'ไม่สามารถอัปเดตขีดจำกัดได้'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@admin_bp.route('/individual_limits')
@login_required
@admin_required
def individual_limits():
    """Individual number limits management page"""
    try:
        return render_template('admin/individual_limits.html')
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/payout_rates')
@login_required
@admin_required
def payout_rates():
    """Payout rates management page"""
    try:
        current_rates = LimitService.get_base_payout_rates()
        return render_template('admin/payout_rates.html', current_rates=current_rates)
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/api/set_individual_limit', methods=['POST'])
@login_required
@admin_required
def api_set_individual_limit():
    """API endpoint to set individual number limit"""
    try:
        # Debug: Log request details
        print(f"DEBUG: Content-Type: {request.content_type}")
        print(f"DEBUG: Request data: {request.get_data()}")
        
        data = request.get_json()
        print(f"DEBUG: Parsed JSON data: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'ไม่มีข้อมูลที่ส่งมา'
            }), 400
        
        field = data.get('field')
        number_norm = data.get('number_norm')
        limit_amount = data.get('limit_amount')
        
        # Validate required fields
        if not field or not number_norm or limit_amount is None:
            return jsonify({
                'success': False,
                'error': 'ข้อมูลไม่ครบถ้วน (field, number_norm, limit_amount)'
            }), 400
        
        try:
            limit_amount = Decimal(str(limit_amount))
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f'จำนวนเงินไม่ถูกต้อง: {str(e)}'
            }), 400
        
        success = LimitService.set_individual_limit(field, number_norm, limit_amount)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'กำหนดขีดจำกัดสำหรับเลข {number_norm} เรียบร้อยแล้ว'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'ไม่สามารถกำหนดขีดจำกัดได้'
            }), 500
            
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/api/delete_individual_limit', methods=['POST'])
@login_required
@admin_required
def api_delete_individual_limit():
    """API endpoint to delete individual number limit"""
    try:
        # Debug: Log request details
        print(f"DEBUG DELETE: Content-Type: {request.content_type}")
        print(f"DEBUG DELETE: Request data: {request.get_data()}")
        
        data = request.get_json()
        print(f"DEBUG DELETE: Parsed JSON data: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'ไม่มีข้อมูลที่ส่งมา'
            }), 400
        
        field = data.get('field')
        number_norm = data.get('number_norm')
        
        # Validate required fields
        if not field or not number_norm:
            return jsonify({
                'success': False,
                'error': 'ข้อมูลไม่ครบถ้วน (field, number_norm)'
            }), 400
        
        # Find and deactivate the rule
        from app.models import Rule, db
        rule = Rule.query.filter(
            Rule.rule_type == 'number_limit',
            Rule.field == field,
            Rule.number_norm == number_norm
        ).first()
        
        if rule:
            rule.is_active = False
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'ลบขีดจำกัดสำหรับเลข {number_norm} เรียบร้อยแล้ว'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'ไม่พบขีดจำกัดที่ต้องการลบ'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@admin_bp.route('/api/update_payout_rate', methods=['POST'])
@login_required
@admin_required
def api_update_payout_rate():
    """API endpoint to update payout rate"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        field = data.get('field')
        rate = data.get('rate')
        
        if not field or rate is None:
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Validate rate
        try:
            rate = int(rate)
            if rate < 0:
                return jsonify({'success': False, 'error': 'Rate must be positive'})
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid rate value'})
        
        # Update the payout rate
        success = LimitService.set_base_payout_rate(field, rate)
        
        if success:
            # Create audit log
            audit_log_entry = AuditLog(
                user_id=current_user.id,
                action='update_payout_rate',
                details=f'Updated payout rate for {field}: {rate}',
                ip_address=request.remote_addr
            )
            db.session.add(audit_log_entry)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'อัปเดตอัตราการจ่าย {LimitService._get_field_display_name(field)} เป็น {rate:,} สำเร็จ'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update payout rate'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================================
# REPORTS ROUTES - ระบบรายงานภาพรวม
# ============================================================================

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """หน้ารายงานภาพรวม"""
    # ดึงรายการ batch ที่มีข้อมูล
    available_batches = ReportsService.get_available_batches()
    
    # ใช้ batch ล่าสุดเป็นค่าเริ่มต้น
    current_batch = available_batches[0]['batch_id'] if available_batches else None
    
    return render_template('admin/reports.html', 
                         available_batches=available_batches,
                         current_batch=current_batch)

@admin_bp.route('/api/reports/summary')
@login_required
@admin_required
def api_reports_summary():
    """API: รายงานสรุปภาพรวม"""
    batch_id = request.args.get('batch_id')
    
    if not batch_id:
        return jsonify({'success': False, 'error': 'กรุณาระบุ batch_id'})
    
    # สร้างรายงานสรุป
    result = ReportsService.get_batch_summary(batch_id)
    
    return jsonify(result)

@admin_bp.route('/api/reports/number_detail')
@login_required
@admin_required
def api_reports_number_detail():
    """API: รายละเอียดเลขเฉพาะตัว"""
    field = request.args.get('field')
    number = request.args.get('number')
    batch_id = request.args.get('batch_id')
    
    if not all([field, number, batch_id]):
        return jsonify({'success': False, 'error': 'กรุณาระบุ field, number และ batch_id'})
    
    # วิเคราะห์เลขเฉพาะตัว
    result = ReportsService.get_number_analysis(field, number, batch_id)
    
    return jsonify(result)

@admin_bp.route('/api/reports/risk_analysis')
@login_required
@admin_required
def api_reports_risk_analysis():
    """API: วิเคราะห์ความเสี่ยง"""
    batch_id = request.args.get('batch_id')
    threshold = float(request.args.get('threshold', 0.1))  # 10% default
    
    if not batch_id:
        return jsonify({'success': False, 'error': 'กรุณาระบุ batch_id'})
    
    # วิเคราะห์ความเสี่ยง
    result = ReportsService.get_risk_analysis(batch_id, threshold)
    
    return jsonify(result)

@admin_bp.route('/api/reports/charts')
@login_required
@admin_required
def api_reports_charts():
    """API: ข้อมูลสำหรับกราฟ"""
    batch_id = request.args.get('batch_id')
    chart_type = request.args.get('type', 'field_distribution')
    
    if not batch_id:
        return jsonify({'success': False, 'error': 'กรุณาระบุ batch_id'})
    
    # สร้างข้อมูลกราฟ
    result = ReportsService.get_chart_data(batch_id, chart_type)
    
    return jsonify(result)

@admin_bp.route('/api/reports/batches')
@login_required
@admin_required
def api_reports_batches():
    """API: รายการ batch ที่มีข้อมูล"""
    batches = ReportsService.get_available_batches()
    
    return jsonify({
        'success': True,
        'data': batches
    })

# Risk Management Routes
@admin_bp.route('/risk-management')
@login_required
@admin_required
def risk_management():
    """หน้า Risk Management Dashboard"""
    try:
        current_batch_id = OrderService.get_current_batch_id()
        if not current_batch_id:
            flash('ไม่พบข้อมูล batch ปัจจุบัน', 'warning')
            return redirect(url_for('admin.dashboard'))
        
        return render_template('admin/risk_management.html', 
                             current_batch_id=current_batch_id)
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/risk-dashboard')
@login_required
@admin_required
def api_risk_dashboard():
    """API สำหรับ Risk Dashboard"""
    try:
        batch_id = request.args.get('batch_id', OrderService.get_current_batch_id())
        if not batch_id:
            return jsonify({"success": False, "error": "ไม่พบ batch_id"}), 400
            
        risk_data = RiskManagementService.get_risk_dashboard(batch_id)
        return jsonify(risk_data)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route('/api/risk-detail')
@login_required
@admin_required  
def api_risk_detail():
    """API สำหรับข้อมูลความเสี่ยงรายละเอียดของเลขเฉพาะ"""
    try:
        field = request.args.get('field')
        number = request.args.get('number')
        batch_id = request.args.get('batch_id', OrderService.get_current_batch_id())
        
        if not all([field, number, batch_id]):
            return jsonify({"success": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400
            
        risk_detail = RiskManagementService.get_number_risk_detail(field, number, batch_id)
        return jsonify(risk_detail)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Simple Sales Report Routes (เหมือนตัวอย่าง)
@admin_bp.route('/simple-sales-report')
@login_required
@admin_required
def simple_sales_report():
    """หน้ารายงานยอดขายแบบง่าย เหมือนตัวอย่าง"""
    return render_template('admin/simple_sales_report.html')

# Sales Report Routes  
@admin_bp.route('/sales-report')
@login_required
@admin_required
def sales_report():
    """หน้ารายงานยอดขายและยอดที่คาดว่าจะจ่าย (ไม่แยก batch)"""
    try:
        return render_template('admin/sales_report.html')
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/sales-summary')
@login_required
@admin_required
def api_sales_summary():
    """API สำหรับรายงานสรุปยอดขายและยอดที่คาดว่าจะจ่าย (ไม่แยก batch)"""
    try:
        sales_data = SimpleSalesService.get_all_sales_report()
        return jsonify(sales_data)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route('/api/top-sales')
@login_required
@admin_required
def api_top_sales():
    """API สำหรับ Top Sales Numbers แยกตามประเภท (ไม่แยก batch)"""
    try:
        top_sales = SimpleSalesService.get_top_sales_by_field()
        return jsonify(top_sales)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500