from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Event, Ticket
from app.services.payment_service import create_checkout_session, handle_checkout_completed
from app.services.telegram_service import send_ticket_confirmation
import os
import qrcode
from datetime import datetime
import stripe

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/buy-ticket/<int:event_id>', methods=['GET', 'POST'])
@login_required
def buy_ticket(event_id):
    # For GET requests, redirect to event detail page
    if request.method == 'GET':
        return redirect(url_for('events.event_detail', event_id=event_id))
    # Get the event
    event = Event.query.get_or_404(event_id)
    
    # Check if event is full
    if event.is_full():
        return jsonify({"error": "This event is fully booked."}), 400
    
    # Check if user already has a ticket
    existing_ticket = Ticket.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if existing_ticket:
        return jsonify({"error": "You are already registered for this event."}), 400
    
    # For free events, this endpoint shouldn't be called directly
    if event.is_free():
        return jsonify({"error": "This is a free event. Please use the register endpoint."}), 400
    
    # Create a pending ticket
    ticket = Ticket(
        event_id=event.id,
        user_id=current_user.id,
        status='pending'
    )
    db.session.add(ticket)
    db.session.commit()
    
    # Create Stripe checkout session
    session = create_checkout_session(
        event_id=event.id,
        user_id=current_user.id
    )
    
    if not session:
        # Rollback ticket creation if session creation fails
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({"error": "Failed to create payment session."}), 500
    
    return jsonify({"sessionId": session.id})

@payments_bp.route('/payment-success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    return render_template('payments/success.html', session_id=session_id)

@payments_bp.route('/payment-cancel')
@login_required
def payment_cancel():
    session_id = request.args.get('session_id')
    return render_template('payments/cancel.html', session_id=session_id)

@payments_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    # Get the webhook payload and signature
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')
    
    # Verify webhook signature and extract the event
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400
    
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Process the payment
        success = handle_checkout_completed(session)
        
        if success:
            # Get the ticket that was just updated
            user_id = int(session.get('metadata', {}).get('user_id'))
            event_id = int(session.get('metadata', {}).get('event_id'))
            ticket = Ticket.query.filter_by(user_id=user_id, event_id=event_id, status='paid').first()
            
            if ticket:
                # Generate QR code for the ticket
                qr_data = f"ticket:{ticket.id}:{user_id}:{event_id}"
                qr = qrcode.make(qr_data)
                
                # Save QR code to file
                qr_path = os.path.join(current_app.root_path, 'static', 'qr_codes', f"qr_{ticket.id}.png")
                qr.save(qr_path)
                
                # Update ticket record with QR code path
                ticket.qr_code_path = url_for('static', filename=f'qr_codes/qr_{ticket.id}.png')
                db.session.commit()
                
                # Send notification to user via Telegram
                send_ticket_confirmation(
                    user_id=user_id,
                    event_name=ticket.event.name,
                    qr_code_url=ticket.qr_code_path
                )
    
    return 'OK', 200
