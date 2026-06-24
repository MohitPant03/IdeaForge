from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.routes.auth import auth
    from app.routes.ideas import ideas
    from app.routes.profile import profile
    
    app.register_blueprint(auth)
    app.register_blueprint(ideas)
    app.register_blueprint(profile)

    with app.app_context():
        db.create_all()

    return app