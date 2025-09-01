from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
cors = CORS()
socketio = SocketIO()

def create_app(config_name='development'):
    # Create Flask app with explicit template and static folders
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///lotoryjung.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = 'static/receipts'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cors.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'กรุณาเข้าสู่ระบบเพื่อเข้าถึงหน้านี้'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Template context processors
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        def current_lottery_period():
            """Return current lottery period in Thai format"""
            now = datetime.now()
            return f"{now.day:02d}/{now.month:02d}/{now.year + 543}"
        
        def format_currency(amount):
            """Format amount as Thai currency"""
            return f"{amount:,.0f} บาท"
        
        def format_thai_date(date):
            """Format date in Thai format"""
            if date:
                thai_year = date.year + 543
                return f"{date.day:02d}/{date.month:02d}/{thai_year}"
            return "-"
        
        return dict(
            current_lottery_period=current_lottery_period,
            format_currency=format_currency,
            format_thai_date=format_thai_date
        )

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

