from flask import Blueprint, jsonify, request, current_app, url_for, flash, redirect, render_template
from flask_login import current_user, login_required
from app import db
from app.models import User
from app.services.telegram_service import (
    generate_telegram_connect_code, 
    verify_telegram_connect_code,
    send_notification,
    start_bot
)
import os

telegram_bp = Blueprint('telegram', __name__, url_prefix='/telegram')

@telegram_bp.route('/link', methods=['GET', 'POST'])
@login_required
def link_telegram():
    """Generate a linking code for Telegram integration."""
    if request.method == 'GET':
        # Show telegram linking page
        return render_template('student/telegram_link.html')
    
    # Generate a unique code for connecting Telegram account
    code = generate_telegram_connect_code(current_user.id)
    
    if code:
        return jsonify({
            'code': code,
            'bot_username': os.environ.get('TELEGRAM_BOT_USERNAME', 'SDUEventHubBot')
        })
    else:
        return jsonify({'error': 'Could not generate connection code'}), 500

@telegram_bp.route('/unlink', methods=['POST'])
@login_required
def unlink_telegram():
    """Unlink the user's Telegram account."""
    if not current_user.telegram_chat_id:
        return jsonify({'error': 'No Telegram account is linked to your profile'}), 400
    
    # Store the chat_id to send a notification
    chat_id = current_user.telegram_chat_id
    
    # Clear Telegram information
    current_user.telegram_chat_id = None
    current_user.telegram_connect_code = None
    db.session.commit()
    
    # Notify the user that their account was unlinked
    message = (
        "Your SDU Event Hub account has been unlinked from Telegram.\n\n"
        "You will no longer receive notifications for events. "
        "If you wish to link again in the future, you can generate a new code from your profile."
    )
    send_notification(chat_id, message)
    
    return jsonify({'success': 'Your Telegram account has been unlinked'})

@telegram_bp.route('/status', methods=['GET'])
@login_required
def telegram_status():
    """Get the user's Telegram connection status."""
    status = {
        'is_linked': bool(current_user.telegram_chat_id),
        'chat_id': current_user.telegram_chat_id,
    }
    return jsonify(status)

@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Webhook for Telegram messages (for production use).
    
    This endpoint will be set up to receive updates from Telegram instead of polling.
    It should match the URL provided to the Telegram API in the setWebhook method.
    """
    # In production, this would process incoming webhook requests from Telegram
    # Since we're using polling mode in development, this is a placeholder
    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400
    
    # Log the request for debugging
    current_app.logger.info(f"Received Telegram webhook: {request.json}")
    
    # Return 200 OK to acknowledge receipt
    return jsonify({'success': True})

@telegram_bp.route('/start', methods=['GET'])
@login_required
def start_telegram_bot():
    """Start the Telegram bot (admin only)."""
    if current_user.role != 'admin':
        flash('You do not have permission to start the Telegram bot.', 'danger')
        return redirect(url_for('events.index'))
    
    try:
        # Start the bot in a background thread
        start_bot()
        flash('Telegram bot started successfully!', 'success')
    except Exception as e:
        flash(f'Error starting Telegram bot: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))