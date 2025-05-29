import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure the database
    database_url = os.environ.get("DATABASE_URL", "sqlite:///student_management.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    with app.app_context():
        # Import models to ensure tables are created
        import models
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        from models import User, Course
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                full_name='مدير النظام',
                phone='1234567890'
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Default admin user created: admin/admin123")
        
        # Create default teacher user if not exists
        teacher = User.query.filter_by(username='teacher').first()
        if not teacher:
            teacher_user = User(
                username='teacher',
                email='teacher@example.com',
                password_hash=generate_password_hash('123456'),
                role='teacher',
                full_name='أحمد محمد - معلم',
                phone='0501234567'
            )
            db.session.add(teacher_user)
            db.session.commit()
            logging.info("Default teacher user created: teacher/123456")
        
        # Create sample courses if none exist
        if Course.query.count() == 0:
            teacher_user = User.query.filter_by(role='teacher').first()
            sample_courses = [
                {
                    'name': 'دورة البرمجة الأساسية',
                    'description': 'دورة تعليمية شاملة لأساسيات البرمجة وعلوم الحاسوب',
                    'teacher_id': teacher_user.id if teacher_user else None,
                    'duration_hours': 40,
                    'fee': 1500.0,
                    'max_students': 25,
                    'is_active': True
                },
                {
                    'name': 'دورة تطوير المواقع',
                    'description': 'تعلم تطوير المواقع الإلكترونية باستخدام HTML وCSS وJavaScript',
                    'teacher_id': teacher_user.id if teacher_user else None,
                    'duration_hours': 60,
                    'fee': 2000.0,
                    'max_students': 20,
                    'is_active': True
                },
                {
                    'name': 'دورة قواعد البيانات',
                    'description': 'أساسيات قواعد البيانات وSQL والتصميم',
                    'teacher_id': teacher_user.id if teacher_user else None,
                    'duration_hours': 30,
                    'fee': 1200.0,
                    'max_students': 30,
                    'is_active': True
                },
                {
                    'name': 'دورة الذكاء الاصطناعي',
                    'description': 'مقدمة في الذكاء الاصطناعي والتعلم الآلي',
                    'teacher_id': teacher_user.id if teacher_user else None,
                    'duration_hours': 50,
                    'fee': 2500.0,
                    'max_students': 15,
                    'is_active': True
                }
            ]
            
            for course_data in sample_courses:
                course = Course(**course_data)
                db.session.add(course)
            
            db.session.commit()
            logging.info("Sample courses created successfully")
    
    # Register blueprints
    from routes import main_bp
    from auth import auth_bp
    from admin import admin_bp
    from teacher import teacher_bp
    from student import student_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    
    return app

# Create app instance
app = create_app()
