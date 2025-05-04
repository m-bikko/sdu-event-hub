import os
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, AdminLoginForm
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('events.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('events.index'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('events.index'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        # Check against hardcoded admin credentials for simplicity
        if form.username.data == Config.ADMIN_USERNAME and form.password.data == Config.ADMIN_PASSWORD:
            # Create admin user if doesn't exist
            admin = User.query.filter_by(email='admin@sdu.edu.kz').first()
            if not admin:
                admin = User(
                    first_name='Admin',
                    last_name='User',
                    email='admin@sdu.edu.kz',
                    password=Config.ADMIN_PASSWORD,
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
            
            login_user(admin)
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Admin login unsuccessful. Please check credentials.', 'danger')
    
    return render_template('auth/admin_login.html', title='Admin Login', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('events.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Handle profile photo upload if provided
        photo_filename = None
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join(current_app.root_path, 'static/profile_pics', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)  # Ensure directory exists
            form.photo.data.save(photo_path)
            photo_filename = url_for('static', filename=f'profile_pics/{photo_filename}')
        
        # Create new user
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data,
            sdu_id=form.sdu_id.data if form.sdu_id.data else None,
            photo_url=photo_filename,
            role='student'  # Default role
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('events.index'))
