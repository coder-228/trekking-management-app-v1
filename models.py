from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f'admin_{self.id}'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role(self):
        return 'admin'

    @property
    def is_active(self):
        return True


class Staff(UserMixin, db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    experience_years = db.Column(db.Integer, default=0)
    specialization = db.Column(db.String(200))
    status = db.Column(db.String(20),default="pending")# pending active blacklisted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    treks = db.relationship('Trek', backref='assigned_staff', lazy=True, foreign_keys='Trek.staff_id')

    def get_id(self):
        return f'staff_{self.id}'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def role(self):
        return 'staff'

    @property
    def is_active(self):
        return self.status == 'active'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    emergency_contact = db.Column(db.String(120))
    emergency_phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')  # active, blacklisted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def get_id(self):
        return f'user_{self.id}'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def role(self):
        return 'user'

    @property
    def is_active(self):
        return self.status == 'active'
