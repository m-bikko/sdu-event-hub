# app/views/chatbot.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.gemini_service import ask_gemini_with_context
from app.models import Event, Club, Location
from app import db
from datetime import datetime, timedelta

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chat')
@login_required
def chat():
    return render_template('chatbot/chat.html')

@chatbot_bp.route('/chatbot', methods=['POST'])
@login_required
def handle_chatbot_request():
    """
    Handles incoming chat messages from the frontend.
    Expects JSON payload: {"message": "User's message"}.
    Fetches relevant context from the DB and sends it to Gemini.
    Returns JSON payload: {"response": "Bot's response"}.
    """
    # Ensure the request content type is JSON
    if not request.is_json:
        return jsonify({"response": "Ошибка запроса: Ожидается JSON."}), 415  # Unsupported Media Type

    user_input = request.json.get('message')

    if not user_input or not isinstance(user_input, str) or user_input.strip() == "":
        return jsonify({"response": "Пожалуйста, введите сообщение."}), 400  # Bad Request

    # --- Dynamic Context Building Logic ---
    context_data_string = ""

    # Example: Always provide upcoming events as context
    try:
        # Fetch events happening from now into the near future (e.g., next 7 days)
        now = datetime.utcnow()
        future_window = now + timedelta(days=7)
        upcoming_events = Event.query.filter(
            Event.date_time >= now, 
            Event.date_time <= future_window
        ).order_by(Event.date_time).limit(10).all()  # Limit results

        if upcoming_events:
            context_data_string += "Вот список некоторых предстоящих мероприятий в SDU:\n"
            for event in upcoming_events:
                # Ensure event.club and event.location relations are loaded or fetched
                club_name = event.club.name if event.club else "Unknown Club"
                location_name = event.location.name if event.location else "Unknown Location"
                # Format the date/time nicely
                event_time_str = event.date_time.strftime('%d.%m %H:%M')
                price_str = f"{int(event.price)} KZT" if event.price > 0 else "Бесплатно"
                context_data_string += f"- '{event.name}' от клуба '{club_name}'. Когда: {event_time_str}. Где: {location_name}. Цена: {price_str}.\n"
            context_data_string += "\n"  # Add a newline for separation

    except Exception as e:
        print(f"Error fetching upcoming events for context: {e}")
        # Log the error but continue without this context

    # Try to identify club names in the user's input and provide club descriptions
    try:
        all_club_names = [club.name for club in Club.query.all()]
        matched_club_name = None
        for name in all_club_names:
            # Basic case-insensitive check
            if name.lower() in user_input.lower():
                matched_club_name = name
                break  # Take the first match for simplicity

        if matched_club_name:
            club_details = Club.query.filter_by(name=matched_club_name).first()
            if club_details and club_details.description:
                context_data_string += f"Информация о клубе '{club_details.name}': {club_details.description}\n\n"
                # Optional: Fetch and add upcoming events specifically for this club
                club_upcoming_events = Event.query.filter(
                    Event.club_id == club_details.id, 
                    Event.date_time >= now
                ).order_by(Event.date_time).limit(5).all()
                
                if club_upcoming_events:
                    context_data_string += f"Предстоящие мероприятия от клуба {club_details.name}:\n"
                    for event in club_upcoming_events:
                        event_time_str = event.date_time.strftime('%d.%m %H:%M')
                        context_data_string += f"- '{event.name}' в {event_time_str}\n"
                    context_data_string += "\n"

    except Exception as e:
        print(f"Error fetching club details for context: {e}")
        # Log the error but continue

    # Provide info about locations if location names are mentioned
    try:
        all_location_names = [loc.name for loc in Location.query.all()]
        matched_location_name = None
        for name in all_location_names:
            # Basic case-insensitive check
            if name.lower() in user_input.lower():
                matched_location_name = name
                break  # Take the first match for simplicity

        if matched_location_name:
            location_details = Location.query.filter_by(name=matched_location_name).first()
            if location_details:
                context_data_string += f"Информация о локации '{location_details.name}':\n"
                if hasattr(location_details, 'capacity_min') and hasattr(location_details, 'capacity_max'):
                    context_data_string += f"Вместимость: {location_details.capacity_min} - {location_details.capacity_max} человек\n"
                
                # Add upcoming events at this location
                location_upcoming_events = Event.query.filter(
                    Event.location_id == location_details.id, 
                    Event.date_time >= now
                ).order_by(Event.date_time).limit(5).all()
                
                if location_upcoming_events:
                    context_data_string += f"Предстоящие мероприятия в локации {location_details.name}:\n"
                    for event in location_upcoming_events:
                        event_time_str = event.date_time.strftime('%d.%m %H:%M')
                        context_data_string += f"- '{event.name}' в {event_time_str}\n"
                context_data_string += "\n"

    except Exception as e:
        print(f"Error fetching location details: {e}")
        # Log the error but continue

    # Add some general instructions to the AI
    context_data_string += "Пожалуйста, отвечай на русском языке и будь вежливым.\n"
    context_data_string += "Если ты не уверен в ответе на основе предоставленной информации, скажи об этом.\n"

    # Call the Gemini service with the user's question and the prepared context
    gemini_response_text = ask_gemini_with_context(user_input, context_data=context_data_string)

    # Return the AI's response in a JSON format expected by the frontend
    return jsonify({"response": gemini_response_text})