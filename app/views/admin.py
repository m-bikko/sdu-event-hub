from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import User, Club, Location, Event
from app.forms import AddStudentForm
from functools import wraps
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

# Decorator to restrict access to admin users
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('events.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    # Get counts for dashboard
    user_count = User.query.count()
    club_count = Club.query.count()
    event_count = Event.query.count()
    location_count = Location.query.count()
    
    # Get recent events
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    
    # Get users with club head role
    club_heads = User.query.filter_by(role='club_head').all()
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count,
                          club_count=club_count,
                          event_count=event_count,
                          location_count=location_count,
                          recent_events=recent_events,
                          club_heads=club_heads)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def user_list():
    users = User.query.order_by(User.last_name).all()
    return render_template('admin/user_list.html', users=users)

@admin_bp.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/user_detail.html', user=user)

@admin_bp.route('/admin/user/<int:user_id>/set-role', methods=['POST'])
@login_required
@admin_required
def set_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['student', 'club_head']:
        user.role = new_role
        db.session.commit()
        flash(f'Role updated to {new_role} for {user.get_full_name()}.', 'success')
    else:
        flash('Invalid role specified.', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user.id))

@admin_bp.route('/admin/user/<int:user_id>/generate-share-token', methods=['POST'])
@login_required
@admin_required
def generate_share_token(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        # Generate a new token using our new UserShareToken model
        token = user.generate_share_token()
        
        if token:
            flash(f'Share token generated for {user.get_full_name()}.', 'success')
        else:
            flash('Failed to generate share token.', 'danger')
    except Exception as e:
        flash(f'Error generating share token: {str(e)}', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user.id))

@admin_bp.route('/admin/add-student', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    form = AddStudentForm()
    
    if form.validate_on_submit():
        # Process form data
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data,
            sdu_id=form.sdu_id.data if form.sdu_id.data else None,
            role=form.role.data
        )
        
        # Handle photo upload if provided
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join(current_app.root_path, 'static/profile_pics', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)  # Ensure directory exists
            form.photo.data.save(photo_path)
            user.photo_url = url_for('static', filename=f'profile_pics/{photo_filename}')
        else:
            # Set default profile image
            user.photo_url = url_for('static', filename='images/default-profile.png')
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Student {user.get_full_name()} has been added successfully!', 'success')
        return redirect(url_for('admin.user_list'))
    
    return render_template('admin/add_student.html', form=form)

@admin_bp.route('/admin/clubs')
@login_required
@admin_required
def club_list():
    clubs = Club.query.order_by(Club.name).all()
    return render_template('admin/club_list.html', clubs=clubs)

@admin_bp.route('/admin/club/<int:club_id>')
@login_required
@admin_required
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    # Get all users to select potential club head
    users = User.query.filter_by(role='club_head').order_by(User.last_name).all()
    return render_template('admin/club_detail.html', club=club, users=users)

@admin_bp.route('/admin/club/<int:club_id>/update', methods=['POST'])
@login_required
@admin_required
def update_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    club.name = request.form.get('name')
    club.description = request.form.get('description')
    head_user_id = request.form.get('head_user_id')
    if head_user_id:
        club.head_user_id = int(head_user_id)
    
    db.session.commit()
    flash(f'Club {club.name} has been updated.', 'success')
    return redirect(url_for('admin.club_detail', club_id=club.id))

@admin_bp.route('/admin/club/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_club():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        head_user_id = request.form.get('head_user_id')
        
        club = Club(
            name=name,
            description=description,
            head_user_id=int(head_user_id) if head_user_id else None
        )
        
        db.session.add(club)
        db.session.commit()
        flash(f'Club {name} has been created.', 'success')
        return redirect(url_for('admin.club_list'))
    
    # Get all club head users for selection
    users = User.query.filter_by(role='club_head').order_by(User.last_name).all()
    return render_template('admin/create_club.html', users=users)

@admin_bp.route('/admin/locations')
@login_required
@admin_required
def location_list():
    locations = Location.query.order_by(Location.name).all()
    return render_template('admin/location_list.html', locations=locations)

@admin_bp.route('/admin/location/<int:location_id>')
@login_required
@admin_required
def location_detail(location_id):
    location = Location.query.get_or_404(location_id)
    return render_template('admin/location_detail.html', location=location)

@admin_bp.route('/admin/location/<int:location_id>/update', methods=['POST'])
@login_required
@admin_required
def update_location(location_id):
    location = Location.query.get_or_404(location_id)
    
    location.name = request.form.get('name')
    try:
        location.capacity_min = int(request.form.get('capacity_min', 0))
        location.capacity_max = int(request.form.get('capacity_max', 0))
    except ValueError:
        flash('Capacity must be a number.', 'danger')
        return redirect(url_for('admin.location_detail', location_id=location.id))
    
    db.session.commit()
    flash(f'Location {location.name} has been updated.', 'success')
    return redirect(url_for('admin.location_detail', location_id=location.id))

@admin_bp.route('/admin/location/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_location():
    if request.method == 'POST':
        name = request.form.get('name')
        try:
            capacity_min = int(request.form.get('capacity_min', 0))
            capacity_max = int(request.form.get('capacity_max', 0))
        except ValueError:
            flash('Capacity must be a number.', 'danger')
            return redirect(url_for('admin.create_location'))
        
        location = Location(
            name=name,
            capacity_min=capacity_min,
            capacity_max=capacity_max
        )
        
        db.session.add(location)
        db.session.commit()
        flash(f'Location {name} has been created.', 'success')
        return redirect(url_for('admin.location_list'))
    
    return render_template('admin/create_location.html')