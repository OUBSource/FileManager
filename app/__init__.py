from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import timedelta
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # Указываем, что шаблоны лежат в папке ../res, а статика в ../static
    app = Flask(__name__, template_folder='../res', static_folder='../static')
    
    # Настройки
    app.config['SECRET_KEY'] = 'super-secret-key-casa-os-clone'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12) # Сессия 12 часов
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.index'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Регистрация путей (Blueprints)
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Создание БД при первом запуске
    with app.app_context():
        db.create_all()

    return app