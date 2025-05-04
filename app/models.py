from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

# Association tables for many-to-many relationships
club_membership = db.Table('club_membership',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('is_head', db.Boolean, default=False)
)

event_genre = db.Table('event_genre',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True)
)

event_tag = db.Table('event_tag',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

club_subscription = db.Table('club_subscription',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('subscribed_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sdu_id = db.Column(db.String(20), unique=True, nullable=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'admin', 'student', 'club_head'
    photo_url = db.Column(db.String(256), nullable=True)
    social_gpa = db.Column(db.Float, default=0.0)
    bonus_points = db.Column(db.Integer, default=0)
    telegram_chat_id = db.Column(db.String(32), unique=True, nullable=True)
    telegram_connect_code = db.Column(db.String(128), unique=True, nullable=True)
    # Remove the share_token property; we'll use a dedicated model instead
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clubs = db.relationship('Club', secondary=club_membership, lazy='subquery',
                           backref=db.backref('members', lazy=True))
    club_subscriptions = db.relationship('Club', secondary=club_subscription, lazy='subquery',
                                        backref=db.backref('subscribers', lazy=True))
    tickets = db.relationship('Ticket', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    bonus_transactions = db.relationship('UserBonusTransaction', backref='user', lazy=True)
    
    def __init__(self, first_name, last_name, email, password, role='student', sdu_id=None, photo_url=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.set_password(password)
        self.role = role
        self.sdu_id = sdu_id
        self.photo_url = photo_url
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def add_bonus_points(self, points, transaction_type, event_id=None):
        # Add points to user's balance
        self.bonus_points += points
        # Record transaction
        transaction = UserBonusTransaction(
            user_id=self.id,
            points_amount=points,
            type=transaction_type,
            related_event_id=event_id
        )
        db.session.add(transaction)
        db.session.commit()
    
    def update_social_gpa(self, new_contribution):
        # Simple calculation for demo
        # In a real app, a more complex algorithm would be used
        self.social_gpa = (self.social_gpa * 0.7) + (new_contribution * 0.3)
        db.session.commit()
        
    def is_admin(self):
        return self.role == 'admin'
    
    def is_club_head(self):
        return self.role == 'club_head'
    
    def generate_share_token(self):
        """Generate or regenerate a unique share token for this user.
        Returns the token string."""
        from sqlalchemy.exc import IntegrityError
        
        # First check if the user already has a token
        existing_token = UserShareToken.query.filter_by(user_id=self.id).first()
        
        if existing_token:
            # Update the existing token
            import secrets
            existing_token.token = secrets.token_urlsafe(32)
            db.session.commit()
            return existing_token.token
        else:
            # Create a new token
            new_token = UserShareToken(user_id=self.id)
            db.session.add(new_token)
            
            try:
                db.session.commit()
                return new_token.token
            except IntegrityError:
                # If there's an integrity error (unlikely), rollback and try again
                db.session.rollback()
                return self.generate_share_token()  # Recursive call, should fix itself
    
    def get_share_token(self):
        """Get the user's share token if it exists, or None."""
        token_obj = UserShareToken.query.filter_by(user_id=self.id).first()
        return token_obj.token if token_obj else None
    
    def get_share_url(self, _external=True):
        """Get the URL for sharing this user's profile, or None if no token exists."""
        from flask import url_for
        
        token = self.get_share_token()
        if not token:
            return None
            
        return url_for('events.user_public_profile', token=token, _external=_external)
    
    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(256), nullable=True)
    head_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    head = db.relationship('User', foreign_keys=[head_user_id], backref='headed_clubs')
    events = db.relationship('Event', backref='club', lazy=True)
    bookings = db.relationship('Booking', backref='club', lazy=True)
    
    @staticmethod
    def get_by_name(name):
        """Fetches a club by its exact name (case-sensitive)."""
        return Club.query.filter_by(name=name).first()
    
    @staticmethod
    def get_all_names():
        """Returns a list of all club names."""
        return [club.name for club in Club.query.all()]
    
    def __repr__(self):
        return f'<Club {self.name}>'


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity_min = db.Column(db.Integer, default=0)
    capacity_max = db.Column(db.Integer, nullable=True)
    
    # Relationships
    events = db.relationship('Event', backref='location', lazy=True)
    bookings = db.relationship('Booking', backref='location', lazy=True)
    
    @staticmethod
    def get_by_name(name):
         """Fetches a location by its exact name (case-sensitive)."""
         return Location.query.filter_by(name=name).first()
    
    def __repr__(self):
        return f'<Location {self.name}>'


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Genre {self.name}>'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Tag {self.name}>'


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(256), nullable=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, default=0.0)
    max_attendees = db.Column(db.Integer, nullable=True)
    type = db.Column(db.String(20), default='general')  # 'club', 'general'
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    
    # Relationships
    genres = db.relationship('Genre', secondary=event_genre, lazy='subquery',
                           backref=db.backref('events', lazy=True))
    tags = db.relationship('Tag', secondary=event_tag, lazy='subquery',
                         backref=db.backref('events', lazy=True))
    booking = db.relationship('Booking', foreign_keys=[booking_id])
    tickets = db.relationship('Ticket', backref='event', lazy=True)
    reviews = db.relationship('Review', backref='event', lazy=True)
    
    def is_free(self):
        return self.price == 0
    
    def is_full(self):
        if self.max_attendees is None:
            return False
        return len(self.tickets) >= self.max_attendees
    
    def is_upcoming(self):
        return self.date_time > datetime.utcnow()
    
    def update_rating(self):
        if self.reviews.count() > 0:
            total_rating = sum(review.rating for review in self.reviews)
            self.rating = total_rating / self.reviews.count()
            db.session.commit()
    
    @classmethod
    def get_todays_events(cls):
        today = datetime.utcnow().date()
        return cls.query.filter(
            db.func.date(cls.date_time) == today
        ).order_by(cls.date_time).all()
    
    @staticmethod
    def get_upcoming_events(time_window_days=7):
        """Fetches events from now up to time_window_days in the future."""
        now = datetime.utcnow()
        future_time = now + timedelta(days=time_window_days)
        return Event.query.filter(
            Event.date_time >= now, 
            Event.date_time <= future_time
        ).order_by(Event.date_time).all()
    
    @staticmethod
    def search_by_name(name_query):
        """Searches for events whose name contains the query string (case-insensitive)."""
        search_term = f"%{name_query}%"
        return Event.query.filter(Event.name.ilike(search_term)).all()
    
    def __repr__(self):
        return f'<Event {self.name}>'


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id])
    related_events = db.relationship('Event', foreign_keys='Event.booking_id', backref='related_booking')
    
    def __repr__(self):
        return f'<Booking {self.location.name} {self.start_time.strftime("%Y-%m-%d %H:%M")}>'


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'attended', 'absent', 'cancelled'
    qr_code_path = db.Column(db.String(256), nullable=True)
    purchase_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance = db.relationship('Attendance', backref='ticket', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<Ticket {self.user.get_full_name()} - {self.event.name}>'


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False, unique=True)
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance {self.ticket.user.get_full_name()} - {self.checkin_time.strftime("%Y-%m-%d %H:%M")}>'


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.user.get_full_name()} - {self.event.name} - {self.rating}>'


class UserBonusTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points_amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'attendance', 'redemption', etc.
    related_event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    related_event = db.relationship('Event', foreign_keys=[related_event_id])
    
    def __repr__(self):
        return f'<UserBonusTransaction {self.user.get_full_name()} - {self.points_amount} - {self.type}>'
        

class UserShareToken(db.Model):
    """Model for storing user share tokens separately from main User model.
    This allows us to have shareable links without altering the User table schema."""
    __tablename__ = 'user_share_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('share_token_obj', lazy=True, uselist=False))
    
    def __init__(self, user_id, token=None):
        self.user_id = user_id
        if not token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        else:
            self.token = token
    
    def __repr__(self):
        return f'<UserShareToken user_id={self.user_id} token={self.token[:10]}...>'