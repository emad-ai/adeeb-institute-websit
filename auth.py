from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from models import User, Course, Enrollment
from forms import LoginForm, StudentRegistrationForm
from app import db
from utils import allowed_file, save_uploaded_file

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.is_active:
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                flash(f'مرحباً {user.full_name}', 'success')
                
                # توجيه المستخدم حسب دوره
                if next_page:
                    return redirect(next_page)
                elif user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                elif user.role == 'student':
                    return redirect(url_for('student.dashboard'))
                else:
                    return redirect(url_for('main.index'))
            else:
                flash('تم إيقاف حسابك. يرجى التواصل مع الإدارة', 'error')
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """تسجيل طالب جديد"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = StudentRegistrationForm()
    
    # تحميل قائمة الدورات النشطة
    active_courses = Course.query.filter_by(is_active=True).all()
    form.course_id.choices = [(course.id, course.name) for course in active_courses]
    
    if form.validate_on_submit():
        # التحقق من عدم وجود المستخدم مسبقاً
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('اسم المستخدم موجود مسبقاً', 'error')
            else:
                flash('البريد الإلكتروني مسجل مسبقاً', 'error')
            return render_template('auth/register.html', form=form)
        
        # إنشاء المستخدم الجديد
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            full_name=form.full_name.data,
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            role='student'
        )
        
        # حفظ الصورة الشخصية
        if form.profile_picture.data:
            filename = save_uploaded_file(form.profile_picture.data, 'profiles')
            if filename:
                user.profile_picture = filename
        
        try:
            db.session.add(user)
            db.session.flush()  # للحصول على ID المستخدم
            
            # تسجيل الطالب في الدورة المختارة
            course = Course.query.get(form.course_id.data)
            if course:
                enrollment = Enrollment(
                    student_id=user.id,
                    course_id=course.id,
                    payment_status='pending'
                )
                db.session.add(enrollment)
            
            db.session.commit()
            flash('تم إنشاء حسابك بنجاح. يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في إنشاء الحساب: {str(e)}")
            flash('حدث خطأ في إنشاء الحساب. يرجى المحاولة مرة أخرى', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """الملف الشخصي"""
    if current_user.role == 'student':
        return redirect(url_for('student.profile'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher.profile'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin.profile'))
    else:
        return redirect(url_for('main.index'))
