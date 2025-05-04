from app import create_app
from app.services.gemini_service import ask_gemini_with_context, generate_mock_response
import sys

# Create Flask app context for database access
app = create_app()

def test_chatbot():
    with app.app_context():
        print("=" * 50)
        print("Testing Chatbot Functionality")
        print("=" * 50)
        
        # Test 1: Direct query with manual context
        print("\nTest 1: Direct query with manual context")
        question = "Какие мероприятия проходят сегодня?"
        context = """
        Вот список некоторых предстоящих мероприятий в SDU:
        - 'Hackathon 2025' от клуба 'ACM Club'. Когда: 10.05 12:00. Где: Main Hall. Цена: 1000 KZT.
        - 'Chess Tournament' от клуба 'Chess Club'. Когда: 15.05 14:30. Где: Recreation Room. Цена: Бесплатно.
        - 'AI Seminar' от клуба 'AI Research Club'. Когда: 20.05 16:00. Где: Room 402. Цена: Бесплатно.
        
        Пожалуйста, отвечай на русском языке и будь вежливым.
        """
        response = ask_gemini_with_context(question, context)
        print(f"Question: {question}")
        print(f"Response: {response}")
        
        # Test 2: Testing mock responses for different questions
        print("\n" + "=" * 50)
        print("Test 2: Testing mock responses for different questions")
        questions = [
            "Какие мероприятия проходят сегодня?",
            "Расскажи о клубе ACM Club",
            "Где находится Main Hall?",
            "Кто ты и что умеешь делать?",
            "Помоги мне найти информацию о мероприятиях",
            "Сколько стоит билет на Hackathon 2025?"
        ]
        
        context_with_club = """
        Вот список некоторых предстоящих мероприятий в SDU:
        - 'Hackathon 2025' от клуба 'ACM Club'. Когда: 10.05 12:00. Где: Main Hall. Цена: 1000 KZT.
        - 'Chess Tournament' от клуба 'Chess Club'. Когда: 15.05 14:30. Где: Recreation Room. Цена: Бесплатно.
        
        Информация о клубе 'ACM Club': Клуб, ориентированный на соревнования по программированию и разработку программного обеспечения. Регулярные занятия по алгоритмам и соревновательному программированию.
        
        Информация о локации 'Main Hall': 
        Вместимость: 100 - 300 человек
        """
        
        for question in questions:
            print(f"\nQuestion: {question}")
            response = generate_mock_response(question, context_with_club)
            print(f"Response: {response}")
        
        print("\nChatbot testing completed!")

if __name__ == "__main__":
    test_chatbot()