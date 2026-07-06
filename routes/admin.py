from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from extensions import db
from models import Admin, Staff, User, Trek, Booking
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.count()
    total_staff = Staff.query.count()
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='Booked').count()
    recent_treks = Trek.query.order_by(Trek.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    easy_count = Trek.query.filter_by(difficulty='Easy').count()
    moderate_count = Trek.query.filter_by(difficulty='Moderate').count()
    hard_count = Trek.query.filter_by(difficulty='Hard').count()

    # Stats by status
    status_stats = {}
    for status in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']:
        status_stats[status] = Trek.query.filter_by(status=status).count()

    return render_template('admin/dashboard.html',
        total_treks=total_treks, total_users=total_users,
        total_staff=total_staff, total_bookings=total_bookings,
        active_bookings=active_bookings, recent_treks=recent_treks,
        recent_bookings=recent_bookings, easy_count=easy_count,
        moderate_count=moderate_count, hard_count=hard_count,
        status_stats=status_stats)

@admin_bp.route('/treks')
@login_required
@admin_required
def treks():
    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '')
    status = request.args.get('status', '')

    query = Trek.query
    if search:
        query = query.filter(
            Trek.name.ilike(f'%{search}%') | Trek.location.ilike(f'%{search}%')
        )
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if status:
        query = query.filter_by(status=status)

    treks = query.order_by(Trek.created_at.desc()).all()
    all_staff = Staff.query.filter_by(status='active').all()
    return render_template('admin/treks.html', treks=treks, staff_list=all_staff,
                           search=search, difficulty=difficulty, status=status)

@admin_bp.route('/staff')
@login_required
@admin_required
def staff():
    search = request.args.get('search', '').strip()
    #query = Staff.query.filter_by(status='active')
    query = Staff.query
    if search:
        query = query.filter(
            Staff.name.ilike(f'%{search}%') | Staff.username.ilike(f'%{search}%')
        )
    staff_list = query.order_by(Staff.created_at.desc()).all()
    return render_template('admin/staff.html', staff_list=staff_list, search=search)
