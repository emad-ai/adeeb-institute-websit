from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FloatField, IntegerField, DateField, RadioField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class StudentRegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('تأكيد كلمة المرور', 
                             validators=[DataRequired(), EqualTo('password', message='كلمات المرور غير متطابقة')])
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(max=100)])
    phone = StringField('رقم الجوال', validators=[DataRequired(), Length(max=20)])
    date_of_birth = DateField('تاريخ الميلاد', validators=[DataRequired()])
    gender = SelectField('الجنس', choices=[('male', 'ذكر'), ('female', 'أنثى')], validators=[DataRequired()])
    address = TextAreaField('العنوان', validators=[Optional()], widget=TextArea())
    profile_picture = FileField('الصورة الشخصية', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
    course_id = SelectField('الدورة', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('تسجيل')

class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(max=100)])
    phone = StringField('رقم الجوال', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('تاريخ الميلاد', validators=[Optional()])
    gender = SelectField('الجنس', choices=[('', 'اختر...'), ('male', 'ذكر'), ('female', 'أنثى')], validators=[Optional()])
    address = TextAreaField('العنوان', validators=[Optional()], widget=TextArea())
    role = SelectField('الدور', choices=[('student', 'طالب'), ('teacher', 'معلم'), ('admin', 'مدير')], validators=[DataRequired()])
    is_active = BooleanField('نشط')
    profile_picture = FileField('الصورة الشخصية', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
    submit = SubmitField('حفظ')

class CourseForm(FlaskForm):
    name = StringField('اسم الدورة', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('الوصف', validators=[Optional()], widget=TextArea())
    teacher_id = SelectField('المعلم', choices=[], coerce=int, validators=[Optional()])
    duration_hours = IntegerField('مدة الدورة (بالساعات)', validators=[Optional(), NumberRange(min=1)])
    start_date = DateField('تاريخ البداية', validators=[Optional()])
    end_date = DateField('تاريخ النهاية', validators=[Optional()])
    fee = FloatField('الرسوم', validators=[Optional(), NumberRange(min=0)])
    max_students = IntegerField('الحد الأقصى للطلاب', validators=[Optional(), NumberRange(min=1)], default=30)
    is_active = BooleanField('نشطة', default=True)
    submit = SubmitField('حفظ')

class AttendanceForm(FlaskForm):
    session_date = DateField('تاريخ الجلسة', validators=[DataRequired()])
    session_time = StringField('وقت الجلسة', validators=[Optional(), Length(max=20)])
    topic = StringField('موضوع الجلسة', validators=[Optional(), Length(max=200)])
    submit = SubmitField('إنشاء جلسة حضور')

class GradeForm(FlaskForm):
    assignment_name = StringField('اسم الواجب/الامتحان', validators=[DataRequired(), Length(max=100)])
    grade_type = SelectField('نوع التقييم', 
                           choices=[('exam', 'امتحان'), ('quiz', 'اختبار قصير'), 
                                  ('assignment', 'واجب'), ('project', 'مشروع')], 
                           validators=[DataRequired()])
    max_grade = FloatField('الدرجة الكاملة', validators=[DataRequired(), NumberRange(min=1)], default=100.0)
    notes = TextAreaField('ملاحظات', validators=[Optional()], widget=TextArea())
    submit = SubmitField('إضافة التقييم')

class EnrollmentForm(FlaskForm):
    student_id = SelectField('الطالب', choices=[], coerce=int, validators=[DataRequired()])
    course_id = SelectField('الدورة', choices=[], coerce=int, validators=[DataRequired()])
    payment_status = SelectField('حالة الدفع', 
                                choices=[('pending', 'معلق'), ('paid', 'مدفوع'), ('partial', 'جزئي')], 
                                validators=[DataRequired()])
    amount_paid = FloatField('المبلغ المدفوع', validators=[Optional(), NumberRange(min=0)], default=0.0)
    submit = SubmitField('تسجيل الطالب')

class ProfileUpdateForm(FlaskForm):
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الجوال', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('تاريخ الميلاد', validators=[Optional()])
    gender = SelectField('الجنس', choices=[('', 'اختر...'), ('male', 'ذكر'), ('female', 'أنثى')], validators=[Optional()])
    address = TextAreaField('العنوان', validators=[Optional()], widget=TextArea())
    profile_picture = FileField('الصورة الشخصية', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
    submit = SubmitField('تحديث الملف الشخصي')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', 
                                   validators=[DataRequired(), EqualTo('new_password', message='كلمات المرور غير متطابقة')])
    submit = SubmitField('تغيير كلمة المرور')


class TeacherEvaluationForm(FlaskForm):
    """نموذج تقييم المعلم"""
    teaching_quality = SelectField('جودة التدريس', 
                                 choices=[('1', 'ضعيف جداً'), ('2', 'ضعيف'), ('3', 'متوسط'), ('4', 'جيد'), ('5', 'ممتاز')],
                                 validators=[DataRequired()], coerce=int)
    
    communication = SelectField('التواصل والتفاعل', 
                              choices=[('1', 'ضعيف جداً'), ('2', 'ضعيف'), ('3', 'متوسط'), ('4', 'جيد'), ('5', 'ممتاز')],
                              validators=[DataRequired()], coerce=int)
    
    punctuality = SelectField('الالتزام بالوقت', 
                            choices=[('1', 'ضعيف جداً'), ('2', 'ضعيف'), ('3', 'متوسط'), ('4', 'جيد'), ('5', 'ممتاز')],
                            validators=[DataRequired()], coerce=int)
    
    knowledge = SelectField('المعرفة والخبرة', 
                          choices=[('1', 'ضعيف جداً'), ('2', 'ضعيف'), ('3', 'متوسط'), ('4', 'جيد'), ('5', 'ممتاز')],
                          validators=[DataRequired()], coerce=int)
    
    interaction = SelectField('التفاعل مع الطلاب', 
                            choices=[('1', 'ضعيف جداً'), ('2', 'ضعيف'), ('3', 'متوسط'), ('4', 'جيد'), ('5', 'ممتاز')],
                            validators=[DataRequired()], coerce=int)
    
    comments = TextAreaField('تعليقات وملاحظات', validators=[Optional(), Length(max=500)], widget=TextArea())
    suggestions = TextAreaField('اقتراحات للتحسين', validators=[Optional(), Length(max=500)], widget=TextArea())
    is_anonymous = BooleanField('تقييم مجهول', default=True)
    
    submit = SubmitField('إرسال التقييم')
