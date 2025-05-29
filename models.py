from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin, teacher, student
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    taught_courses = db.relationship('Course', backref='teacher', lazy=True)
    student_enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    grades = db.relationship('Grade', backref='student', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    duration_hours = db.Column(db.Integer)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    fee = db.Column(db.Float, default=0.0)
    max_students = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    attendance_sessions = db.relationship('AttendanceSession', backref='course', lazy=True)
    grades = db.relationship('Grade', backref='course', lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, partial
    amount_paid = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)

class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    session_time = db.Column(db.String(20))
    topic = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='session', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=False)
    status = db.Column(db.String(20), default='absent')  # present, absent, late, excused
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    assignment_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Float, nullable=False)
    max_grade = db.Column(db.Float, default=100.0)
    grade_type = db.Column(db.String(50))  # exam, quiz, assignment, project
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    
    # Relationship
    user = db.relationship('User', backref='documents')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notifications')


class TeacherEvaluation(db.Model):
    """نموذج تقييم المعلمين من قبل الطلاب"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # معايير التقييم (من 1 إلى 5)
    teaching_quality = db.Column(db.Integer, nullable=False)  # جودة التدريس
    communication = db.Column(db.Integer, nullable=False)     # التواصل
    punctuality = db.Column(db.Integer, nullable=False)       # الالتزام بالوقت
    knowledge = db.Column(db.Integer, nullable=False)         # المعرفة والخبرة
    interaction = db.Column(db.Integer, nullable=False)       # التفاعل مع الطلاب
    
    # التقييم العام والتعليقات
    overall_rating = db.Column(db.Float, nullable=False)      # التقييم العام (محسوب تلقائياً)
    comments = db.Column(db.Text)                             # تعليقات الطالب
    suggestions = db.Column(db.Text)                          # اقتراحات للتحسين
    
    # معلومات إضافية
    is_anonymous = db.Column(db.Boolean, default=True)        # هل التقييم مجهول؟
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    student = db.relationship('User', foreign_keys=[student_id], backref='given_evaluations')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='received_evaluations')
    course = db.relationship('Course', backref='evaluations')
    
    # فهرس فريد لمنع تقييم نفس المعلم أكثر من مرة في نفس الدورة
    __table_args__ = (db.UniqueConstraint('student_id', 'teacher_id', 'course_id', name='unique_evaluation'),)
    
    def calculate_overall_rating(self):
        """حساب التقييم العام"""
        total = self.teaching_quality + self.communication + self.punctuality + self.knowledge + self.interaction
        self.overall_rating = round(total / 5, 2)
        return self.overall_rating
    
    def get_rating_text(self):
        """تحويل التقييم الرقمي إلى نص"""
        if self.overall_rating >= 4.5:
            return "ممتاز"
        elif self.overall_rating >= 3.5:
            return "جيد جداً"
        elif self.overall_rating >= 2.5:
            return "جيد"
        elif self.overall_rating >= 1.5:
            return "مقبول"
        else:
            return "ضعيف"
