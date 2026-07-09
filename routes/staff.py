from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import Trek, Booking, User, Review
from datetime import datetime

staff_bp = Blueprint('staff', __name__)


def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            flash('Staff access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    assigned_treks = Trek.query.filter_by(staff_id=current_user.id).all()
    total_participants = 0
    for trek in assigned_treks:
        total_participants += trek.booked_slots
    open_treks = [t for t in assigned_treks if t.status == 'Open']
    return render_template('staff/dashboard.html',
        assigned_treks=assigned_treks,
        total_participants=total_participants,
        open_treks=open_treks)


@staff_bp.route('/treks')
@login_required
@staff_required
def treks():
    assigned_treks = Trek.query.filter_by(staff_id=current_user.id).order_by(Trek.start_date).all()
    return render_template('staff/treks.html', treks=assigned_treks)
