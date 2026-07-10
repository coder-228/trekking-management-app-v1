from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from extensions import db
from models import Admin, Staff, User, Trek, Booking, Review
from datetime import datetime
from sqlalchemy import func

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

    revenue = 0
    completed_bookings = Booking.query.filter(Booking.status.in_(["Booked", "Completed"])).all()
    for booking in completed_bookings:
        revenue += booking.num_participants * booking.trek.price

    easy_bookings = Booking.query.join(Trek).filter(Trek.difficulty == "Easy",Booking.status.in_(["Booked", "Completed"])).count()
    moderate_bookings = Booking.query.join(Trek).filter(Trek.difficulty == "Moderate",Booking.status.in_(["Booked", "Completed"])).count()
    hard_bookings = Booking.query.join(Trek).filter(Trek.difficulty == "Hard",Booking.status.in_(["Booked", "Completed"])).count()

    difficulty_total = easy_bookings + moderate_bookings + hard_bookings
    if difficulty_total:
        easy_percent = int(easy_bookings * 100 / difficulty_total)
        moderate_percent = int(moderate_bookings * 100 / difficulty_total)
        hard_percent = int(hard_bookings * 100 / difficulty_total)
    else:
        easy_percent = 0
        moderate_percent = 0
        hard_percent = 0

    popular_treks = (db.session.query(Trek,func.count(Booking.id).label("bookings")).outerjoin(Booking)
        .group_by(Trek.id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
        .all()
    )

    highest_rated = (db.session.query(Trek,func.avg(Review.rating).label("avg_rating")
        ).join(Review)
        .group_by(Trek.id)
        .order_by(func.avg(Review.rating).desc())
        .first()
    )

    average_rating = db.session.query(func.avg(Review.rating)).scalar() or 0

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
        status_stats=status_stats,revenue=revenue,
        easy_percent=easy_percent,moderate_percent=moderate_percent,hard_percent=hard_percent,
        popular_treks=popular_treks,highest_rated=highest_rated,average_rating=average_rating)

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


@admin_bp.route('/treks/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trek():
    all_staff = Staff.query.filter_by(status='active').all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        difficulty = request.form.get('difficulty', '')
        duration_days = request.form.get('duration_days', '')
        total_slots = request.form.get('total_slots', '')
        price = request.form.get('price', '0')
        altitude = request.form.get('altitude', '').strip()
        status = request.form.get('status', 'Pending')
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        staff_id = request.form.get('staff_id', '')

        errors = []
        if not name: errors.append('Trek name is required.')
        if not location: errors.append('Location is required.')
        if not difficulty: errors.append('Difficulty is required.')
        if not duration_days or not duration_days.isdigit(): errors.append('Valid duration required.')
        if not total_slots or not total_slots.isdigit(): errors.append('Valid total slots required.')

        if errors:
            for e in errors: flash(e, 'danger')
            return render_template('admin/trek_form.html', staff_list=all_staff, trek=None)

        trek = Trek(
            name=name, location=location, description=description,
            difficulty=difficulty, duration_days=int(duration_days),
            total_slots=int(total_slots), available_slots=int(total_slots),
            price=float(price) if price else 0.0,
            altitude=altitude, status=status,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
            staff_id=int(staff_id) if staff_id else None
        )
        db.session.add(trek)
        db.session.commit()
        flash(f'Trek "{name}" created successfully!', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', staff_list=all_staff, trek=None)


@admin_bp.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    all_staff = Staff.query.filter_by(status='active').all()

    if request.method == 'POST':
        trek.name = request.form.get('name', '').strip()
        trek.location = request.form.get('location', '').strip()
        trek.description = request.form.get('description', '').strip()
        trek.difficulty = request.form.get('difficulty', '')
        duration = request.form.get('duration_days', '')
        total_slots = request.form.get('total_slots', '')
        trek.price = float(request.form.get('price', '0') or 0)
        trek.altitude = request.form.get('altitude', '').strip()
        old_status = trek.status
        new_status = request.form.get('status', 'Pending')
        trek.status = new_status
        if old_status != "Completed" and new_status == "Completed":
            for booking in trek.bookings:
                if booking.status == "Booked":
                    booking.status = "Completed"
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        staff_id = request.form.get('staff_id', '')

        if duration.isdigit():
            trek.duration_days = int(duration)
        if total_slots.isdigit():
            booked = trek.booked_slots
            new_total = int(total_slots)
            if new_total < booked:
                flash(f'Cannot reduce slots below booked count ({booked}).', 'danger')
                return render_template('admin/trek_form.html', trek=trek, staff_list=all_staff)
            trek.total_slots = new_total
            trek.available_slots = new_total - booked

        trek.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        trek.end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        trek.staff_id = int(staff_id) if staff_id else None
        trek.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Trek updated successfully!', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=trek, staff_list=all_staff)


@admin_bp.route('/treks/<int:trek_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    for booking in trek.bookings:
        booking.status = 'Cancelled'
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully.', 'success')
    return redirect(url_for('admin.treks'))


@admin_bp.route('/treks/<int:trek_id>/assign_staff', methods=['POST'])
@login_required
@admin_required
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_id = request.form.get('staff_id', '')
    trek.staff_id = int(staff_id) if staff_id else None
    db.session.commit()
    flash('Staff assigned successfully!', 'success')
    return redirect(url_for('admin.treks'))


# ---- STAFF MANAGEMENT ----

@admin_bp.route('/staff')
@login_required
@admin_required
def staff():
    search = request.args.get('search', '').strip()
    query = Staff.query
    if search:
        query = query.filter(
            Staff.name.ilike(f'%{search}%') | Staff.username.ilike(f'%{search}%')
        )
    staff_list = query.order_by(Staff.created_at.desc()).all()
    return render_template('admin/staff.html', staff_list=staff_list, search=search)

@admin_bp.route('/staff/pending')
@login_required
@admin_required
def pending_staff():
    search = request.args.get('search', '').strip()
    query = Staff.query.filter_by(status='pending')
    if search:
        query = query.filter(Staff.name.ilike(f'%{search}%') | Staff.username.ilike(f'%{search}%'))
    staff_list = query.order_by(Staff.created_at.desc()).all()
    return render_template('admin/pending_staff.html',staff_list=staff_list,search=search)

@admin_bp.route('/staff/<int:staff_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_staff_status(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if staff.status == "pending":
        staff.status = "active"
        flash(f"{staff.name} has been approved.", "success")
    elif staff.status == "active":
        staff.status = "blacklisted"
        flash(f"{staff.name} has been blacklisted.", "warning")
    elif staff.status == "blacklisted":
        staff.status = "active"
        flash(f"{staff.name} has been reactivated.", "success")
    db.session.commit()
    return redirect(url_for('admin.staff'))


@admin_bp.route('/staff/<int:staff_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    for trek in staff.treks:
        trek.staff_id = None
    db.session.delete(staff)
    db.session.commit()
    flash('Staff removed.', 'success')
    return redirect(url_for('admin.staff'))


# ---- USER MANAGEMENT ----

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    search = request.args.get('search', '').strip()
    query = User.query
    if search:
        query = query.filter(
            User.name.ilike(f'%{search}%') | User.username.ilike(f'%{search}%') | User.email.ilike(f'%{search}%')
        )
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, search=search)


@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'blacklisted' if user.status == 'active' else 'active'
    db.session.commit()
    flash(f'User status updated to {user.status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    bookings = query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings, search=search, status=status)
