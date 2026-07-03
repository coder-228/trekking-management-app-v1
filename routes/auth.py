from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Staff, Admin

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = None

        # Check Admin
        user = Admin.query.filter((Admin.username == username) | (Admin.email == username)).first()

        # Check Staff
        if not user:
            user = Staff.query.filter((Staff.username == username) | (Staff.email == username)).first()

        # Check Trekker/User
        if not user:
            user = User.query.filter((User.username == username) | (User.email == username)).first()

        if user and user.check_password(password):
            # Staff approval
            if isinstance(user, Staff):
                if user.status == "pending":
                    flash("Your account is awaiting admin approval.", "warning")
                    return render_template("auth/login.html")

                if user.status == "blacklisted":
                    flash("Your account has been blacklisted.", "danger")
                    return render_template("auth/login.html")

            # Trekker blacklist
            if isinstance(user, User):
                if user.status == "blacklisted":
                    flash("Your account has been blacklisted.", "danger")
                    return render_template("auth/login.html")

            login_user(user)

            flash(f"Welcome back, {user.name}!", "success")
            
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for(f"{user.role}.dashboard"))
        flash("Invalid username/email or password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        age = request.form.get('age', '')
        role = request.form.get('role', 'user')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not name:
            errors.append('Name is required.')
        if (User.query.filter_by(username=username).first() or
            Staff.query.filter_by(username=username).first() or
            Admin.query.filter_by(username=username).first()):
            errors.append('Username already taken.')

        if (User.query.filter_by(email=email).first() or
            Staff.query.filter_by(email=email).first() or
            Admin.query.filter_by(email=email).first()):
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html')

        if role == "staff":
            account = Staff(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                phone=phone,
                status="pending"
            )

        else:
            account = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                phone=phone,
                age=int(age) if age.isdigit() else None,
                status="active"
            )
        db.session.add(account)
        db.session.commit()
        if role == "staff":
            flash("Registration successful! Your account is awaiting admin approval.","success")
        else:
            flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
