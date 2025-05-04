from app import db
from app.models import User, Event, Ticket, Attendance, Review
from datetime import datetime, timedelta

def calculate_user_social_gpa(user_id):
    """
    Calculates a user's Social GPA based on event participation, club activities, and feedback.
    Focuses on last 6 months of activity.
    
    Args:
        user_id (int): The user's ID.
        
    Returns:
        float: The calculated Social GPA (0.0 to 5.0).
    """
    user = User.query.get(user_id)
    if not user:
        return 0.0
    
    # Define the time window (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Get all tickets for user in the last 6 months
    tickets = Ticket.query.filter(
        Ticket.user_id == user_id,
        Ticket.purchase_time >= six_months_ago
    ).all()
    
    if not tickets:
        return 0.0  # No activity in last 6 months
    
    # Base metrics
    total_events = len(tickets)
    attended_events = sum(1 for t in tickets if t.status == 'attended')
    absent_events = sum(1 for t in tickets if t.status == 'absent')
    club_events = sum(1 for t in tickets if t.event.type == 'club')
    general_events = sum(1 for t in tickets if t.event.type == 'general')
    
    # Get user's reviews
    reviews = Review.query.filter(
        Review.user_id == user_id,
        Review.created_at >= six_months_ago
    ).count()
    
    # Calculate attendance rate (more important for club events)
    attendance_rate = attended_events / total_events if total_events > 0 else 0
    
    # Calculate weights for different factors
    # This is a simplified calculation for the prototype
    # A real implementation would have more sophisticated weights and factors
    
    # Base points from attendance
    base_points = attendance_rate * 3.0  # Up to 3.0 points for perfect attendance
    
    # Bonus for club events (more important than general events)
    club_bonus = (club_events / total_events) * 1.0 if total_events > 0 else 0  # Up to 1.0 extra point
    
    # Penalty for absences (especially club events)
    absence_penalty = (absent_events / total_events) * 1.5 if total_events > 0 else 0  # Up to 1.5 point reduction
    
    # Bonus for being active and leaving reviews
    review_bonus = min(reviews / 5, 1) * 0.5  # Up to 0.5 points for 5+ reviews
    
    # Special bonus for club heads
    club_head_bonus = 0.5 if user.is_club_head() else 0
    
    # Calculate final Social GPA (capped between 0 and 5)
    social_gpa = base_points + club_bonus - absence_penalty + review_bonus + club_head_bonus
    
    # Ensure it's within the valid range
    social_gpa = max(0, min(5, social_gpa))
    
    # Update the user's Social GPA
    user.social_gpa = social_gpa
    db.session.commit()
    
    return social_gpa

def update_social_gpa_for_attendance(ticket_id, attended=True):
    """
    Updates a user's Social GPA when they attend/miss an event.
    
    Args:
        ticket_id (int): The ticket ID.
        attended (bool): Whether the user attended (True) or missed (False) the event.
        
    Returns:
        float: The updated Social GPA.
    """
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return None
    
    # Update ticket status
    ticket.status = 'attended' if attended else 'absent'
    
    # If attended, create attendance record
    if attended and not ticket.attendance:
        attendance = Attendance(ticket_id=ticket.id)
        db.session.add(attendance)
    
    # Award bonus points for attendance
    user = ticket.user
    event = ticket.event
    
    if attended:
        # Points depend on event type
        points = 50 if event.type == 'club' else 10
        user.add_bonus_points(points, 'attendance', event.id)
    
    db.session.commit()
    
    # Recalculate Social GPA
    return calculate_user_social_gpa(user.id)

def update_club_ratings():
    """
    Updates all club ratings based on their events' ratings.
    Should be run periodically.
    
    Returns:
        int: The number of clubs updated.
    """
    from app.models import Club
    
    clubs = Club.query.all()
    updated_count = 0
    
    for club in clubs:
        # Get all club events with ratings
        events_with_ratings = [e for e in club.events if e.rating > 0]
        
        if events_with_ratings:
            # Calculate average rating
            total_rating = sum(e.rating for e in events_with_ratings)
            avg_rating = total_rating / len(events_with_ratings)
            
            # Update club rating
            club.rating = avg_rating
            updated_count += 1
    
    db.session.commit()
    return updated_count
