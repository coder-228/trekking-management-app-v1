from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from models import User, Staff, Admin
    # user_id format: "role_id"
    if '_' not in user_id:
        return None
    role, uid = user_id.split('_', 1)
    uid = int(uid)
    if role == 'user':
        return User.query.get(uid)
    elif role == 'staff':
        return Staff.query.get(uid)
    elif role == 'admin':
        return Admin.query.get(uid)
    return None
