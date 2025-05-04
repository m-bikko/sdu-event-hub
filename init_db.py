#!/usr/bin/env python
import os
import sys
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Club, Location, Genre, Tag, Event, Booking

app = create_app()

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if database is already populated
        if User.query.count() > 0:
            print("Database already initialized. Use --force to reinitialize.")
            return
        
        print("Creating sample data...")
        
        # Create admin user
        admin = User(
            first_name="Admin",
            last_name="User",
            email="admin@sdu.edu.kz",
            password="admin123",
            role="admin"
        )
        db.session.add(admin)
        
        # Create locations
        locations = [
            Location(name="Red Hall", capacity_min=50, capacity_max=200),
            Location(name="Blue Hall", capacity_min=30, capacity_max=150),
            Location(name="Room D201", capacity_min=10, capacity_max=30),
            Location(name="Room D202", capacity_min=10, capacity_max=30),
            Location(name="Room I105", capacity_min=20, capacity_max=40),
            Location(name="Room I106", capacity_min=20, capacity_max=40)
        ]
        db.session.add_all(locations)
        
        # Create genres
        genres = [
            Genre(name="Technology"),
            Genre(name="Science"),
            Genre(name="Art"),
            Genre(name="Music"),
            Genre(name="Sports"),
            Genre(name="Business"),
            Genre(name="Literature"),
            Genre(name="Education")
        ]
        db.session.add_all(genres)
        
        # Create tags
        tags = [
            Tag(name="Workshop"),
            Tag(name="Lecture"),
            Tag(name="Conference"),
            Tag(name="Competition"),
            Tag(name="Concert"),
            Tag(name="Performance"),
            Tag(name="Hackathon"),
            Tag(name="Social"),
            Tag(name="Game"),
            Tag(name="Charity")
        ]
        db.session.add_all(tags)
        
        # Commit to get IDs
        db.session.commit()
        
        # Create sample students
        students = [
            User(first_name="John", last_name="Doe", email="john.doe@sdu.edu.kz", password="password", sdu_id="190103001", role="student"),
            User(first_name="Jane", last_name="Smith", email="jane.smith@sdu.edu.kz", password="password", sdu_id="190103002", role="student"),
            User(first_name="Alex", last_name="Johnson", email="alex.johnson@sdu.edu.kz", password="password", sdu_id="190103003", role="student"),
            User(first_name="Sara", last_name="Williams", email="sara.williams@sdu.edu.kz", password="password", sdu_id="190103004", role="student"),
            User(first_name="Michael", last_name="Brown", email="michael.brown@sdu.edu.kz", password="password", sdu_id="190103005", role="student"),
            User(first_name="Emily", last_name="Davis", email="emily.davis@sdu.edu.kz", password="password", sdu_id="190103006", role="club_head"),
            User(first_name="David", last_name="Miller", email="david.miller@sdu.edu.kz", password="password", sdu_id="190103007", role="club_head"),
            User(first_name="Sophia", last_name="Wilson", email="sophia.wilson@sdu.edu.kz", password="password", sdu_id="190103008", role="club_head"),
            User(first_name="Daniel", last_name="Taylor", email="daniel.taylor@sdu.edu.kz", password="password", sdu_id="190103009", role="club_head")
        ]
        db.session.add_all(students)
        db.session.commit()
        
        # Create clubs
        club_heads = User.query.filter_by(role="club_head").all()
        
        clubs = [
            Club(name="SDU ACM Chapter", description="Association for Computing Machinery student chapter at SDU.", head_user_id=club_heads[0].id),
            Club(name="SDU Debate Club", description="Platform for students to engage in formal debates and improve public speaking skills.", head_user_id=club_heads[1].id),
            Club(name="SDU Music Club", description="For students passionate about music, singing, and playing instruments.", head_user_id=club_heads[2].id),
            Club(name="SDU Innovation Hub", description="Fostering innovation and entrepreneurship among students.", head_user_id=club_heads[3].id)
        ]
        db.session.add_all(clubs)
        db.session.commit()
        
        # Set club memberships
        all_students = User.query.filter(User.role.in_(["student", "club_head"])).all()
        for club in clubs:
            # Add a few random members to each club
            import random
            members = random.sample(all_students, min(len(all_students), random.randint(3, 6)))
            club.members.extend(members)
            
            # Always add the club head as a member
            if club.head not in club.members:
                club.members.append(club.head)
        
        # Add some club subscriptions
        for student in all_students:
            # Subscribe to 1-3 random clubs
            subscriptions = random.sample(clubs, random.randint(1, min(3, len(clubs))))
            student.club_subscriptions.extend(subscriptions)
        
        db.session.commit()
        
        # Create bookings and events
        now = datetime.utcnow()
        
        # Create some past bookings and events
        for i in range(5):
            past_date = now - timedelta(days=i+1)
            
            # Create booking
            booking = Booking(
                location_id=random.choice(locations).id,
                club_id=random.choice(clubs).id,
                start_time=past_date.replace(hour=14, minute=0),
                end_time=past_date.replace(hour=16, minute=0),
                status="confirmed",
                created_by_user_id=random.choice(club_heads).id
            )
            db.session.add(booking)
            db.session.commit()
            
            # Create event using booking
            event = Event(
                name=f"Past Event {i+1}",
                description=f"This is a sample past event {i+1} for demonstration purposes.",
                club_id=booking.club_id,
                location_id=booking.location_id,
                date_time=booking.start_time,
                price=0.0 if i % 2 == 0 else 500.0,
                max_attendees=random.randint(20, 50),
                type="general" if i % 2 == 0 else "club",
                booking_id=booking.id
            )
            
            # Add random genres and tags
            event.genres = random.sample(genres, min(len(genres), random.randint(1, 3)))
            event.tags = random.sample(tags, min(len(tags), random.randint(1, 3)))
            
            db.session.add(event)
            db.session.commit()
        
        # Create upcoming events (for the next 7 days)
        for i in range(10):
            future_date = now + timedelta(days=random.randint(1, 7))
            
            # Create booking
            booking = Booking(
                location_id=random.choice(locations).id,
                club_id=random.choice(clubs).id,
                start_time=future_date.replace(hour=random.choice([10, 12, 14, 16, 18]), minute=0),
                end_time=future_date.replace(hour=random.choice([12, 14, 16, 18, 20]), minute=0),
                status="confirmed",
                created_by_user_id=random.choice(club_heads).id
            )
            
            if booking.end_time <= booking.start_time:
                booking.end_time = booking.start_time + timedelta(hours=2)
                
            db.session.add(booking)
            db.session.commit()
            
            # Create event using booking
            event = Event(
                name=f"Upcoming Event {i+1}",
                description=f"This is a sample upcoming event {i+1} for demonstration purposes. Join us for an exciting time!",
                club_id=booking.club_id,
                location_id=booking.location_id,
                date_time=booking.start_time,
                price=0.0 if i % 2 == 0 else 500.0,
                max_attendees=random.randint(20, 50),
                type="general" if i % 2 == 0 else "club",
                booking_id=booking.id
            )
            
            # Add random genres and tags
            event.genres = random.sample(genres, min(len(genres), random.randint(1, 3)))
            event.tags = random.sample(tags, min(len(tags), random.randint(1, 3)))
            
            db.session.add(event)
            db.session.commit()
        
        print("Sample data created successfully!")
        print("Admin login: admin@sdu.edu.kz / admin123")
        print("Student logins: [email]@sdu.edu.kz / password")

if __name__ == "__main__":
    # Check for force flag
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        with app.app_context():
            # This will drop all tables and recreate them
            db.drop_all()
            print("Database reset forced.")
    
    init_db()