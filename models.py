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


class Trek(db.Model):
    __tablename__ = 'treks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), nullable=False)  # Easy, Moderate, Hard
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, default=0.0)
    altitude = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Open, Closed, Completed
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='trek', lazy=True)

    @property
    def booked_slots(self):
        return self.total_slots - self.available_slots

    @property
    def completion_percent(self):
        if self.total_slots == 0:
            return 0
        return int((self.booked_slots / self.total_slots) * 100)
    
    @property
    def average_rating(self):
        if not self.reviews:
            return 0

        total = sum(r.rating for r in self.reviews)
        return round(total / len(self.reviews), 1)


    @property
    def review_count(self):
        return len(self.reviews)


class Booking(db.Model):
    __tablename__ = 'bookings'
    __table_args__ = (db.UniqueConstraint('user_id','trek_id',name='unique_user_booking'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')  # Booked, Cancelled, Completed
    num_participants = db.Column(db.Integer, default=1)
    special_requirements = db.Column(db.Text)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)   # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="reviews")
    trek = db.relationship("Trek", backref="reviews")
    __table_args__ = (
        db.UniqueConstraint('user_id', 'trek_id', name='unique_user_review'),
    )
