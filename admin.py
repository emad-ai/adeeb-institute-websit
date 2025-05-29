from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.security import generate_password_hash
from sqlalchemy import func, and_, extract, case
from datetime import datetime, timedelta
import io
import csv
import json
from models import User, Course, Enrollment, Attendance, Grade, AttendanceSession, Notification, TeacherEvaluation
from forms import UserForm, CourseForm, EnrollmentForm, AttendanceForm, GradeForm
from app import db
from utils import save_uploaded_file, create_pdf_report, admin_required

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """ديكوريتر للتحقق من صلاحيات المدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """لوحة تحكم المدير"""
    # إحصائيات عامة
    total_students = User.query.filter_by(role='student', is_active=True).count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    total_courses = Course.query.filter_by(is_active=True).count()
    total_enrollments = Enrollment.query.filter_by(is_active=True).count()
    
    # إحصائيات الرسوم
    total_fees = db.session.query(func.sum(Enrollment.amount_paid)).scalar() or 0
    pending_payments = Enrollment.query.filter_by(payment_status='pending').count()
    
    # أحدث التسجيلات
    recent_enrollments = db.session.query(Enrollment, User, Course).join(
        User, Enrollment.student_id == User.id
    ).join(
        Course, Enrollment.course_id == Course.id
    ).order_by(Enrollment.enrollment_date.desc()).limit(5).all()
    
    # إحصائيات الحضور لهذا الشهر
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_attendance = db.session.query(
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'present', 1), else_=0)).label('present'),
        func.sum(case((Attendance.status == 'absent', 1), else_=0)).label('absent')
    ).join(AttendanceSession).filter(
        extract('month', AttendanceSession.session_date) == current_month,
        extract('year', AttendanceSession.session_date) == current_year
    ).first()
    
    # الدورات الأكثر تسجيلاً
    popular_courses = db.session.query(
        Course.name,
        func.count(Enrollment.id).label('enrollment_count')
    ).join(Enrollment).filter(Course.is_active == True).group_by(
        Course.id, Course.name
    ).order_by(func.count(Enrollment.id).desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_courses=total_courses,
                         total_enrollments=total_enrollments,
                         total_fees=total_fees,
                         pending_payments=pending_payments,
                         recent_enrollments=recent_enrollments,
                         monthly_attendance=monthly_attendance,
                         popular_courses=popular_courses)

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    """إدارة الطلاب"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    course_filter = request.args.get('course', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    # بناء الاستعلام
    query = User.query.filter_by(role='student')
    
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.phone.contains(search))
        )
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if course_filter:
        query = query.join(Enrollment).filter(
            Enrollment.course_id == course_filter,
            Enrollment.is_active == True
        )
    
    students = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # قائمة الدورات للفلترة
    courses = Course.query.filter_by(is_active=True).all()
    
    return render_template('admin/students.html',
                         students=students,
                         courses=courses,
                         search=search,
                         course_filter=course_filter,
                         status_filter=status_filter)

@admin_bp.route('/student/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    """إضافة طالب جديد"""
    form = UserForm()
    form.role.data = 'student'  # تعيين الدور كطالب
    
    if form.validate_on_submit():
        # التحقق من عدم وجود المستخدم مسبقاً
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني موجود مسبقاً', 'error')
            return render_template('admin/add_student.html', form=form)
        
        # إنشاء المستخدم الجديد
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash('123456'),  # كلمة مرور افتراضية
            full_name=form.full_name.data,
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            role='student',
            is_active=form.is_active.data
        )
        
        # حفظ الصورة الشخصية
        if form.profile_picture.data:
            filename = save_uploaded_file(form.profile_picture.data, 'profiles')
            if filename:
                user.profile_picture = filename
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'تم إضافة الطالب {user.full_name} بنجاح. كلمة المرور الافتراضية: 123456', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في إضافة الطالب: {str(e)}")
            flash('حدث خطأ في إضافة الطالب', 'error')
    
    return render_template('admin/add_student.html', form=form)

@admin_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    """تعديل بيانات طالب"""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    form = UserForm(obj=student)
    
    if form.validate_on_submit():
        # التحقق من عدم تكرار اسم المستخدم أو البريد الإلكتروني
        existing_user = User.query.filter(
            User.id != student_id,
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني موجود مسبقاً', 'error')
            return render_template('admin/edit_student.html', form=form, student=student)
        
        # تحديث البيانات
        form.populate_obj(student)
        
        # حفظ الصورة الشخصية الجديدة
        if form.profile_picture.data:
            filename = save_uploaded_file(form.profile_picture.data, 'profiles')
            if filename:
                student.profile_picture = filename
        
        try:
            db.session.commit()
            flash(f'تم تحديث بيانات الطالب {student.full_name} بنجاح', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في تحديث الطالب: {str(e)}")
            flash('حدث خطأ في تحديث البيانات', 'error')
    
    return render_template('admin/edit_student.html', form=form, student=student)

@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    """حذف طالب"""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    
    try:
        # إلغاء تفعيل الطالب بدلاً من حذفه للحفاظ على البيانات التاريخية
        student.is_active = False
        db.session.commit()
        flash(f'تم إلغاء تفعيل الطالب {student.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في حذف الطالب: {str(e)}")
        flash('حدث خطأ في حذف الطالب', 'error')
    
    return redirect(url_for('admin.students'))

@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """إدارة الدورات"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    teacher_filter = request.args.get('teacher', '', type=str)
    
    # بناء الاستعلام
    query = Course.query
    
    if search:
        query = query.filter(Course.name.contains(search))
    
    if teacher_filter:
        query = query.filter_by(teacher_id=teacher_filter)
    
    courses = query.order_by(Course.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    # قائمة المعلمين للفلترة
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    
    return render_template('admin/courses.html',
                         courses=courses,
                         teachers=teachers,
                         search=search,
                         teacher_filter=teacher_filter)

@admin_bp.route('/course/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    """إضافة دورة جديدة"""
    form = CourseForm()
    
    # تحميل قائمة المعلمين
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    form.teacher_id.choices = [(0, 'بدون معلم')] + [(t.id, t.full_name) for t in teachers]
    
    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            description=form.description.data,
            teacher_id=form.teacher_id.data if form.teacher_id.data > 0 else None,
            duration_hours=form.duration_hours.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            fee=form.fee.data,
            max_students=form.max_students.data,
            is_active=form.is_active.data
        )
        
        try:
            db.session.add(course)
            db.session.commit()
            flash(f'تم إضافة الدورة {course.name} بنجاح', 'success')
            return redirect(url_for('admin.courses'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في إضافة الدورة: {str(e)}")
            flash('حدث خطأ في إضافة الدورة', 'error')
    
    return render_template('admin/add_course.html', form=form)

@admin_bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """تعديل دورة"""
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    
    # تحميل قائمة المعلمين
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    form.teacher_id.choices = [(0, 'بدون معلم')] + [(t.id, t.full_name) for t in teachers]
    
    if form.validate_on_submit():
        form.populate_obj(course)
        if course.teacher_id == 0:
            course.teacher_id = None
        
        try:
            db.session.commit()
            flash(f'تم تحديث الدورة {course.name} بنجاح', 'success')
            return redirect(url_for('admin.courses'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في تحديث الدورة: {str(e)}")
            flash('حدث خطأ في تحديث الدورة', 'error')
    
    return render_template('admin/edit_course.html', form=form, course=course)

@admin_bp.route('/teachers')
@login_required
@admin_required
def teachers():
    """إدارة المعلمين"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    # بناء الاستعلام
    query = User.query.filter_by(role='teacher')
    
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.username.contains(search)) |
            (User.email.contains(search))
        )
    
    teachers = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/teachers.html', teachers=teachers, search=search)

@admin_bp.route('/teacher/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_teacher():
    """إضافة معلم جديد"""
    form = UserForm()
    form.role.data = 'teacher'
    
    if form.validate_on_submit():
        # التحقق من عدم وجود المستخدم مسبقاً
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني موجود مسبقاً', 'error')
            return render_template('admin/add_teacher.html', form=form)
        
        # إنشاء المعلم الجديد
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash('123456'),
            full_name=form.full_name.data,
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            role='teacher',
            is_active=form.is_active.data
        )
        
        # حفظ الصورة الشخصية
        if form.profile_picture.data:
            filename = save_uploaded_file(form.profile_picture.data, 'profiles')
            if filename:
                user.profile_picture = filename
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'تم إضافة المعلم {user.full_name} بنجاح. كلمة المرور الافتراضية: 123456', 'success')
            return redirect(url_for('admin.teachers'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في إضافة المعلم: {str(e)}")
            flash('حدث خطأ في إضافة المعلم', 'error')
    
    return render_template('admin/add_teacher.html', form=form)

@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """صفحة الإحصائيات التفصيلية"""
    # إحصائيات شهرية للتسجيلات
    monthly_enrollments = db.session.query(
        extract('month', Enrollment.enrollment_date).label('month'),
        extract('year', Enrollment.enrollment_date).label('year'),
        func.count(Enrollment.id).label('count')
    ).filter(
        Enrollment.enrollment_date >= datetime.now() - timedelta(days=365)
    ).group_by(
        extract('year', Enrollment.enrollment_date),
        extract('month', Enrollment.enrollment_date)
    ).order_by('year', 'month').all()
    
    # إحصائيات الرسوم
    payment_stats = db.session.query(
        Enrollment.payment_status,
        func.count(Enrollment.id).label('count'),
        func.sum(Enrollment.amount_paid).label('total_amount')
    ).group_by(Enrollment.payment_status).all()
    
    # أداء الطلاب في الدورات
    course_performance = db.session.query(
        Course.name,
        func.avg(Grade.grade).label('avg_grade'),
        func.count(Grade.id).label('grade_count')
    ).join(Grade).group_by(Course.id, Course.name).all()
    
    # معدل الحضور لكل دورة
    attendance_rates = db.session.query(
        Course.name,
        func.count(Attendance.id).label('total_sessions'),
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present_count')
    ).join(
        AttendanceSession, Course.id == AttendanceSession.course_id
    ).join(
        Attendance, AttendanceSession.id == Attendance.session_id
    ).group_by(Course.id, Course.name).all()
    
    return render_template('admin/statistics.html',
                         monthly_enrollments=monthly_enrollments,
                         payment_stats=payment_stats,
                         course_performance=course_performance,
                         attendance_rates=attendance_rates)

@admin_bp.route('/export/students')
@login_required
@admin_required
def export_students():
    """تصدير بيانات الطلاب إلى CSV"""
    students = User.query.filter_by(role='student').all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # كتابة العناوين
    writer.writerow(['ID', 'اسم المستخدم', 'الاسم الكامل', 'البريد الإلكتروني', 
                    'رقم الجوال', 'تاريخ الميلاد', 'الجنس', 'تاريخ التسجيل', 'الحالة'])
    
    # كتابة البيانات
    for student in students:
        writer.writerow([
            student.id,
            student.username,
            student.full_name,
            student.email,
            student.phone or '',
            student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            'ذكر' if student.gender == 'male' else 'أنثى' if student.gender == 'female' else '',
            student.created_at.strftime('%Y-%m-%d'),
            'نشط' if student.is_active else 'غير نشط'
        ])
    
    output.seek(0)
    
    # إنشاء ملف للتحميل
    buffer = io.BytesIO()
    buffer.write(output.getvalue().encode('utf-8-sig'))  # BOM for Excel Arabic support
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'students_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@admin_bp.route('/export/courses')
@login_required
@admin_required
def export_courses():
    """تصدير بيانات الدورات إلى CSV"""
    courses = Course.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # كتابة العناوين
    writer.writerow(['ID', 'اسم الدورة', 'المعلم', 'المدة بالساعات', 'تاريخ البداية', 
                    'تاريخ النهاية', 'الرسوم', 'أقصى عدد طلاب', 'عدد المسجلين', 'الحالة'])
    
    # كتابة البيانات
    for course in courses:
        enrolled_count = Enrollment.query.filter_by(course_id=course.id, is_active=True).count()
        teacher_name = course.teacher.full_name if course.teacher else 'بدون معلم'
        
        writer.writerow([
            course.id,
            course.name,
            teacher_name,
            course.duration_hours or '',
            course.start_date.strftime('%Y-%m-%d') if course.start_date else '',
            course.end_date.strftime('%Y-%m-%d') if course.end_date else '',
            course.fee or 0,
            course.max_students or '',
            enrolled_count,
            'نشطة' if course.is_active else 'غير نشطة'
        ])
    
    output.seek(0)
    
    # إنشاء ملف للتحميل
    buffer = io.BytesIO()
    buffer.write(output.getvalue().encode('utf-8-sig'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'courses_{datetime.now().strftime("%Y%m%d")}.csv'
    )
