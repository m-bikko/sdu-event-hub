from app import create_app
from app.services.gemini_service import ask_gemini

# Create a Flask app context for testing
app = create_app()

def test_chatbot_responses():
    """Test the chatbot with various questions to verify mock responses are working"""
    with app.app_context():
        print("="*50)
        print("TESTING CHATBOT WITH MOCK RESPONSES")
        print("="*50)
        
        test_questions = [
            "What events are happening today?",
            "Tell me about the Chess Club",
            "Where is the Red Hall located?",
            "What time is the next event?",
            "Who are you?",
            "How can I join a club?",
            "Какие мероприятия сегодня?",
            "Расскажи о клубах в SDU",
            "Где находится главный зал?",
            "Кто ты?",
            "Как присоединиться к клубу?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\nTest {i}: '{question}'")
            response = ask_gemini(question)
            print(f"Response: {response}")
            
        print("\nChatbot testing completed!")

if __name__ == "__main__":
    test_chatbot_responses()