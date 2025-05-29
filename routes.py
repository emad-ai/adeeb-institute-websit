from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Course, Enrollment
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """الصفحة الرئيسية"""
    # إحصائيات عامة للصفحة الرئيسية
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_courses = Course.query.filter_by(is_active=True).count()
    total_enrollments = Enrollment.query.filter_by(is_active=True).count()
    
    # أحدث الدورات
    latest_courses = Course.query.filter_by(is_active=True).order_by(Course.created_at.desc()).limit(6).all()
    
    return render_template('index.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_courses=total_courses,
                         total_enrollments=total_enrollments,
                         latest_courses=latest_courses)

@main_bp.route('/courses')
def courses():
    """صفحة عرض جميع الدورات"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    # فلترة الدورات حسب البحث
    query = Course.query.filter_by(is_active=True)
    if search:
        query = query.filter(Course.name.contains(search))
    
    courses = query.order_by(Course.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('courses.html', courses=courses, search=search)

@main_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    """تفاصيل الدورة"""
    course = Course.query.get_or_404(course_id)
    
    # عدد الطلاب المسجلين
    enrolled_count = Enrollment.query.filter_by(course_id=course_id, is_active=True).count()
    
    # التحقق من تسجيل المستخدم الحالي
    is_enrolled = False
    if current_user.is_authenticated and current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course_id, 
            is_active=True
        ).first()
        is_enrolled = enrollment is not None
    
    return render_template('course_detail.html', 
                         course=course, 
                         enrolled_count=enrolled_count,
                         is_enrolled=is_enrolled)

@main_bp.route('/about')
def about():
    """صفحة حول الموقع"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """صفحة الاتصال"""
    return render_template('contact.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """توجيه لوحة التحكم حسب دور المستخدم"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student.dashboard'))
    else:
        flash('دور المستخدم غير محدد', 'error')
        return redirect(url_for('main.index'))
