from flask import Flask
from extensions import db, login_manager
from models import User, Staff, Admin
#import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'trekking-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.staff import staff_bp
    from routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(user_bp, url_prefix='/user')
    with app.app_context():
        db.create_all()
        seed_admin()
    return app

def seed_admin():
    from models import Admin
    from werkzeug.security import generate_password_hash
    if not Admin.query.first():
        admin = Admin(username='admin',email='admin@trek.com',password_hash=generate_password_hash('admin123'),name='Super Admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin seeded: admin / admin123")
app = create_app()
if __name__ == '__main__':
    app.run(debug=False)
