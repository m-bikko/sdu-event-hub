Understood. Here is the documentation specifically for the backend implementation of the AI chatbot using the Gemini API in your Flask application, assuming the frontend (HTML/JavaScript for the chat interface) is already completed and sends messages to a designated backend endpoint.

---START_OF_GEMINI_BACKEND_DOCS---

**Documentation: AI Chatbot Backend Integration using Google Gemini API**

**Objective:**
Implement the backend logic within the Flask application to receive messages from the frontend chat interface, process them using the Google Gemini API, incorporating relevant data from the SDU database, and return the AI's response.

**Your Provided Gemini API Key:**
`AIzaSyA7zgkfPqewfQsGhQi7L8OYXxsiZuOguSU`

**Important Security Note:** The API key provided above should be stored securely. Do NOT hardcode it directly into public code files that might be committed to repositories. Use environment variables (`os.environ.get`) or a secure configuration file (`config.py` with appropriate handling) to access it. For development/hackathon purposes, reading from `config.py` is acceptable, but prefer environment variables.

**Required Library:**
You will need the official Google Generative AI library for Python.
Installation:
```bash
pip install google-generativeai
```

**Backend Implementation Steps:**

The backend implementation will involve creating a service module for API interaction and a Flask endpoint to handle requests.

**Step 1: Backend Service Module (`services/gemini_service.py`)**

Create a dedicated Python module to handle the communication with the Gemini API. This isolates the external API logic.

*   **File Location:** `app/services/gemini_service.py`
*   **Purpose:** Encapsulate the logic for making API calls to Gemini. Handles API configuration, calling the model, and basic error handling for API communication.
*   **Code:**

```python
# app/services/gemini_service.py
import google.generativeai as genai
import os
# If you prefer config.py for secrets in hackathon:
# from app.config import Config

# Load the API key securely. Prefer environment variable.
# If using config.py: API_KEY = Config.GEMINI_API_KEY
# For hackathon simplicity with direct key (less secure):
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyA7zgkfPqewfQsGhQi7L8OYXxsiZuOguSU")

# Configure the API client
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    # Handle configuration errors appropriately (e.g., log and disable chatbot)

# Choose the Gemini model. 'gemini-pro' is a good general model.
# 'gemini-1.5-flash' might handle larger contexts better if needed.
MODEL_NAME = 'gemini-pro' # Or 'gemini-1.5-flash'
model = None # Initialize model as None
try:
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"Gemini model '{MODEL_NAME}' initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini model '{MODEL_NAME}': {e}")
    # If model fails to initialize, the ask_gemini_with_context function should handle it.


def ask_gemini_with_context(question: str, context_data: str = None) -> str:
    """
    Sends a question to the Gemini API, including optional context data from SDU DB.

    Args:
        question (str): The user's question received from the frontend.
        context_data (str, optional): Relevant information about SDU events, clubs,
                                       etc., fetched from the application's database,
                                       formatted as a clear text string. Defaults to None.

    Returns:
        str: The generated response text from Gemini, or a user-friendly error message.
    """
    if model is None:
        # Return an error if the model failed to initialize
        return "Чат-бот временно недоступен из-за проблемы с его инициализацией на сервере."

    # Construct the prompt for the AI.
    # It's important to clearly separate the context and the user's question,
    # and instruct the AI on how to use the context.
    prompt_parts = []

    # Add the database context if provided
    if context_data:
        prompt_parts.append(f"""
Используй следующую информацию о мероприятиях, клубах, локациях и других данных SDU, если она релевантна для ответа на вопрос студента:
---
{context_data}
---
Если предоставленная информация не содержит ответа на вопрос, или вопрос не связан напрямую с SDU, отвечай на основе своих общих знаний, но можешь упомянуть, что специфичная информация по SDU была ограничена для этого вопроса.
""")

    # Add the user's question
    prompt_parts.append(f"Вопрос студента: {question}")

    try:
        # Call the Gemini API to generate content
        # Consider adding safety_settings here if needed, based on use case.
        response = model.generate_content(prompt_parts)

        # Check if the response contains text content
        if response and response.text:
            return response.text.strip() # Use .strip() to remove leading/trailing whitespace
        else:
            # Handle cases where the API call was successful but returned no text
            # This can happen due to safety filters or other reasons.
            print(f"Gemini API returned no text for prompt. Full response: {response}")
            # Check for safety ratings that might have blocked the response
            if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                 return "Извините, я не могу ответить на этот вопрос из-за ограничений безопасности."
            return "Извините, я не могу сгенерировать ответ на этот вопрос сейчас. Попробуйте перефразировать или задать другой вопрос."

    except Exception as e:
        # Catch potential API errors (network issues, invalid API key, rate limits, etc.)
        print(f"Error calling Gemini API: {e}")
        # Provide a user-friendly error message
        return "Извините, произошла ошибка при обращении к чат-боту. Пожалуйста, попробуйте позже."

# Note: For production-level applications, implement more detailed logging
# and potentially retry mechanisms for transient API errors.
```

**Step 2: Backend Endpoint (`views/chatbot.py`)**

Create or modify a Flask route to serve as the API endpoint that your frontend chat interface will communicate with. This route will receive the user's message, fetch relevant data from your SDU database, pass it to the Gemini service, and send the response back to the frontend.

*   **File Location:** `app/views/chatbot.py`
*   **Purpose:** Receive POST requests with user messages, orchestrate fetching database context, calling the Gemini service, and returning a JSON response.
*   **Code:**

```python
# app/views/chatbot.py
from flask import Blueprint, request, jsonify
from app.services.gemini_service import ask_gemini_with_context
from app.models import Event, Club, Location # Import your SQLAlchemy models
from app import db # Assuming you have your SQLAlchemy instance here
from datetime import datetime
# You might need flask_login or similar if chat is only for logged-in users
# from flask_login import login_required, current_user

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot', methods=['POST'])
# @login_required # Add this decorator if only logged-in users can use the chat
def handle_chatbot_request():
    """
    Handles incoming chat messages from the frontend.
    Expects JSON payload: {"message": "User's message"}.
    Fetches relevant context from the DB and sends it to Gemini.
    Returns JSON payload: {"response": "Bot's response"}.
    """
    # Ensure the request content type is JSON
    if not request.is_json:
        return jsonify({"response": "Ошибка запроса: Ожидается JSON."}), 415 # Unsupported Media Type

    user_input = request.json.get('message')

    if not user_input or not isinstance(user_input, str) or user_input.strip() == "":
        return jsonify({"response": "Пожалуйста, введите сообщение."}), 400 # Bad Request

    # --- Dynamic Context Building Logic ---
    # This is where you decide which database information is relevant
    # to the user's question and fetch it.
    # The complexity here depends on how smart you want the context fetching to be.
    # For a hackathon, fetching basic common context is sufficient.

    context_data_string = ""

    # Example: Always provide upcoming events as context
    try:
        # Fetch events happening from now into the near future (e.g., next 7 days)
        # Adjust the time window as needed.
        now = datetime.utcnow() # Use timezone-aware datetimes if possible
        future_window = now + timedelta(days=7)
        upcoming_events = Event.query.filter(Event.date_time >= now, Event.date_time <= future_window)\
                                   .order_by(Event.date_time).limit(10).all() # Limit results

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
            context_data_string += "\n" # Add a newline for separation

    except Exception as e:
        print(f"Error fetching upcoming events for context: {e}")
        # Log the error but continue without this context


    # Example: Try to identify club names in the user's input and provide club descriptions
    # This requires a list of club names and a method to get club details.
    try:
        # IMPLEMENT Club.get_all_names() to return a list of strings
        all_club_names = [club.name for club in Club.query.all()] # Or use a dedicated method
        matched_club_name = None
        for name in all_club_names:
            # Basic case-insensitive check
            if name.lower() in user_input.lower():
                matched_club_name = name
                break # Take the first match for simplicity

        if matched_club_name:
            # IMPLEMENT Club.get_club_by_name(name) to fetch the club object
            club_details = Club.query.filter_by(name=matched_club_name).first()
            if club_details and club_details.description:
                 context_data_string += f"Информация о клубе '{club_details.name}': {club_details.description}\n\n"
                 # Optional: Fetch and add upcoming events specifically for this club
                 # club_upcoming_events = Event.query.filter(Event.club_id == club_details.id, Event.date_time >= now).order_by(Event.date_time).limit(5).all()
                 # ... format and add club_upcoming_events to context_data_string ...

    except Exception as e:
        print(f"Error fetching club details for context: {e}")
        # Log the error but continue


    # Example: Provide info about locations if location names are mentioned
    # Similar keyword matching and fetching logic for Location model.
    # try:
    #     # IMPLEMENT Location.get_all_names() etc.
    #     all_location_names = [loc.name for loc in Location.query.all()]
    #     # ... matching and fetching location details ...
    # except Exception as e:
    #     print(f"Error fetching location details: {e}")


    # Add some general instructions to the AI
    context_data_string += "Пожалуйста, отвечай на русском языке и будь вежливым.\n"
    context_data_string += "Если ты не уверен в ответе на основе предоставленной информации, скажи об этом.\n"


    # Call the Gemini service with the user's question and the prepared context
    # Pass the formatted string of context data
    gemini_response_text = ask_gemini_with_context(user_input, context_data=context_data_string)

    # Return the AI's response in a JSON format expected by the frontend
    return jsonify({"response": gemini_response_text})

# Remember to register this blueprint in your app/__init__.py
# from app.views.chatbot import chatbot_bp
# app.register_blueprint(chatbot_bp) # Or with a URL prefix like url_prefix='/api'
```

**Step 3: Database Model Methods (`models.py`)**

Ensure your SQLAlchemy models (`app/models.py`) have the necessary methods or properties to easily query and retrieve the data you need for context building (as demonstrated in the `views/chatbot.py` code comments).

*   **File Location:** `app/models.py`
*   **Purpose:** Define the structure of your data and provide methods for querying.
*   **Add Methods Like (Example):**

```python
# app/models.py
from app import db # Assuming db = SQLAlchemy(app)
from datetime import datetime, timedelta # Import timedelta

# --- Assume other model definitions (User, Club, Location, etc.) are here ---

class Event(db.Model):
    # ... (Existing columns like id, name, description, date_time, price, club_id, location_id) ...
    # Ensure relationships are defined if needed, e.g.:
    club = db.relationship('Club', backref='events')
    location = db.relationship('Location', backref='events')

    # Method to get upcoming events within a time window
    @staticmethod
    def get_upcoming_events(time_window_days=7):
        """Fetches events from now up to time_window_days in the future."""
        now = datetime.utcnow() # Use timezone-aware datetimes if appropriate
        future_time = now + timedelta(days=time_window_days)
        return Event.query.filter(Event.date_time >= now, Event.date_time <= future_time)\
                                   .order_by(Event.date_time).all()

    # Method to search events by name (basic search)
    @staticmethod
    def search_by_name(name_query):
        """Searches for events whose name contains the query string (case-insensitive)."""
        search_term = f"%{name_query}%"
        return Event.query.filter(Event.name.ilike(search_term)).all()

class Club(db.Model):
    # ... (Existing columns like id, name, description) ...

    # Method to get club details by name
    @staticmethod
    def get_by_name(name):
        """Fetches a club by its exact name (case-sensitive)."""
        return Club.query.filter_by(name=name).first()

    # Method to get all club names
    @staticmethod
    def get_all_names():
        """Returns a list of all club names."""
        return [club.name for club in Club.query.all()]

class Location(db.Model):
    # ... (Existing columns like id, name) ...

    # Method to get location by name
    @staticmethod
    def get_by_name(name):
         """Fetches a location by its exact name (case-sensitive)."""
         return Location.query.filter_by(name=name).first()

# Ensure these methods are implemented correctly and the database session (db.session) is managed.
```

**Step 4: Configuration (`config.py`)**

Ensure your Flask application can access the Gemini API key from your configuration.

*   **File Location:** `config.py` or `app/config.py`
*   **Code:**

```python
# config.py or app/config.py
import os

class Config:
    # ... other configurations like SECRET_KEY, SQLALCHEMY_DATABASE_URI ...
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyA7zgkfPqewfQsGhQi7L8OYXxsiZuOguSU') # Use your provided key

# In your app factory or __init__.py:
# from config import Config
# app = Flask(__name__)
# app.config.from_object(Config)
# db = SQLAlchemy(app)
```
**Recommendation:** Set the `GEMINI_API_KEY` environment variable in your development environment. For example, in your terminal before running `run.py`:
```bash
export GEMINI_API_KEY='AIzaSyA7zgkfPqewfQsGhQi7L8OYXxsiZuOguSU'
```
Or use a `.env` file and `python-dotenv`.

**Error Handling and Robustness:**

*   Ensure that database queries (`.all()`, `.first()`) are wrapped in `try...except` blocks in the context-building logic (`views/chatbot.py`) to prevent database errors from crashing the chatbot.
*   The `ask_gemini_with_context` function includes basic error handling for API calls. Log these errors server-side.
*   Consider implementing logging throughout the backend to help diagnose issues.

**Context Building Sophistication (Beyond Hackathon):**

For a more advanced chatbot, the context-building logic in `views/chatbot.py` could be improved by:

*   **Keyword Extraction:** Using simple string methods or regex to identify keywords like "мероприятия", "события", "клуб такой-то", "где", "когда".
*   **Simple NLP:** Using a library like `spaCy` or `NLTK` (more setup) to identify entities (like club names) and intent (asking for events, details).
*   **Conversation History:** Passing a summary or the last few turns of the conversation as part of the context to allow the AI to maintain context across messages. This requires storing conversation history temporarily.

This backend documentation, combined with the assumption of a functional frontend sending POST requests to the `/chatbot` endpoint, provides a clear path for the AI agent to implement the core chatbot functionality using the Gemini API and your database.

---END_OF_GEMINI_BACKEND_DOCS---