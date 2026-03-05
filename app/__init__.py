from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'gooutandtouchgrass'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SESSION_PERMANENT'] = False
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'resumes')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
   

    db.init_app(app)
    login.init_app(app)

    from app.admin import admin_bp
    from app.company import company_bp
    from app.student import student_bp
    from app.miscellaneous import main_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(main_bp)

    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    with app.app_context():
        from app import model
        model.create_db_and_seed()

    return app


