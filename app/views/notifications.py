from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.services.telegram_service import send_reminders

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications/send-reminders', methods=['POST'])
@login_required
def manual_send_reminders():
    """Endpoint to manually trigger reminders (for demo purposes)"""
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Send reminders
    result = send_reminders()
    
    return jsonify(result)
