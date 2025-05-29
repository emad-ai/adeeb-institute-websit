from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, case
from datetime import datetime
from models import User, Course, Enrollment, Attendance, Grade, AttendanceSession, Notification, TeacherEvaluation
from forms import ProfileUpdateForm, PasswordChangeForm, TeacherEvaluationForm
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from utils import save_uploaded_file

student_bp = Blueprint('student', __name__)

def student_required(f):
    """ديكوريتر للتحقق من صلاحيات الطالب"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """لوحة تحكم الطالب"""
    # الدورات المسجل فيها الطالب
    enrollments = db.session.query(Enrollment, Course).join(
        Course, Enrollment.course_id == Course.id
    ).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).all()
    
    # إحصائيات الطالب
    total_courses = len(enrollments)
    
    # معدل الحضور العام
    total_attendance = Attendance.query.filter_by(student_id=current_user.id).count()
    present_attendance = Attendance.query.filter_by(student_id=current_user.id, status='present').count()
    
    attendance_rate = 0
    if total_attendance > 0:
        attendance_rate = round((present_attendance / total_attendance) * 100, 1)
    
    # متوسط الدرجات العام
    avg_grade = db.session.query(func.avg(Grade.grade)).filter(
        Grade.student_id == current_user.id
    ).scalar() or 0
    avg_grade = round(float(avg_grade), 1) if avg_grade else 0
    
    # إجمالي الرسوم والمدفوعات
    total_fees = sum([enrollment.course.fee or 0 for enrollment, course in enrollments])
    total_paid = db.session.query(func.sum(Enrollment.amount_paid)).filter(
        Enrollment.student_id == current_user.id
    ).scalar() or 0
    
    # أحدث الدرجات
    recent_grades = db.session.query(Grade, Course).join(
        Course, Grade.course_id == Course.id
    ).filter(
        Grade.student_id == current_user.id
    ).order_by(Grade.date_recorded.desc()).limit(5).all()
    
    # الجلسات القادمة
    upcoming_sessions = db.session.query(AttendanceSession, Course).join(
        Course, AttendanceSession.course_id == Course.id
    ).join(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True,
        AttendanceSession.session_date >= datetime.now().date()
    ).order_by(AttendanceSession.session_date).limit(5).all()
    
    # الإشعارات غير المقروءة
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html',
                         enrollments=enrollments,
                         total_courses=total_courses,
                         attendance_rate=attendance_rate,
                         avg_grade=avg_grade,
                         total_fees=total_fees,
                         total_paid=total_paid,
                         recent_grades=recent_grades,
                         upcoming_sessions=upcoming_sessions,
                         unread_notifications=unread_notifications)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    """الملف الشخصي للطالب"""
    form = ProfileUpdateForm(obj=current_user)
    
    if form.validate_on_submit():
        # التحقق من عدم تكرار البريد الإلكتروني
        existing_user = User.query.filter(
            User.id != current_user.id,
            User.email == form.email.data
        ).first()
        
        if existing_user:
            flash('البريد الإلكتروني مسجل مسبقاً', 'error')
        else:
            # تحديث البيانات
            current_user.full_name = form.full_name.data
            current_user.email = form.email.data
            current_user.phone = form.phone.data
            current_user.date_of_birth = form.date_of_birth.data
            current_user.gender = form.gender.data
            current_user.address = form.address.data
            
            # حفظ الصورة الشخصية الجديدة
            if form.profile_picture.data:
                filename = save_uploaded_file(form.profile_picture.data, 'profiles')
                if filename:
                    current_user.profile_picture = filename
            
            try:
                db.session.commit()
                flash('تم تحديث الملف الشخصي بنجاح', 'success')
                return redirect(url_for('student.profile'))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ في تحديث الملف الشخصي', 'error')
    
    return render_template('student/profile.html', form=form)

@student_bp.route('/courses')
@login_required
@student_required
def courses():
    """دوراتي"""
    # الدورات المسجل فيها الطالب مع التفاصيل
    enrollments_data = db.session.query(Enrollment, Course, User).join(
        Course, Enrollment.course_id == Course.id
    ).outerjoin(
        User, Course.teacher_id == User.id
    ).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).all()
    
    # حساب الإحصائيات لكل دورة
    courses_with_stats = []
    for enrollment, course, teacher in enrollments_data:
        # معدل الحضور للدورة
        attendance_stats = db.session.query(
            func.count(Attendance.id).label('total'),
            func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present')
        ).join(AttendanceSession).filter(
            Attendance.student_id == current_user.id,
            AttendanceSession.course_id == course.id
        ).first()
        
        attendance_rate = 0
        if attendance_stats.total and attendance_stats.total > 0:
            attendance_rate = round((attendance_stats.present / attendance_stats.total) * 100, 1)
        
        # متوسط الدرجات للدورة
        avg_grade = db.session.query(func.avg(Grade.grade)).filter(
            Grade.student_id == current_user.id,
            Grade.course_id == course.id
        ).scalar() or 0
        avg_grade = round(float(avg_grade), 1) if avg_grade else 0
        
        # عدد الواجبات والامتحانات
        total_assignments = Grade.query.filter(
            Grade.student_id == current_user.id,
            Grade.course_id == course.id
        ).count()
        
        courses_with_stats.append({
            'enrollment': enrollment,
            'course': course,
            'teacher': teacher,
            'attendance_rate': attendance_rate,
            'avg_grade': avg_grade,
            'total_assignments': total_assignments
        })
    
    return render_template('student/courses.html', courses_data=courses_with_stats)

@student_bp.route('/course/<int:course_id>/details')
@login_required
@student_required
def course_details(course_id):
    """تفاصيل دورة محددة"""
    # التحقق من تسجيل الطالب في الدورة
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
        is_active=True
    ).first_or_404()
    
    course = Course.query.get_or_404(course_id)
    
    # سجل الحضور للطالب في هذه الدورة
    attendance_records = db.session.query(Attendance, AttendanceSession).join(
        AttendanceSession, Attendance.session_id == AttendanceSession.id
    ).filter(
        Attendance.student_id == current_user.id,
        AttendanceSession.course_id == course_id
    ).order_by(AttendanceSession.session_date.desc()).all()
    
    # الدرجات في هذه الدورة
    grades = Grade.query.filter(
        Grade.student_id == current_user.id,
        Grade.course_id == course_id
    ).order_by(Grade.date_recorded.desc()).all()
    
    # إحصائيات الدورة
    attendance_stats = db.session.query(
        func.count(Attendance.id).label('total'),
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present'),
        func.sum(func.case([(Attendance.status == 'absent', 1)], else_=0)).label('absent'),
        func.sum(func.case([(Attendance.status == 'late', 1)], else_=0)).label('late')
    ).join(AttendanceSession).filter(
        Attendance.student_id == current_user.id,
        AttendanceSession.course_id == course_id
    ).first()
    
    # متوسط الدرجات
    avg_grade = db.session.query(func.avg(Grade.grade)).filter(
        Grade.student_id == current_user.id,
        Grade.course_id == course_id
    ).scalar() or 0
    avg_grade = round(float(avg_grade), 1) if avg_grade else 0
    
    return render_template('student/course_details.html',
                         course=course,
                         enrollment=enrollment,
                         attendance_records=attendance_records,
                         grades=grades,
                         attendance_stats=attendance_stats,
                         avg_grade=avg_grade)

@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    """سجل الحضور"""
    course_id = request.args.get('course_id', type=int)
    
    # الدورات المسجل فيها الطالب
    my_courses = db.session.query(Course).join(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).all()
    
    attendance_records = []
    selected_course = None
    
    if course_id:
        # التحقق من تسجيل الطالب في الدورة
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
            is_active=True
        ).first()
        
        if enrollment:
            selected_course = Course.query.get(course_id)
            
            # سجل الحضور للطالب في هذه الدورة
            attendance_records = db.session.query(Attendance, AttendanceSession).join(
                AttendanceSession, Attendance.session_id == AttendanceSession.id
            ).filter(
                Attendance.student_id == current_user.id,
                AttendanceSession.course_id == course_id
            ).order_by(AttendanceSession.session_date.desc()).all()
    else:
        # جميع سجلات الحضور للطالب
        attendance_records = db.session.query(Attendance, AttendanceSession, Course).join(
            AttendanceSession, Attendance.session_id == AttendanceSession.id
        ).join(
            Course, AttendanceSession.course_id == Course.id
        ).filter(
            Attendance.student_id == current_user.id
        ).order_by(AttendanceSession.session_date.desc()).all()
    
    return render_template('student/attendance.html',
                         my_courses=my_courses,
                         attendance_records=attendance_records,
                         selected_course=selected_course)

@student_bp.route('/grades')
@login_required
@student_required
def grades():
    """درجاتي"""
    course_id = request.args.get('course_id', type=int)
    grade_type = request.args.get('type', type=str)
    
    # الدورات المسجل فيها الطالب
    my_courses = db.session.query(Course).join(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).all()
    
    grades_query = db.session.query(Grade, Course).join(
        Course, Grade.course_id == Course.id
    ).filter(Grade.student_id == current_user.id)
    
    selected_course = None
    
    if course_id:
        # التحقق من تسجيل الطالب في الدورة
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
            is_active=True
        ).first()
        
        if enrollment:
            selected_course = Course.query.get(course_id)
            grades_query = grades_query.filter(Grade.course_id == course_id)
    
    if grade_type:
        grades_query = grades_query.filter(Grade.grade_type == grade_type)
    
    grades_data = grades_query.order_by(Grade.date_recorded.desc()).all()
    
    # حساب المتوسطات
    course_averages = {}
    for course in my_courses:
        avg = db.session.query(func.avg(Grade.grade)).filter(
            Grade.student_id == current_user.id,
            Grade.course_id == course.id
        ).scalar() or 0
        course_averages[course.id] = round(float(avg), 1) if avg else 0
    
    return render_template('student/grades.html',
                         my_courses=my_courses,
                         grades_data=grades_data,
                         selected_course=selected_course,
                         selected_type=grade_type,
                         course_averages=course_averages)

@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    """الإشعارات"""
    page = request.args.get('page', 1, type=int)
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # تمييز الإشعارات كمقروءة عند فتح الصفحة
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in unread_notifications:
        notification.is_read = True
    
    try:
        db.session.commit()
    except:
        db.session.rollback()
    
    return render_template('student/notifications.html', notifications=notifications)

@student_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
@student_required
def change_password():
    """تغيير كلمة المرور"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = generate_password_hash(form.new_password.data)
            try:
                db.session.commit()
                flash('تم تغيير كلمة المرور بنجاح', 'success')
                return redirect(url_for('student.profile'))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ في تغيير كلمة المرور', 'error')
        else:
            flash('كلمة المرور الحالية غير صحيحة', 'error')
    
    return render_template('student/change_password.html', form=form)

@student_bp.route('/payments')
@login_required
@student_required
def payments():
    """سجل المدفوعات"""
    # معلومات المدفوعات للطالب
    enrollments = db.session.query(Enrollment, Course).join(
        Course, Enrollment.course_id == Course.id
    ).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.is_active == True
    ).all()
    
    # حساب الإجماليات
    total_fees = sum([course.fee or 0 for enrollment, course in enrollments])
    total_paid = sum([enrollment.amount_paid or 0 for enrollment, course in enrollments])
    remaining_balance = total_fees - total_paid
    
    return render_template('student/payments.html',
                         enrollments=enrollments,
                         total_fees=total_fees,
                         total_paid=total_paid,
                         remaining_balance=remaining_balance)


@student_bp.route('/evaluations')
@login_required
@student_required
def evaluations():
    """عرض تقييمات المعلمين"""
    # الحصول على التقييمات التي قام بها الطالب
    my_evaluations = TeacherEvaluation.query.filter_by(student_id=current_user.id).all()
    
    # الحصول على الدورات التي يمكن تقييم معلميها
    enrollments = Enrollment.query.filter_by(student_id=current_user.id, is_active=True).all()
    available_to_evaluate = []
    
    for enrollment in enrollments:
        if enrollment.course.teacher:
            # التحقق من عدم وجود تقييم سابق
            existing_evaluation = TeacherEvaluation.query.filter_by(
                student_id=current_user.id,
                teacher_id=enrollment.course.teacher.id,
                course_id=enrollment.course.id
            ).first()
            
            if not existing_evaluation:
                available_to_evaluate.append(enrollment)
    
    return render_template('student/evaluations.html',
                         my_evaluations=my_evaluations,
                         available_to_evaluate=available_to_evaluate)


@student_bp.route('/evaluate_teacher/<int:course_id>', methods=['GET', 'POST'])
@login_required
@student_required
def evaluate_teacher(course_id):
    """تقييم معلم في دورة محددة"""
    # التحقق من التسجيل في الدورة
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, 
        course_id=course_id, 
        is_active=True
    ).first()
    
    if not enrollment:
        flash('غير مصرح لك بتقييم هذه الدورة', 'error')
        return redirect(url_for('student.evaluations'))
    
    course = enrollment.course
    if not course.teacher:
        flash('لا يوجد معلم محدد لهذه الدورة', 'error')
        return redirect(url_for('student.evaluations'))
    
    # التحقق من عدم وجود تقييم سابق
    existing_evaluation = TeacherEvaluation.query.filter_by(
        student_id=current_user.id,
        teacher_id=course.teacher.id,
        course_id=course_id
    ).first()
    
    if existing_evaluation:
        flash('لقد قمت بتقييم هذا المعلم من قبل', 'warning')
        return redirect(url_for('student.evaluations'))
    
    form = TeacherEvaluationForm()
    
    if form.validate_on_submit():
        evaluation = TeacherEvaluation(
            student_id=current_user.id,
            teacher_id=course.teacher.id,
            course_id=course_id,
            teaching_quality=form.teaching_quality.data,
            communication=form.communication.data,
            punctuality=form.punctuality.data,
            knowledge=form.knowledge.data,
            interaction=form.interaction.data,
            comments=form.comments.data,
            suggestions=form.suggestions.data,
            is_anonymous=form.is_anonymous.data
        )
        
        # حساب التقييم العام
        evaluation.calculate_overall_rating()
        
        db.session.add(evaluation)
        db.session.commit()
        
        flash('تم إرسال التقييم بنجاح', 'success')
        return redirect(url_for('student.evaluations'))
    
    return render_template('student/evaluate_teacher.html',
                         form=form,
                         course=course,
                         teacher=course.teacher)


@student_bp.route('/evaluation/<int:evaluation_id>')
@login_required
@student_required
def view_evaluation(evaluation_id):
    """عرض تفاصيل تقييم محدد"""
    evaluation = TeacherEvaluation.query.filter_by(
        id=evaluation_id,
        student_id=current_user.id
    ).first_or_404()
    
    return render_template('student/view_evaluation.html', evaluation=evaluation)
