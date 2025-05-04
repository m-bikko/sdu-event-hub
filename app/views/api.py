from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import User, Club
from sqlalchemy import or_

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/search/users', methods=['GET'])
@login_required
def search_users():
    """
    API endpoint to search for users by name or email.
    This is used by the club head to add members to their club.
    """
    # Get search query
    query = request.args.get('query', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Get the club headed by the current user (for club heads)
    club = None
    if current_user.role == 'club_head':
        club = Club.query.filter_by(head_user_id=current_user.id).first()
        
        if not club:
            return jsonify([])
    
    # Search for users matching the query
    search_pattern = f"%{query}%"
    users = User.query.filter(
        or_(
            User.first_name.ilike(search_pattern),
            User.last_name.ilike(search_pattern),
            User.email.ilike(search_pattern)
        )
    ).limit(10).all()
    
    # Filter out users who are already members of the club
    if club:
        existing_members = [member.id for member in club.members]
        users = [user for user in users if user.id not in existing_members]
    
    # Format the results
    results = []
    for user in users:
        results.append({
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'photo_url': user.photo_url or '/static/images/default-profile.png'
        })
    
    return jsonify(results)