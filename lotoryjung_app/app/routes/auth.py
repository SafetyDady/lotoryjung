from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models import User, AuditLog
from app import db

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('ชื่อผู้ใช้', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('รหัสผ่าน', validators=[DataRequired(), Length(min=3)])
    submit = SubmitField('เข้าสู่ระบบ')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            
            # Log successful login
            audit_log = AuditLog(
                user_id=user.id,
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                details={'username': user.username}
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            # Log failed login attempt
            audit_log = AuditLog(
                user_id=user.id if user else None,
                action='login_failed',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                details={'username': form.username.data, 'reason': 'invalid_credentials'}
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    # Log logout
    audit_log = AuditLog(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        details={'username': current_user.username}
    )
    db.session.add(audit_log)
    db.session.commit()
    
    logout_user()
    flash('ออกจากระบบแล้ว', 'info')
    return redirect(url_for('main.index'))

