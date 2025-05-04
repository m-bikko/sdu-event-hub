from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import current_user, login_required
from app import db
from app.models import Event, Club, Location, Tag, Genre, Ticket, User, UserShareToken
from datetime import datetime

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
@events_bp.route('/events')
def index():
    # Get filter parameters from query string
    club_id = request.args.get('club_id', type=int)
    genre_id = request.args.get('genre_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    location_id = request.args.get('location_id', type=int)
    search_query = request.args.get('q')
    
    # Base query - show upcoming events by default
    events_query = Event.query.filter(Event.date_time > datetime.utcnow())
    
    # Apply filters if provided
    if club_id:
        events_query = events_query.filter(Event.club_id == club_id)
    
    if genre_id:
        events_query = events_query.join(Event.genres).filter(Genre.id == genre_id)
    
    if tag_id:
        events_query = events_query.join(Event.tags).filter(Tag.id == tag_id)
    
    if location_id:
        events_query = events_query.filter(Event.location_id == location_id)
    
    if search_query:
        search_term = f'%{search_query}%'
        events_query = events_query.filter(
            db.or_(
                Event.name.ilike(search_term),
                Event.description.ilike(search_term)
            )
        )
    
    # Order by date
    events = events_query.order_by(Event.date_time).all()
    
    # Get recommended events (highest rated events coming soon)
    recommended_events = Event.query.filter(
        Event.date_time > datetime.utcnow()
    ).order_by(
        Event.rating.desc(),  # Highest rated first
        Event.date_time       # Then by date (soonest first)
    ).limit(3).all()
    
    # If we don't have enough recommended events based on rating,
    # get some random upcoming events by adding a random sort factor
    if len(recommended_events) < 3:
        more_events = Event.query.filter(
            Event.date_time > datetime.utcnow(),
            ~Event.id.in_([e.id for e in recommended_events])  # Not already in recommended
        ).order_by(
            db.func.random()  # Random selection
        ).limit(3 - len(recommended_events)).all()
        
        recommended_events.extend(more_events)
    
    # Get filter options for the form
    clubs = Club.query.order_by(Club.name).all()
    locations = Location.query.order_by(Location.name).all()
    genres = Genre.query.order_by(Genre.name).all()
    tags = Tag.query.order_by(Tag.name).all()
    
    return render_template('events/index.html', 
                          events=events,
                          recommended_events=recommended_events,
                          clubs=clubs,
                          locations=locations,
                          genres=genres,
                          tags=tags,
                          selected_club_id=club_id,
                          selected_genre_id=genre_id,
                          selected_tag_id=tag_id,
                          selected_location_id=location_id,
                          search_query=search_query)

@events_bp.route('/events/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user already has a ticket
    user_has_ticket = False
    if current_user.is_authenticated:
        ticket = Ticket.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        user_has_ticket = ticket is not None
    
    # Get similar events (same genre/tag or by same club)
    similar_events = []
    if event.genres:
        # Find events with the same primary genre
        primary_genre = event.genres[0] if event.genres else None
        if primary_genre:
            genre_similar = Event.query.join(Event.genres)\
                .filter(Genre.id == primary_genre.id)\
                .filter(Event.id != event.id)\
                .filter(Event.date_time > datetime.utcnow())\
                .limit(3).all()
            similar_events.extend(genre_similar)
    
    # Add events from same club if we need more
    if len(similar_events) < 3:
        club_similar = Event.query.filter(Event.club_id == event.club_id)\
            .filter(Event.id != event.id)\
            .filter(Event.date_time > datetime.utcnow())\
            .limit(3 - len(similar_events)).all()
        similar_events.extend(club_similar)
    
    return render_template('events/event_detail.html', 
                          event=event,
                          similar_events=similar_events,
                          user_has_ticket=user_has_ticket,
                          current_time=datetime.utcnow())

@events_bp.route('/clubs')
def clubs():
    clubs = Club.query.order_by(Club.name).all()
    return render_template('events/clubs.html', clubs=clubs)

@events_bp.route('/clubs/<int:club_id>')
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    
    # Get upcoming events for this club
    upcoming_events = Event.query.filter(
        Event.club_id == club.id,
        Event.date_time > datetime.utcnow()
    ).order_by(Event.date_time).all()
    
    # Check if user is already a member or subscribed
    is_member = False
    is_subscribed = False
    if current_user.is_authenticated:
        is_member = club in current_user.clubs
        is_subscribed = club in current_user.club_subscriptions
    
    return render_template('events/club_detail.html', 
                          club=club,
                          upcoming_events=upcoming_events,
                          is_member=is_member,
                          is_subscribed=is_subscribed)

@events_bp.route('/clubs/subscribe/<int:club_id>', methods=['POST'])
@login_required
def subscribe_to_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    if club in current_user.club_subscriptions:
        # Unsubscribe
        current_user.club_subscriptions.remove(club)
        db.session.commit()
        flash(f'You have unsubscribed from {club.name}.', 'info')
    else:
        # Subscribe
        current_user.club_subscriptions.append(club)
        db.session.commit()
        flash(f'You have subscribed to {club.name}. You will receive notifications about new events.', 'success')
    
    return redirect(url_for('events.club_detail', club_id=club.id))

@events_bp.route('/events/register/<int:event_id>', methods=['POST'])
@login_required
def register_for_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if event is full
    if event.is_full():
        flash('Sorry, this event is fully booked.', 'danger')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # Check if user already has a ticket
    existing_ticket = Ticket.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if existing_ticket:
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('events.event_detail', event_id=event.id))
    
    # For paid events, redirect to payment
    if event.price > 0:
        return redirect(url_for('payments.buy_ticket', event_id=event.id))
    
    # For free events, create ticket directly
    ticket = Ticket(
        event_id=event.id,
        user_id=current_user.id,
        status='confirmed',  # Free events are confirmed immediately
    )
    db.session.add(ticket)
    db.session.commit()
    
    flash(f'Successfully registered for {event.name}!', 'success')
    return redirect(url_for('student.tickets'))

@events_bp.route('/user/<string:token>')
def user_public_profile(token):
    """Public view to display user information and tickets via shareable link."""
    
    # First, find the share token object
    share_token = UserShareToken.query.filter_by(token=token).first()
    
    # If token not found, show error
    if not share_token:
        flash('Invalid or expired share token.', 'warning')
        return redirect(url_for('events.index'))
    
    # Get user from the token
    user = User.query.get(share_token.user_id)
    
    # If user not found (unlikely), show error
    if not user:
        flash('User not found. The token may be invalid.', 'warning')
        return redirect(url_for('events.index'))
    
    # Get user's upcoming events
    now = datetime.utcnow()
    upcoming_tickets = Ticket.query.filter_by(user_id=user.id).join(
        Ticket.event
    ).filter(
        Event.date_time > now
    ).order_by(Event.date_time.asc()).all()
    
    # Get past events the user attended
    past_tickets = Ticket.query.filter_by(user_id=user.id).join(
        Ticket.event
    ).filter(
        Event.date_time <= now
    ).order_by(Event.date_time.desc()).all()
    
    # Get the clubs the user is a member of
    clubs = user.clubs
    
    return render_template('events/public_profile.html',
                          user=user,
                          upcoming_tickets=upcoming_tickets, 
                          past_tickets=past_tickets,
                          clubs=clubs)
