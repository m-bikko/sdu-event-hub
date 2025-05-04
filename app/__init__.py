import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configure login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.views.auth import auth_bp
    from app.views.admin import admin_bp
    from app.views.student import student_bp
    from app.views.club_head import club_head_bp
    from app.views.events import events_bp
    from app.views.payments import payments_bp
    from app.views.notifications import notifications_bp
    from app.views.chatbot import chatbot_bp
    from app.views.api import api_bp
    from app.views.telegram import telegram_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(club_head_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(telegram_bp)

    # Create directories if they don't exist
    os.makedirs(os.path.join(app.static_folder, 'qr_codes'), exist_ok=True)
    
    # Run database migrations
    with app.app_context():
        from app.migrations import run_migrations
        try:
            run_migrations()
        except Exception as e:
            app.logger.error(f"Error running migrations: {e}")

    return app
