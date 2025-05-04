from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import current_user, login_required
from app import db
from app.models import Club, Event, Booking, Location, Genre, Tag, Ticket, User
from datetime import datetime, timedelta
from functools import wraps
import os
from werkzeug.utils import secure_filename

club_head_bp = Blueprint('club_head', __name__)

# Decorator to restrict access to club heads
def club_head_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'club_head':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('events.index'))
        return f(*args, **kwargs)
    return decorated_function

@club_head_bp.route('/club-head/dashboard')
@login_required
@club_head_required
def dashboard():
    # Get clubs headed by the current user
    clubs = Club.query.filter_by(head_user_id=current_user.id).all()
    
    # If not heading any clubs, show an error
    if not clubs:
        flash('You are not currently the head of any clubs.', 'warning')
        return redirect(url_for('events.index'))
    
    # Use the first club for now (in real app, might want to let user choose which club to manage)
    club = clubs[0]
    
    # Get upcoming events for this club
    upcoming_events = Event.query.filter(
        Event.club_id == club.id,
        Event.date_time > datetime.utcnow()
    ).order_by(Event.date_time).all()
    
    # Get past events for this club
    past_events = Event.query.filter(
        Event.club_id == club.id,
        Event.date_time <= datetime.utcnow()
    ).order_by(Event.date_time.desc()).limit(5).all()
    
    # Get recent bookings
    bookings = Booking.query.filter_by(club_id=club.id).order_by(Booking.start_time.desc()).limit(5).all()
    
    # Count club members
    member_count = len(club.members)
    
    return render_template('club_head/dashboard.html', 
                          club=club,
                          upcoming_events=upcoming_events,
                          past_events=past_events,
                          bookings=bookings,
                          member_count=member_count)

@club_head_bp.route('/club-head/events')
@login_required
@club_head_required
def events():
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    # Get all events for this club
    events = Event.query.filter_by(club_id=club.id).order_by(Event.date_time.desc()).all()
    
    # Add current datetime for template
    now = datetime.utcnow()
    
    return render_template('club_head/events.html', club=club, events=events, now=now)

@club_head_bp.route('/club-head/events/<int:event_id>')
@login_required
@club_head_required
def event_detail(event_id):
    # Get the event and verify it belongs to a club headed by current user
    event = Event.query.get_or_404(event_id)
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    if event.club_id != club.id:
        abort(403)  # Forbidden
    
    # Get list of attendees
    tickets = Ticket.query.filter_by(event_id=event.id).all()
    
    return render_template('club_head/event_detail.html', club=club, event=event, tickets=tickets)

@club_head_bp.route('/club-head/events/create', methods=['GET', 'POST'])
@login_required
@club_head_required
def create_event():
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        location_id = request.form.get('location_id')
        date = request.form.get('date')
        time = request.form.get('time')
        price = request.form.get('price')
        event_type = request.form.get('type')
        max_attendees = request.form.get('max_attendees')
        genre_ids = request.form.getlist('genres')
        tag_ids = request.form.getlist('tags')
        booking_id = request.form.get('booking_id')
        
        # Validate required fields
        if not all([name, description, location_id, date, time]):
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('club_head.create_event'))
        
        # Handle photo upload if provided
        photo_url = None
        if 'photo' in request.files and request.files['photo'].filename:
            photo = request.files['photo']
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(current_app.root_path, 'static/event_pics', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)  # Ensure directory exists
            photo.save(photo_path)
            photo_url = url_for('static', filename=f'event_pics/{photo_filename}')
        
        # Parse date and time
        try:
            date_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('club_head.create_event'))
        
        # Create event
        event = Event(
            name=name,
            description=description,
            club_id=club.id,
            location_id=int(location_id),
            date_time=date_time,
            price=float(price) if price else 0.0,
            max_attendees=int(max_attendees) if max_attendees else None,
            type=event_type,
            photo_url=photo_url,
            booking_id=int(booking_id) if booking_id else None
        )
        
        db.session.add(event)
        
        # Add genres
        if genre_ids:
            genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
            event.genres = genres
        
        # Add tags
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            event.tags = tags
        
        db.session.commit()
        
        # Update booking if provided
        if booking_id:
            booking = Booking.query.get(int(booking_id))
            if booking and booking.club_id == club.id:
                booking.status = 'confirmed'
                db.session.commit()
        
        # Send notifications to club subscribers via Telegram
        from app.services.telegram_service import send_event_notification
        send_event_notification(event.id, 'new')
        
        flash(f'Event "{name}" has been created successfully!', 'success')
        return redirect(url_for('club_head.events'))
    
    # Get data for form
    locations = Location.query.order_by(Location.name).all()
    genres = Genre.query.order_by(Genre.name).all()
    tags = Tag.query.order_by(Tag.name).all()
    
    # Get available bookings (not yet assigned to an event)
    bookings = Booking.query.filter_by(
        club_id=club.id,
        status='pending'
    ).order_by(Booking.start_time).all()
    
    return render_template('club_head/create_event.html', 
                          club=club,
                          locations=locations,
                          genres=genres,
                          tags=tags,
                          bookings=bookings)

@club_head_bp.route('/club-head/bookings')
@login_required
@club_head_required
def bookings():
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    # Get all bookings for this club
    bookings = Booking.query.filter_by(club_id=club.id).order_by(Booking.start_time.desc()).all()
    
    # Add current datetime for template
    now = datetime.utcnow()
    
    return render_template('club_head/bookings.html', club=club, bookings=bookings, now=now)

@club_head_bp.route('/club-head/bookings/create', methods=['GET', 'POST'])
@login_required
@club_head_required
def create_booking():
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        # Get form data
        location_id = request.form.get('location_id')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        # Validate required fields
        if not all([location_id, date, start_time, end_time]):
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('club_head.create_booking'))
        
        # Parse date and times
        try:
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('club_head.create_booking'))
        
        # Validate end time is after start time
        if end_datetime <= start_datetime:
            flash('End time must be after start time.', 'danger')
            return redirect(url_for('club_head.create_booking'))
        
        # Check for booking conflicts
        conflicts = Booking.query.filter(
            Booking.location_id == int(location_id),
            Booking.status != 'cancelled',
            db.or_(
                # New booking starts during an existing booking
                db.and_(
                    Booking.start_time <= start_datetime,
                    Booking.end_time > start_datetime
                ),
                # New booking ends during an existing booking
                db.and_(
                    Booking.start_time < end_datetime,
                    Booking.end_time >= end_datetime
                ),
                # New booking completely contains an existing booking
                db.and_(
                    Booking.start_time >= start_datetime,
                    Booking.end_time <= end_datetime
                )
            )
        ).first()
        
        if conflicts:
            flash('This time slot is already booked. Please choose another time.', 'danger')
            return redirect(url_for('club_head.create_booking'))
        
        # Create booking
        booking = Booking(
            location_id=int(location_id),
            club_id=club.id,
            start_time=start_datetime,
            end_time=end_datetime,
            status='pending',
            created_by_user_id=current_user.id
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Location booking created successfully! Please create an event within 24 hours to confirm this reservation.', 'success')
        return redirect(url_for('club_head.bookings'))
    
    # Get data for form
    locations = Location.query.order_by(Location.name).all()
    
    # Add current datetime for template
    now = datetime.utcnow()
    
    return render_template('club_head/create_booking.html', 
                          club=club, 
                          locations=locations,
                          now=now)

@club_head_bp.route('/club-head/members')
@login_required
@club_head_required
def members():
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    # Get all members of this club
    members = club.members
    
    return render_template('club_head/members.html', club=club, members=members)

@club_head_bp.route('/club-head/members/add', methods=['POST'])
@login_required
@club_head_required
def add_member():
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    # Get the user to add
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('No user specified.', 'danger')
        return redirect(url_for('club_head.members'))
    
    user = User.query.get_or_404(int(user_id))
    
    # Check if user is already a member
    if user in club.members:
        flash(f'{user.get_full_name()} is already a member of {club.name}.', 'info')
    else:
        # Add user to club members
        club.members.append(user)
        db.session.commit()
        flash(f'{user.get_full_name()} has been added to {club.name}.', 'success')
    
    return redirect(url_for('club_head.members'))

@club_head_bp.route('/club-head/members/remove/<int:user_id>', methods=['POST'])
@login_required
@club_head_required
def remove_member(user_id):
    # Get the club headed by the current user
    club = Club.query.filter_by(head_user_id=current_user.id).first_or_404()
    
    # Get the user to remove
    user = User.query.get_or_404(user_id)
    
    # Check if user is a member
    if user not in club.members:
        flash(f'{user.get_full_name()} is not a member of {club.name}.', 'warning')
    elif user.id == current_user.id:
        flash('You cannot remove yourself from the club.', 'danger')
    else:
        # Remove user from club members
        club.members.remove(user)
        db.session.commit()
        flash(f'{user.get_full_name()} has been removed from {club.name}.', 'success')
    
    return redirect(url_for('club_head.members'))
