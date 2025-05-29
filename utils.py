import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, flash
from PIL import Image
import io
from functools import wraps
from flask_login import current_user
from datetime import datetime
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# الملفات المسموحة للرفع
ALLOWED_EXTENSIONS = {
    'images': {'png', 'jpg', 'jpeg', 'gif'},
    'documents': {'pdf', 'doc', 'docx', 'txt'},
    'profiles': {'png', 'jpg', 'jpeg'}
}

def allowed_file(filename, file_type='images'):
    """التحقق من نوع الملف المسموح"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def save_uploaded_file(file, subfolder='uploads', max_size=(800, 800)):
    """
    حفظ الملف المرفوع مع تصغير الصور
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename, subfolder):
        flash('نوع الملف غير مسموح', 'error')
        return None
    
    # إنشاء اسم ملف فريد
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{file_extension}"
    
    # إنشاء مجلد فرعي إذا لم يكن موجود
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    
    filepath = os.path.join(upload_path, filename)
    
    try:
        # إذا كان ملف صورة، قم بتصغيره
        if subfolder in ['images', 'profiles'] and file_extension in ['png', 'jpg', 'jpeg']:
            image = Image.open(file.stream)
            
            # تحويل RGBA إلى RGB إذا لزم الأمر
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # تصغير الصورة مع الحفاظ على النسبة
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # حفظ الصورة المحسنة
            image.save(filepath, optimize=True, quality=85)
        else:
            # حفظ الملف كما هو
            file.save(filepath)
        
        return f"{subfolder}/{filename}"
    
    except Exception as e:
        current_app.logger.error(f"خطأ في حفظ الملف: {str(e)}")
        flash('حدث خطأ في رفع الملف', 'error')
        return None

def admin_required(f):
    """ديكوريتر للتحقق من صلاحيات المدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """ديكوريتر للتحقق من صلاحيات المعلم"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """ديكوريتر للتحقق من صلاحيات الطالب"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def format_date(date_value, format_string='%Y-%m-%d'):
    """تنسيق التاريخ"""
    if date_value:
        return date_value.strftime(format_string)
    return ''

def format_datetime(datetime_value, format_string='%Y-%m-%d %H:%M'):
    """تنسيق التاريخ والوقت"""
    if datetime_value:
        return datetime_value.strftime(format_string)
    return ''

def calculate_age(birth_date):
    """حساب العمر"""
    if birth_date:
        today = datetime.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return None

def get_payment_status_text(status):
    """تحويل حالة الدفع إلى نص عربي"""
    status_map = {
        'pending': 'معلق',
        'paid': 'مدفوع',
        'partial': 'جزئي'
    }
    return status_map.get(status, status)

def get_attendance_status_text(status):
    """تحويل حالة الحضور إلى نص عربي"""
    status_map = {
        'present': 'حاضر',
        'absent': 'غائب',
        'late': 'متأخر',
        'excused': 'معذور'
    }
    return status_map.get(status, status)

def get_grade_type_text(grade_type):
    """تحويل نوع التقييم إلى نص عربي"""
    type_map = {
        'exam': 'امتحان',
        'quiz': 'اختبار قصير',
        'assignment': 'واجب',
        'project': 'مشروع'
    }
    return type_map.get(grade_type, grade_type)

def create_pdf_report(title, headers, data, filename=None):
    """إنشاء تقرير PDF"""
    try:
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # إنشاء المستند
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # الأنماط
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            spaceAfter=30,
            alignment=1  # وسط
        )
        
        # العنوان
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # الجدول
        if data:
            table_data = [headers] + data
            table = Table(table_data)
            
            # تنسيق الجدول
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        # بناء المستند
        doc.build(story)
        return filename
        
    except Exception as e:
        current_app.logger.error(f"خطأ في إنشاء تقرير PDF: {str(e)}")
        return None

def export_to_csv(headers, data, filename=None):
    """تصدير البيانات إلى CSV"""
    try:
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(data)
        
        return filename
        
    except Exception as e:
        current_app.logger.error(f"خطأ في تصدير CSV: {str(e)}")
        return None

def validate_phone_number(phone):
    """التحقق من صحة رقم الهاتف"""
    import re
    # نمط بسيط للتحقق من رقم الهاتف السعودي
    pattern = r'^(05|5)[0-9]{8}$'
    return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None

def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_student_id():
    """توليد رقم طالب فريد"""
    from models import User
    year = datetime.now().year
    
    # البحث عن آخر رقم طالب في هذا العام
    last_student = User.query.filter(
        User.role == 'student',
        User.username.like(f'{year}%')
    ).order_by(User.id.desc()).first()
    
    if last_student and last_student.username.startswith(str(year)):
        try:
            last_number = int(last_student.username[4:])
            new_number = last_number + 1
        except:
            new_number = 1
    else:
        new_number = 1
    
    return f"{year}{new_number:04d}"

def send_notification(user_id, title, message):
    """إرسال إشعار للمستخدم"""
    try:
        from models import Notification
        from app import db
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message
        )
        
        db.session.add(notification)
        db.session.commit()
        return True
        
    except Exception as e:
        current_app.logger.error(f"خطأ في إرسال الإشعار: {str(e)}")
        return False

def calculate_gpa(grades):
    """حساب المعدل التراكمي"""
    if not grades:
        return 0.0
    
    total_points = 0
    total_hours = 0
    
    for grade in grades:
        grade_points = (grade.grade / grade.max_grade) * 4.0  # تحويل إلى نظام 4.0
        total_points += grade_points
        total_hours += 1  # افتراض أن كل مادة لها وزن متساوي
    
    return round(total_points / total_hours, 2) if total_hours > 0 else 0.0

def get_grade_letter(percentage):
    """تحويل النسبة المئوية إلى درجة حرفية"""
    if percentage >= 95:
        return 'A+'
    elif percentage >= 90:
        return 'A'
    elif percentage >= 85:
        return 'B+'
    elif percentage >= 80:
        return 'B'
    elif percentage >= 75:
        return 'C+'
    elif percentage >= 70:
        return 'C'
    elif percentage >= 65:
        return 'D+'
    elif percentage >= 60:
        return 'D'
    else:
        return 'F'

def backup_database():
    """نسخ احتياطي لقاعدة البيانات"""
    try:
        import shutil
        from datetime import datetime
        
        # اسم ملف النسخة الاحتياطية
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join('backups', backup_name)
        
        # إنشاء مجلد النسخ الاحتياطية
        os.makedirs('backups', exist_ok=True)
        
        # نسخ قاعدة البيانات
        shutil.copy2('student_management.db', backup_path)
        
        return backup_path
        
    except Exception as e:
        current_app.logger.error(f"خطأ في النسخ الاحتياطي: {str(e)}")
        return None
