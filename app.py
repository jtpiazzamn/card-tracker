from flask import Flask
from flask_login import LoginManager
from models import db, User
from dotenv import load_dotenv
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Flask 3 removed `Markup` from `flask`. Some dependencies (e.g. Flask-WTF) still import it.
# Provide a runtime shim so those imports continue to work.
try:
    import flask as _flask
    from markupsafe import Markup
    _flask.Markup = Markup
except Exception:
    pass

from flask_wtf import CSRFProtect

load_dotenv()

limiter = Limiter(get_remote_address, default_limits=["200 per day", "50 per hour"])
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    limiter.init_app(app)
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY environment variable is required for security. Set it in your environment or in a .env file.')
    app.config['SECRET_KEY'] = secret_key

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_PERMANENT'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    with app.app_context():
        db.create_all()
        # Migrate: add market_price_updated_at column to existing card tables
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE card ADD COLUMN market_price_updated_at DATETIME'
                ))
                conn.commit()
        except Exception:
            pass  # Column already exists — safe to ignore

    return app

if __name__ == '__main__':
    app = create_app()
    debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    app.run(debug=debug)
