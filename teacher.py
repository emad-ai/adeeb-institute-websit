from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import and_, func
from datetime import datetime, date
from models import User, Course, Enrollment, Attendance, Grade, AttendanceSession
from forms import AttendanceForm, GradeForm, ProfileUpdateForm, PasswordChangeForm
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from utils import save_uploaded_file

teacher_bp = Blueprint('teacher', __name__)

def teacher_required(f):
    """ديكوريتر للتحقق من صلاحيات المعلم"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """لوحة تحكم المعلم"""
    # الدورات المخصصة للمعلم
    my_courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    
    # إحصائيات المعلم
    total_students = db.session.query(func.count(Enrollment.student_id.distinct())).join(
        Course
    ).filter(
        Course.teacher_id == current_user.id,
        Enrollment.is_active == True
    ).scalar() or 0
    
    total_courses = len(my_courses)
    
    # جلسات الحضور الأخيرة
    recent_sessions = AttendanceSession.query.join(Course).filter(
        Course.teacher_id == current_user.id
    ).order_by(AttendanceSession.session_date.desc()).limit(5).all()
    
    # الواجبات والدرجات الأخيرة
    recent_grades = Grade.query.join(Course).filter(
        Course.teacher_id == current_user.id
    ).order_by(Grade.date_recorded.desc()).limit(10).all()
    
    # إحصائيات الحضور لهذا الشهر
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_attendance = db.session.query(
        func.count(Attendance.id).label('total'),
        func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present')
    ).join(AttendanceSession).join(Course).filter(
        Course.teacher_id == current_user.id,
        func.extract('month', AttendanceSession.session_date) == current_month,
        func.extract('year', AttendanceSession.session_date) == current_year
    ).first()
    
    attendance_rate = 0
    if monthly_attendance.total and monthly_attendance.total > 0:
        attendance_rate = round((monthly_attendance.present / monthly_attendance.total) * 100, 1)
    
    return render_template('teacher/dashboard.html',
                         my_courses=my_courses,
                         total_students=total_students,
                         total_courses=total_courses,
                         recent_sessions=recent_sessions,
                         recent_grades=recent_grades,
                         attendance_rate=attendance_rate)

@teacher_bp.route('/students')
@login_required
@teacher_required
def students():
    """عرض طلاب المعلم"""
    course_id = request.args.get('course_id', type=int)
    search = request.args.get('search', '', type=str)
    
    # الدورات المخصصة للمعلم
    my_courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    
    # بناء الاستعلام للطلاب
    query = db.session.query(User, Enrollment, Course).join(
        Enrollment, User.id == Enrollment.student_id
    ).join(
        Course, Enrollment.course_id == Course.id
    ).filter(
        Course.teacher_id == current_user.id,
        Enrollment.is_active == True,
        User.is_active == True
    )
    
    if course_id:
        query = query.filter(Course.id == course_id)
    
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.username.contains(search)) |
            (User.email.contains(search))
        )
    
    students_data = query.order_by(User.full_name).all()
    
    # حساب إحصائيات لكل طالب
    students_with_stats = []
    for user, enrollment, course in students_data:
        # معدل الحضور
        attendance_stats = db.session.query(
            func.count(Attendance.id).label('total'),
            func.sum(func.case([(Attendance.status == 'present', 1)], else_=0)).label('present')
        ).join(AttendanceSession).filter(
            Attendance.student_id == user.id,
            AttendanceSession.course_id == course.id
        ).first()
        
        attendance_rate = 0
        if attendance_stats.total and attendance_stats.total > 0:
            attendance_rate = round((attendance_stats.present / attendance_stats.total) * 100, 1)
        
        # متوسط الدرجات
        avg_grade = db.session.query(func.avg(Grade.grade)).filter(
            Grade.student_id == user.id,
            Grade.course_id == course.id
        ).scalar() or 0
        avg_grade = round(float(avg_grade), 1) if avg_grade else 0
        
        students_with_stats.append({
            'student': user,
            'enrollment': enrollment,
            'course': course,
            'attendance_rate': attendance_rate,
            'avg_grade': avg_grade
        })
    
    return render_template('teacher/students.html',
                         students_data=students_with_stats,
                         my_courses=my_courses,
                         selected_course=course_id,
                         search=search)

@teacher_bp.route('/attendance')
@login_required
@teacher_required
def attendance():
    """إدارة الحضور"""
    course_id = request.args.get('course_id', type=int)
    session_date = request.args.get('date', type=str)
    
    # الدورات المخصصة للمعلم
    my_courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    
    sessions_data = []
    students_data = []
    selected_course = None
    
    if course_id:
        selected_course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
        if selected_course:
            # جلسات الحضور لهذه الدورة
            sessions_query = AttendanceSession.query.filter_by(course_id=course_id)
            
            if session_date:
                try:
                    date_obj = datetime.strptime(session_date, '%Y-%m-%d').date()
                    sessions_query = sessions_query.filter_by(session_date=date_obj)
                except ValueError:
                    pass
            
            sessions_data = sessions_query.order_by(AttendanceSession.session_date.desc()).all()
            
            # طلاب هذه الدورة
            students_data = db.session.query(User).join(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.is_active == True,
                User.is_active == True
            ).order_by(User.full_name).all()
    
    return render_template('teacher/attendance.html',
                         my_courses=my_courses,
                         sessions_data=sessions_data,
                         students_data=students_data,
                         selected_course=selected_course,
                         selected_date=session_date)

@teacher_bp.route('/attendance/session/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_attendance_session():
    """إضافة جلسة حضور جديدة"""
    form = AttendanceForm()
    course_id = request.args.get('course_id', type=int)
    
    if not course_id:
        flash('يرجى اختيار الدورة أولاً', 'error')
        return redirect(url_for('teacher.attendance'))
    
    # التحقق من أن الدورة تابعة للمعلم
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
    if not course:
        flash('الدورة غير موجودة أو ليس لديك صلاحية للوصول إليها', 'error')
        return redirect(url_for('teacher.attendance'))
    
    if form.validate_on_submit():
        # التحقق من عدم وجود جلسة في نفس التاريخ
        existing_session = AttendanceSession.query.filter_by(
            course_id=course_id,
            session_date=form.session_date.data
        ).first()
        
        if existing_session:
            flash('توجد جلسة حضور في هذا التاريخ مسبقاً', 'error')
        else:
            session = AttendanceSession(
                course_id=course_id,
                session_date=form.session_date.data,
                session_time=form.session_time.data,
                topic=form.topic.data
            )
            
            try:
                db.session.add(session)
                db.session.flush()  # للحصول على ID الجلسة
                
                # إضافة سجلات حضور فارغة لجميع الطلاب المسجلين
                students = db.session.query(User).join(Enrollment).filter(
                    Enrollment.course_id == course_id,
                    Enrollment.is_active == True,
                    User.is_active == True
                ).all()
                
                for student in students:
                    attendance = Attendance(
                        student_id=student.id,
                        session_id=session.id,
                        status='absent'  # الافتراضي غائب
                    )
                    db.session.add(attendance)
                
                db.session.commit()
                flash('تم إنشاء جلسة الحضور بنجاح', 'success')
                return redirect(url_for('teacher.attendance', course_id=course_id))
                
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ في إنشاء جلسة الحضور', 'error')
    
    return render_template('teacher/add_attendance_session.html', form=form, course=course)

@teacher_bp.route('/attendance/session/<int:session_id>')
@login_required
@teacher_required
def attendance_session_detail(session_id):
    """تفاصيل جلسة حضور وتسجيل الحضور"""
    session = AttendanceSession.query.join(Course).filter(
        AttendanceSession.id == session_id,
        Course.teacher_id == current_user.id
    ).first_or_404()
    
    # سجلات الحضور لهذه الجلسة
    attendance_records = db.session.query(Attendance, User).join(
        User, Attendance.student_id == User.id
    ).filter(
        Attendance.session_id == session_id
    ).order_by(User.full_name).all()
    
    return render_template('teacher/attendance_session_detail.html',
                         session=session,
                         attendance_records=attendance_records)

@teacher_bp.route('/attendance/update', methods=['POST'])
@login_required
@teacher_required
def update_attendance():
    """تحديث حالة الحضور للطلاب"""
    session_id = request.form.get('session_id', type=int)
    
    # التحقق من صلاحية المعلم للجلسة
    session = AttendanceSession.query.join(Course).filter(
        AttendanceSession.id == session_id,
        Course.teacher_id == current_user.id
    ).first()
    
    if not session:
        return jsonify({'success': False, 'message': 'الجلسة غير موجودة'})
    
    try:
        # تحديث حالة الحضور لكل طالب
        for key, value in request.form.items():
            if key.startswith('attendance_'):
                student_id = int(key.split('_')[1])
                status = value
                
                attendance = Attendance.query.filter_by(
                    session_id=session_id,
                    student_id=student_id
                ).first()
                
                if attendance:
                    attendance.status = status
        
        # تحديث ملاحظات الجلسة إذا تم إرسالها
        if 'session_notes' in request.form:
            session.topic = request.form['session_notes']
        
        db.session.commit()
        flash('تم تحديث سجلات الحضور بنجاح', 'success')
        return redirect(url_for('teacher.attendance_session_detail', session_id=session_id))
        
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ في تحديث سجلات الحضور', 'error')
        return redirect(url_for('teacher.attendance_session_detail', session_id=session_id))

@teacher_bp.route('/grades')
@login_required
@teacher_required
def grades():
    """إدارة الدرجات"""
    course_id = request.args.get('course_id', type=int)
    student_id = request.args.get('student_id', type=int)
    
    # الدورات المخصصة للمعلم
    my_courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    
    grades_data = []
    students_data = []
    selected_course = None
    selected_student = None
    
    if course_id:
        selected_course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
        if selected_course:
            # طلاب هذه الدورة
            students_data = db.session.query(User).join(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.is_active == True,
                User.is_active == True
            ).order_by(User.full_name).all()
            
            # الدرجات
            grades_query = db.session.query(Grade, User).join(
                User, Grade.student_id == User.id
            ).filter(Grade.course_id == course_id)
            
            if student_id:
                selected_student = User.query.get(student_id)
                grades_query = grades_query.filter(Grade.student_id == student_id)
            
            grades_data = grades_query.order_by(Grade.date_recorded.desc()).all()
    
    return render_template('teacher/grades.html',
                         my_courses=my_courses,
                         grades_data=grades_data,
                         students_data=students_data,
                         selected_course=selected_course,
                         selected_student=selected_student)

@teacher_bp.route('/grades/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_grade():
    """إضافة درجة جديدة"""
    form = GradeForm()
    course_id = request.args.get('course_id', type=int)
    
    if not course_id:
        flash('يرجى اختيار الدورة أولاً', 'error')
        return redirect(url_for('teacher.grades'))
    
    # التحقق من أن الدورة تابعة للمعلم
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
    if not course:
        flash('الدورة غير موجودة أو ليس لديك صلاحية للوصول إليها', 'error')
        return redirect(url_for('teacher.grades'))
    
    # طلاب هذه الدورة
    students = db.session.query(User).join(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.is_active == True,
        User.is_active == True
    ).order_by(User.full_name).all()
    
    if form.validate_on_submit():
        # إضافة الدرجة لجميع الطلاب المحددين
        student_grades = request.form.getlist('student_grades')
        added_count = 0
        
        for student_grade in student_grades:
            if student_grade:
                student_id, grade_value = student_grade.split(':')
                student_id = int(student_id)
                grade_value = float(grade_value)
                
                if 0 <= grade_value <= form.max_grade.data:
                    grade = Grade(
                        student_id=student_id,
                        course_id=course_id,
                        assignment_name=form.assignment_name.data,
                        grade=grade_value,
                        max_grade=form.max_grade.data,
                        grade_type=form.grade_type.data,
                        notes=form.notes.data
                    )
                    db.session.add(grade)
                    added_count += 1
        
        try:
            db.session.commit()
            flash(f'تم إضافة {added_count} درجة بنجاح', 'success')
            return redirect(url_for('teacher.grades', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ في إضافة الدرجات', 'error')
    
    return render_template('teacher/add_grade.html', form=form, course=course, students=students)

@teacher_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@teacher_required
def profile():
    """الملف الشخصي للمعلم"""
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
                return redirect(url_for('teacher.profile'))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ في تحديث الملف الشخصي', 'error')
    
    return render_template('teacher/profile.html', form=form)

@teacher_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
@teacher_required
def change_password():
    """تغيير كلمة المرور"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = generate_password_hash(form.new_password.data)
            try:
                db.session.commit()
                flash('تم تغيير كلمة المرور بنجاح', 'success')
                return redirect(url_for('teacher.profile'))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ في تغيير كلمة المرور', 'error')
        else:
            flash('كلمة المرور الحالية غير صحيحة', 'error')
    
    return render_template('teacher/change_password.html', form=form)
