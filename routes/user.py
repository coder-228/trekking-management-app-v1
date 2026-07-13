from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import Trek, Booking, User, Review
from datetime import datetime

user_bp = Blueprint('user', __name__)

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'user':
            flash('User access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    my_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    active_bookings = [b for b in my_bookings if b.status == 'Booked']
    open_treks = Trek.query.filter_by(status='Open').order_by(Trek.start_date).limit(6).all()
    return render_template('user/dashboard.html',
        my_bookings=my_bookings,
        active_bookings=active_bookings,
        open_treks=open_treks)

@user_bp.route('/treks')
@login_required
@user_required
def treks():
    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    query = Trek.query.filter_by(status='Open')
    if search:
        query = query.filter(Trek.name.ilike(f'%{search}%') | Trek.location.ilike(f'%{search}%'))
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    if min_price and min_price.replace('.','').isdigit():
        query = query.filter(Trek.price >= float(min_price))
    if max_price and max_price.replace('.','').isdigit():
        query = query.filter(Trek.price <= float(max_price))
    treks = query.order_by(Trek.start_date).all()
    user_booked_ids = {b.trek_id for b in Booking.query.filter_by(
        user_id=current_user.id, status='Booked').all()}

    return render_template('user/treks.html',
        treks=treks, search=search, difficulty=difficulty,
        location=location, user_booked_ids=user_booked_ids,
        min_price=min_price, max_price=max_price)


@user_bp.route('/treks/<int:trek_id>')
@login_required
@user_required
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek_id, status='Booked').first()
    return render_template('user/trek_detail.html', trek=trek, existing_booking=existing_booking)


@user_bp.route('/treks/<int:trek_id>/book', methods=['POST'])
@login_required
@user_required
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.status != 'Open':
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('user.trek_detail', trek_id=trek_id))
    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek_id, status='Booked').first()
    if existing:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('user.trek_detail', trek_id=trek_id))

    num_participants = int(request.form.get('num_participants', 1))
    special_requirements = request.form.get('special_requirements', '').strip()

    if trek.available_slots < num_participants:
        flash(f'Only {trek.available_slots} slots available.', 'danger')
        return redirect(url_for('user.trek_detail', trek_id=trek_id))

    booking = Booking(user_id=current_user.id,trek_id=trek_id,num_participants=num_participants,special_requirements=special_requirements,status='Booked')
    trek.available_slots -= num_participants
    db.session.add(booking)
    db.session.commit()
    flash(f'Successfully booked {trek.name}! 🎉', 'success')
    return redirect(url_for('user.bookings'))


@user_bp.route('/bookings')
@login_required
@user_required
def bookings():
    status_filter = request.args.get('status', '')
    query = Booking.query.filter_by(user_id=current_user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    my_bookings = query.order_by(Booking.booking_date.desc()).all()
    return render_template('user/bookings.html', bookings=my_bookings, status_filter=status_filter)

@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@user_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('user.bookings'))
    if booking.status != 'Booked':
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('user.bookings'))

    booking.status = 'Cancelled'
    booking.trek.available_slots += booking.num_participants
    db.session.commit()
    flash('Booking cancelled successfully.', 'info')
    return redirect(url_for('user.bookings'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@user_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        age = request.form.get('age', '')
        current_user.age = int(age) if age.isdigit() else None
        current_user.emergency_contact = request.form.get('emergency_contact', '').strip()
        current_user.emergency_phone = request.form.get('emergency_phone', '').strip()

        new_pass = request.form.get('new_password', '')
        if new_pass:
            if len(new_pass) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('user/profile.html')
            confirm = request.form.get('confirm_password', '')
            if new_pass != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('user/profile.html')
            current_user.set_password(new_pass)

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html')


@user_bp.route('/history')
@login_required
@user_required
def history():
    completed = Booking.query.filter_by(user_id=current_user.id, status='Completed').all()
    cancelled = Booking.query.filter_by(user_id=current_user.id, status='Cancelled').all()
    reviews = {
        review.trek_id: review
        for review in Review.query.filter_by(user_id=current_user.id).all()
    }
    return render_template('user/history.html', completed=completed, cancelled=cancelled, reviews=reviews)

@user_bp.route('/treks/<int:trek_id>/review', methods=['GET', 'POST'])
@login_required
@user_required
def review_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    booking = Booking.query.filter_by(trek_id=trek_id,user_id=current_user.id).first()
    if not booking:
        flash("You can only review treks you have booked.", "danger")
        return redirect(url_for("user.history"))

    if trek.status != "Completed":
        flash("You can only review completed treks.", "warning")
        return redirect(url_for("user.history"))

    review = Review.query.filter_by(trek_id=trek_id,user_id=current_user.id).first()
    if request.method == "POST":
        rating = request.form.get("rating")
        comment = request.form.get("comment", "").strip()

        if not rating:
            flash("Please provide a rating.", "danger")
            return redirect(url_for("user.review_trek", trek_id=trek_id))

        rating = int(rating)
        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5.", "danger")
            return redirect(url_for("user.review_trek", trek_id=trek_id))
        if review:
            review.rating = rating
            review.comment = comment
            flash("Review updated successfully!", "success")
        else:
            review = Review(user_id=current_user.id,trek_id=trek_id,rating=rating,comment=comment)
            db.session.add(review)
            flash("Thank you for your review!", "success")
        db.session.commit()
        return redirect(url_for("user.history"))
    return render_template("user/review.html", trek=trek,review=review)
