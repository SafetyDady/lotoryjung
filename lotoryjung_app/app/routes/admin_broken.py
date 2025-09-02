from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length
f@admin_bp.route('/blocked_numbers/<int:id>/delete', methods=['POST'])
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


def admin_required(f):
    generate_blocked_numbers_for_field, 
    validate_bulk_numbers, 
    preview_bulk_blocked_numbers
)
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
    
    if not isinstance(numbers_data, list):
        return {'valid': False, 'errors': ['ข้อมูลไม่ถูกรูปแบบ'], 'valid_numbers': []}
    
    for i, item in enumerate(numbers_data):
        if not isinstance(item, dict):
            errors.append(f'รายการที่ {i+1}: ข้อมูลไม่ถูกรูปแบบ')
            continue
            
        number = item.get('number', '').strip()
        number_type = item.get('type', '').strip()
        
        # Validate number
        if not number:
            errors.append(f'รายการที่ {i+1}: กรุณากรอกหมายเลข')
            continue
            
        if not number.isdigit():
            errors.append(f'รายการที่ {i+1}: หมายเลขต้องเป็นตัวเลขเท่านั้น')
            continue
        
        # Validate number type and length
        if number_type == '2_digit':
            if len(number) > 2:
                errors.append(f'รายการที่ {i+1}: เลข 2 หลักต้องไม่เกิน 2 ตัว')
                continue
        elif number_type == '3_digit':
            if len(number) > 3:
                errors.append(f'รายการที่ {i+1}: เลข 3 หลักต้องไม่เกิน 3 ตัว')
                continue
        else:
            errors.append(f'รายการที่ {i+1}: ประเภทไม่ถูกต้อง')
            continue
        
        # Auto-detect type if not specified correctly
        if len(number) <= 2:
            number_type = '2_digit'
        else:
            number_type = '3_digit'
        
        valid_numbers.append({
            'number': number,
            'type': number_type,
            'original_index': i
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
    return render_template('admin/dashboard.html')

@admin_bp.route('/blocked_numbers')
@login_required  
@admin_required
def blocked_numbers():
    """Blocked numbers list"""
    page = request.args.get('page', 1, type=int)
    field_filter = request.args.get('field', '')
    search = request.args.get('search', '')
    
    query = BlockedNumber.query
    
    if field_filter:
        query = query.filter_by(field=field_filter)
    
    if search:
        query = query.filter(BlockedNumber.number_norm.contains(search))
    
    blocked_numbers = query.order_by(BlockedNumber.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    
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
    
    return render_template('admin/blocked_numbers.html', 
                         blocked_numbers=blocked_numbers,
                         field_filter=field_filter,
                         search=search,
                         stats=stats)

@admin_bp.route('/blocked_numbers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_blocked_number():
    """Add new blocked number"""
    form = BlockedNumberForm()
    
    if form.validate_on_submit():
        try:
            blocked_number = BlockedNumber(
                field=form.field.data,
                number_norm=form.number_norm.data.zfill(3),
                reason=form.reason.data,
                is_active=form.is_active.data
            )
            
            db.session.add(blocked_number)
            db.session.commit()
            
            flash('เพิ่มเลขอั้นเรียบร้อย', 'success')
            return redirect(url_for('admin.blocked_numbers'))
            
        except Exception as e:
            db.session.rollback()
            flash('เกิดข้อผิดพลาดในการบันทึกข้อมูล', 'error')
    
    return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้น')

@admin_bp.route('/blocked_numbers/bulk_add', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_add_blocked_numbers():
    """Bulk add blocked numbers with automatic permutation generation"""
    form = BulkBlockedNumberForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Get numbers data from JSON
        numbers_data = request.get_json() if request.is_json else request.form.get('numbers_data')
        
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
        
        if not validation_result['valid']:
            for error in validation_result['errors'][:5]:  # Show first 5 errors
                flash(error, 'error')
            return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้นหลายตัว')
        
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            # Clear all existing blocked numbers first
            deleted_count = BlockedNumber.query.delete()
            
            # Process each input number and generate all permutations
            all_records = []
            
            for item in validation_result['valid_numbers']:
                number = item['number']
                number_type = item['type']
                
                # Generate permutations based on number type
                if number_type == '2_digit':
                    # For 2-digit, generate permutations for both 2_top and 2_bottom
                    records_2top = generate_blocked_numbers_for_field(number, '2_top')
                    all_records.extend(records_2top)
                elif number_type == '3_digit':
                    # For 3-digit, generate permutations for 3_top and tote
                    records = generate_blocked_numbers_for_field(number, '3_top')
                    all_records.extend(records)
            
            # Remove duplicates and apply global settings
            unique_records = []
            seen = set()
            
            for record in all_records:
                key = (record['field'], record['number_norm'])
                if key not in seen:
                    seen.add(key)
                    # Apply global form settings
                    if form.reason.data:
                        record['reason'] = form.reason.data
                    record['is_active'] = form.is_active.data
                    unique_records.append(record)
            
            # Batch insert new records to database
            if unique_records:
                for record in unique_records:
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
                db.session.commit()
        
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}', 'error')
            return render_template('admin/bulk_blocked_number_form.html', form=form, title='เพิ่มเลขอั้นหลายตัว')
        
        # Show results
        if success_count > 0:
            flash(f'✅ สำเร็จ! ล้างข้อมูลเก่า {deleted_count} รายการ และบันทึกข้อมูลใหม่ {success_count} รายการ', 'success')
            flash(f'📊 สถิติ: บันทึกจาก {len(validation_result["valid_numbers"])} เลขที่กรอก → สร้างเป็น {success_count} records ในฐานข้อมูล', 'info')
        
        if error_count > 0:
            flash(f'⚠️ พบข้อผิดพลาด {error_count} รายการ', 'warning')
            for error in errors[:3]:  # Show first 3 errors
                flash(error, 'error')
        
        if success_count > 0:
            return redirect(url_for('admin.blocked_numbers'))
        
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
            blocked_number.number_norm = form.number_norm.data.zfill(3)
            blocked_number.reason = form.reason.data
            blocked_number.is_active = form.is_active.data
            
            db.session.commit()
            flash('แก้ไขเลขอั้นเรียบร้อย', 'success')
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
        flash('ลบเลขอั้นเรียบร้อย', 'success')
    except Exception as e:
        db.session.rollback()
        flash('เกิดข้อผิดพลาดในการลบข้อมูล', 'error')
    
    return redirect(url_for('admin.blocked_numbers'))


@admin_bp.route('/rules')
@login_required
@admin_required 
def rules():
    """Rules management"""
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


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Reports and analytics"""
    return render_template('admin/reports.html')
