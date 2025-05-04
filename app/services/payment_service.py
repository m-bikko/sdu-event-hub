import os
from datetime import datetime
from app import db
from app.models import Event, User, Ticket
import uuid

# Use environment variable for API key or fallback to config value
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_your_test_key")

# Flag to control whether to use mock responses instead of actual API
# Use mock mode by default during development
USE_MOCK = os.environ.get("USE_MOCK_STRIPE", "True").lower() == "true"

try:
    import stripe
    stripe.api_key = STRIPE_KEY
    IMPORT_SUCCESS = True
except ImportError:
    print("Warning: stripe package not available, using mock responses")
    IMPORT_SUCCESS = False
    USE_MOCK = True

class MockStripeSession:
    """Mock implementation of a Stripe session for demo/testing"""
    def __init__(self, event_id, user_id, amount_kzt, description):
        self.id = f"mock_stripe_sess_{uuid.uuid4()}"
        self.url = "#mock-stripe-checkout"
        self.metadata = {
            'event_id': event_id,
            'user_id': user_id,
        }
        self.amount_total = amount_kzt
        self.description = description
        print(f"[MOCK STRIPE] Created checkout session for event {event_id}, user {user_id}, amount {amount_kzt}")
        
    def get(self, key, default=None):
        """Mock implementation of dict-like access for session"""
        if key == 'metadata':
            return self.metadata
        return default

def create_checkout_session(event_id, user_id, amount_kzt=None, description=None):
    """
    Creates a Stripe Checkout session.
    
    Args:
        event_id (int): ID of the event.
        user_id (int): ID of the user.
        amount_kzt (int, optional): Amount in KZT (smallest unit). If None, will be calculated from event price.
        description (str, optional): Description of the ticket. If None, will be generated from event name.
        
    Returns:
        stripe.checkout.Session or MockStripeSession: The created session object, or None if an error occurred.
    """
    try:
        # Get event and user
        event = Event.query.get(event_id)
        user = User.query.get(user_id)
        
        if not event or not user:
            return None
        
        # Set amount if not provided
        if amount_kzt is None:
            amount_kzt = int(event.price * 100)  # Convert to smallest currency unit (tiyn)
            
        # Set description if not provided
        if description is None:
            description = f"Ticket for event: {event.name}"
        
        # Use mock session if requested or if import failed
        if USE_MOCK or not IMPORT_SUCCESS:
            mock_session = MockStripeSession(event_id, user_id, amount_kzt, description)
            
            # For mock sessions, auto-create the ticket as 'paid' immediately
            # This means we don't have to wait for a webhook that will never come in development
            ticket = Ticket.query.filter_by(
                user_id=user_id, 
                event_id=event_id, 
                status='pending'
            ).first()
            
            if ticket:
                # Update the ticket status
                ticket.status = 'paid'
                ticket.purchase_time = datetime.utcnow()
                
                # Generate and save QR code for the ticket
                try:
                    import qrcode
                    from flask import current_app
                    
                    # Generate QR code data
                    qr_data = f"ticket:{ticket.id}:{user_id}:{event_id}"
                    qr = qrcode.make(qr_data)
                    
                    # Ensure directory exists
                    import os
                    qr_dir = os.path.join(current_app.static_folder, 'qr_codes')
                    os.makedirs(qr_dir, exist_ok=True)
                    
                    # Save QR code to file
                    qr_path = os.path.join(current_app.static_folder, 'qr_codes', f"qr_{ticket.id}.png")
                    qr.save(qr_path)
                    
                    # Set QR code path in ticket
                    ticket.qr_code_path = f'/static/qr_codes/qr_{ticket.id}.png'
                except Exception as e:
                    print(f"[MOCK STRIPE] Error generating QR code: {e}")
                    # Set a placeholder path if QR generation fails
                    ticket.qr_code_path = f'/static/qr_codes/qr_{ticket.id}.png'
                
                db.session.commit()
                print(f"[MOCK STRIPE] Auto-marked ticket {ticket.id} as paid for testing")
            
            return mock_session
        
        # Get base URL from environment or config
        base_url = os.environ.get("BASE_URL", "http://localhost:5004")
        
        # Create Stripe session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'kzt',
                    'product_data': {
                        'name': description,
                    },
                    'unit_amount': amount_kzt,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{base_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/payment-cancel?session_id={{CHECKOUT_SESSION_ID}}",
            metadata={
                'event_id': event_id,
                'user_id': user_id,
            },
        )
        return session
    except Exception as e:
        print(f"Error creating Stripe session: {e}")
        return None

def handle_checkout_completed(session):
    """
    Handles the checkout.session.completed webhook event.
    
    Args:
        session (dict or MockStripeSession): The checkout session data from Stripe.
        
    Returns:
        bool: True if the ticket was successfully processed, False otherwise.
    """
    try:
        # Extract metadata
        user_id = int(session.get('metadata', {}).get('user_id'))
        event_id = int(session.get('metadata', {}).get('event_id'))
        
        # Find or create ticket
        ticket = Ticket.query.filter_by(
            user_id=user_id, 
            event_id=event_id, 
            status='pending'
        ).first()
        
        if not ticket:
            # Create new ticket if not found
            ticket = Ticket(
                event_id=event_id,
                user_id=user_id,
                status='pending'
            )
            db.session.add(ticket)
        
        # Update ticket status
        ticket.status = 'paid'
        ticket.purchase_time = datetime.utcnow()
        
        # Save to get the ticket ID if it's new
        db.session.commit()
        
        # Generate QR code path (actual QR generation happens in payments controller)
        ticket.qr_code_path = f'/static/qr_codes/qr_{ticket.id}.png'
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error processing checkout completion: {e}")
        db.session.rollback()
        return False

def verify_webhook_signature(payload, sig_header, webhook_secret):
    """
    Verifies the signature of a Stripe webhook.
    
    Args:
        payload (bytes): The raw request body.
        sig_header (str): The Stripe signature header.
        webhook_secret (str): The webhook signing secret.
        
    Returns:
        dict or None: The verified event, or None if verification failed.
    """
    if USE_MOCK or not IMPORT_SUCCESS:
        # For mock mode, just parse the payload as JSON
        import json
        try:
            return json.loads(payload)
        except:
            return None
    
    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError:
        # Invalid payload
        print("Invalid payload")
        return None
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        print("Invalid signature")
        return None