# app/services/gemini_service.py
import os
from datetime import datetime

# Use environment variable for API key or fallback to the provided key
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyA7zgkfPqewfQsGhQi7L8OYVxsiZuOguSU")

# Configure the Google Gemini API client
try:
    from google import genai
    genai.configure(api_key=API_KEY)
    
    # Choose the Gemini model - using "gemini-pro" for general purpose text responses
    MODEL_NAME = 'gemini-pro'
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"Gemini model '{MODEL_NAME}' initialized successfully.")
    IMPORT_SUCCESS = True
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    IMPORT_SUCCESS = False
    model = None

def generate_mock_response(question: str, context_data: str = None) -> str:
    """
    Generates a mock response when the Gemini API is unavailable.
    This function creates a response in English as required.
    
    Args:
        question (str): The user's question
        context_data (str, optional): Context data that would have been sent to the API
        
    Returns:
        str: A simulated response in English
    """
    question_lower = question.lower()
    
    # Check for event-related questions
    if any(keyword in question_lower for keyword in ["today", "happening", "events", "schedule"]):
        if context_data and "upcoming events" in context_data.lower():
            # Extract event information from context if available
            try:
                events_section = context_data.split("Here is a list of some upcoming events at SDU:")[1].split("\n\n")[0]
                return f"Here are the events coming up at SDU:\n{events_section}"
            except:
                pass
        return "I don't currently have information about today's events. Please check the SDU Event Hub schedule for the latest updates."
    
    # Check for club-related questions
    if any(keyword in question_lower for keyword in ["club", "organization", "society"]):
        if context_data and "Information about club" in context_data:
            club_info = ""
            for line in context_data.split("\n"):
                if "Information about club" in line:
                    club_info = line
                    # Get the following lines as well
                    in_club_section = True
                    for line in context_data.split("\n"):
                        if in_club_section and line.strip():
                            club_info += "\n" + line
                        if in_club_section and not line.strip():
                            break
                    break
            if club_info:
                return club_info
        return "SDU has many active clubs catering to various interests. You can find detailed information about each club on the SDU Event Hub platform."
    
    # Check for location-related questions
    if any(keyword in question_lower for keyword in ["where", "location", "place", "hall", "room"]):
        if context_data and "Information about location" in context_data:
            location_info = ""
            for line in context_data.split("\n"):
                if "Information about location" in line:
                    location_info = line
                    # Get the following lines as well
                    in_location_section = True
                    for line in context_data.split("\n"):
                        if in_location_section and line.strip():
                            location_info += "\n" + line
                        if in_location_section and not line.strip():
                            break
                    break
            if location_info:
                return location_info
        return "SDU has various event locations including lecture halls, conference rooms, and open spaces. For detailed information about specific locations, please check the event details on the SDU Event Hub platform."
    
    # Generic responses for other questions
    if any(word in question_lower for word in ["what", "who", "how"]) and any(word in question_lower for word in ["you", "chatbot", "assistant"]):
        return "I'm the SDU Event Hub assistant, created to help students find information about events, clubs, and activities at Suleyman Demirel University."
    
    if any(word in question_lower for word in ["help"]):
        return "I can help you find information about events, clubs, locations, and activities at SDU. Just ask specific questions like 'What events are happening today?' or 'Tell me about the Chess Club'."
    
    # Default response
    return "I understand you're asking about SDU events or activities. For specific information, please clarify your question or check the SDU Event Hub platform."

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
    if model is None or not IMPORT_SUCCESS:
        # Return a mock response if the model failed to initialize
        print("Gemini API unavailable - using mock responses")
        return generate_mock_response(question, context_data)

    # Construct the prompt for the AI
    prompt_parts = []

    # Add the database context if provided
    if context_data:
        # Replace Russian instructions with English
        english_context = context_data.replace(
            "Пожалуйста, отвечай на русском языке и будь вежливым.", 
            "Please respond in English and be polite."
        ).replace(
            "Если ты не уверен в ответе на основе предоставленной информации, скажи об этом.",
            "If you're not sure about the answer based on the provided information, please say so."
        ).replace(
            "Вот список некоторых предстоящих мероприятий в SDU:", 
            "Here is a list of some upcoming events at SDU:"
        ).replace(
            "Информация о клубе", 
            "Information about club"
        ).replace(
            "Информация о локации", 
            "Information about location"
        ).replace(
            "Предстоящие мероприятия", 
            "Upcoming events"
        ).replace(
            "от клуба", 
            "by club"
        ).replace(
            "Когда:", 
            "When:"
        ).replace(
            "Где:", 
            "Where:"
        ).replace(
            "Цена:", 
            "Price:"
        ).replace(
            "Бесплатно", 
            "Free"
        ).replace(
            "человек", 
            "people"
        ).replace(
            "Вместимость:", 
            "Capacity:"
        )
        
        prompt_parts.append(f"""
Use the following information about SDU events, clubs, locations and other data if it's relevant to answering the student's question:
---
{english_context}
---
If the provided information doesn't contain the answer to the question, or if the question isn't directly related to SDU, answer based on your general knowledge, but you may mention that specific SDU information was limited for this question.
""")

    # Add the user's question
    prompt_parts.append(f"Student's question: {question}")
    
    # Add instruction to respond in English
    prompt_parts.append("Please respond in English, even if the question was asked in another language.")

    try:
        # Call the Gemini API to generate content
        response = model.generate_content(prompt_parts)

        # Check if the response contains text content
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()  # Use .strip() to remove leading/trailing whitespace
        else:
            # Handle cases where the API call was successful but returned no text
            print(f"Gemini API returned no text for prompt. Full response: {response}")
            # Check for safety ratings that might have blocked the response
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.safety_ratings:
                return "I'm sorry, I can't answer this question due to safety restrictions."
            return "I'm sorry, I can't generate a response to this question right now. Please try rephrasing or asking a different question."

    except Exception as e:
        # Log the error
        print(f"Error calling Gemini API: {e}")
        # Provide a fallback mock response
        return generate_mock_response(question, context_data)