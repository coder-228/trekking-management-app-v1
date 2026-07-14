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


@staff_bp.route('/treks/<int:trek_id>')
@login_required
@staff_required
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user.id:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.treks'))
    bookings = Booking.query.filter_by(trek_id=trek_id, status='Booked').all()
    reviews = Review.query.filter_by(trek_id=trek_id).order_by(Review.created_at.desc()).all()
    return render_template('staff/trek_detail.html', trek=trek, bookings=bookings, reviews=reviews)


@staff_bp.route('/treks/<int:trek_id>/update', methods=['POST'])
@login_required
@staff_required
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('staff.treks'))

    new_status = request.form.get('status', '')
    new_total = request.form.get('total_slots', '')

    if new_status:
        allowed = ['Open', 'Closed', 'Completed']
        if new_status not in allowed:
            flash('Invalid status.', 'danger')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))
        if trek.status == 'Completed':
            flash('Cannot change status of a completed trek.', 'danger')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))
        trek.status = new_status

    if new_total and new_total.isdigit():
        total = int(new_total)
        booked = trek.booked_slots
        if total < booked:
            flash(f'Total slots cannot be less than booked participants ({booked}).', 'danger')
            return redirect(url_for('staff.trek_detail', trek_id=trek_id))
        trek.total_slots = total
        trek.available_slots = total - booked

    trek.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Trek updated successfully!', 'success')
    return redirect(url_for('staff.trek_detail', trek_id=trek_id))


@staff_bp.route('/treks/<int:trek_id>/participants')
@login_required
@staff_required
def participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('staff.treks'))
    bookings = Booking.query.filter_by(trek_id=trek_id).order_by(Booking.booking_date).all()
    return render_template('staff/participants.html', trek=trek, bookings=bookings)


@staff_bp.route('/profile')
@login_required
@staff_required
def profile():
    return render_template('staff/profile.html', staff=current_user)

@staff_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', '').strip()
        current_user.email = request.form.get('email', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        exp = request.form.get('experience_years', '0')
        current_user.experience_years = int(exp) if exp.isdigit() else 0
        current_user.specialization = request.form.get('specialization', '').strip()

        new_password = request.form.get('new_password', '')

        if new_password:
            if len(new_password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("staff/edit_profile.html", staff=current_user)
            current_user.set_password(new_password)
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("staff.profile"))
    return render_template("staff/edit_profile.html",staff=current_user)
