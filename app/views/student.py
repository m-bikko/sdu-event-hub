from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.models import Ticket, User, Review, Club, Event
from app.forms import ProfileUpdateForm
from app.services.telegram_service import generate_telegram_connect_code
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import and_

student_bp = Blueprint('student', __name__)

@student_bp.route('/profile')
@login_required
def profile():
    # Get user's tickets (upcoming and past)
    now = datetime.utcnow()
    
    # Query for upcoming tickets
    upcoming_tickets = Ticket.query.filter_by(user_id=current_user.id).join(
        Ticket.event
    ).filter(
        Event.date_time > now
    ).order_by(Event.date_time.asc()).all()
    
    # Query for past tickets
    past_tickets = Ticket.query.filter_by(user_id=current_user.id).join(
        Ticket.event
    ).filter(
        Event.date_time <= now
    ).order_by(Event.date_time.desc()).all()
    
    # Get clubs the user is a member of
    clubs = current_user.clubs
    
    # Get the user's subscribed clubs
    subscriptions = current_user.club_subscriptions
    
    return render_template('student/profile.html', 
                          user=current_user,
                          upcoming_tickets=upcoming_tickets,
                          past_tickets=past_tickets,
                          clubs=clubs,
                          subscriptions=subscriptions)

@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileUpdateForm()
    # Need to set it to make the validation work
    form.user_id = current_user.id
    
    if form.validate_on_submit():
        # Handle profile photo upload if provided
        if form.photo.data:
            photo_filename = secure_filename(form.photo.data.filename)
            photo_path = os.path.join(current_app.root_path, 'static/profile_pics', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)  # Ensure directory exists
            form.photo.data.save(photo_path)
            current_user.photo_url = url_for('static', filename=f'profile_pics/{photo_filename}')
        
        # Update user details
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        if form.sdu_id.data:
            current_user.sdu_id = form.sdu_id.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('student.profile'))
    elif request.method == 'GET':
        # Populate form with current data
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.sdu_id.data = current_user.sdu_id
    
    return render_template('student/edit_profile.html', form=form)

@student_bp.route('/tickets')
@login_required
def tickets():
    # Get all tickets for the current user
    now = datetime.utcnow()
    
    # Query for upcoming tickets
    upcoming_tickets = Ticket.query.filter_by(user_id=current_user.id).join(
        Ticket.event
    ).filter(
        Event.date_time > now
    ).order_by(Event.date_time.asc()).all()
    
    # Query for past tickets
    past_tickets = Ticket.query.filter_by(user_id=current_user.id).join(
        Ticket.event
    ).filter(
        Event.date_time <= now
    ).order_by(Event.date_time.desc()).all()
    
    return render_template('student/tickets.html', 
                          upcoming_tickets=upcoming_tickets,
                          past_tickets=past_tickets)

@student_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    # Get the ticket and verify it belongs to the current user
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id:
        abort(403)  # Forbidden
    
    # Check if the user can leave a review (event is in the past and no review exists)
    can_review = False
    existing_review = None
    
    if ticket.event.date_time < datetime.utcnow():
        # Check if a review already exists
        existing_review = Review.query.filter_by(
            user_id=current_user.id,
            event_id=ticket.event.id
        ).first()
        can_review = not existing_review and ticket.status in ['paid', 'attended']
    
    return render_template('student/ticket_detail.html', 
                          ticket=ticket,
                          can_review=can_review,
                          existing_review=existing_review)

@student_bp.route('/leave-review/<int:event_id>', methods=['POST'])
@login_required
def leave_review(event_id):
    # Verify the user attended the event
    ticket = Ticket.query.filter(
        and_(
            Ticket.user_id == current_user.id,
            Ticket.event_id == event_id,
            Ticket.status.in_(['paid', 'attended'])  # User must have attended
        )
    ).first_or_404()
    
    # Check if the event has passed
    if ticket.event.date_time > datetime.utcnow():
        flash('You cannot review an event that has not happened yet.', 'danger')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    # Check if user already reviewed this event
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this event.', 'info')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    # Get the rating and comment from the form
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5).', 'danger')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    # Create the review
    review = Review(
        user_id=current_user.id,
        event_id=event_id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(review)
    
    # Update event rating
    ticket.event.update_rating()
    
    # Update club rating (would typically be done by a scheduler, but for demo purposes, update on review)
    from app.services.social_gpa_calculator import update_club_ratings
    update_club_ratings()
    
    # Update user's social GPA
    from app.services.social_gpa_calculator import calculate_user_social_gpa
    calculate_user_social_gpa(current_user.id)
    
    # Add bonus points for leaving a review
    current_user.add_bonus_points(5, 'review', event_id)
    
    db.session.commit()
    
    flash('Thank you for your review!', 'success')
    return redirect(url_for('events.event_detail', event_id=event_id))

@student_bp.route('/profile/link-telegram', methods=['POST'])
@login_required
def link_telegram():
    # Generate a unique code for connecting Telegram account
    code = generate_telegram_connect_code(current_user.id)
    
    if code:
        return jsonify({
            'code': code,
            'bot_username': os.environ.get('TELEGRAM_BOT_USERNAME', 'SDUEventHubBot')
        })
    else:
        return jsonify({'error': 'Could not generate connection code'}), 500