from google import genai

# Initialize the client with the API key
client = genai.Client(api_key="AIzaSyA7zgkfPqewfQsGhQi7L8OYVxsiZuOguSU")

# Make a simple request to test the API connection
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Ответь на русском языке: Что такое Сулейман Демирель Университет и где он находится?"
    )
    print("Success! Response text:")
    print(response.text)
except Exception as e:
    print(f"Error calling Gemini API: {e}")
    print("Using mock response instead of the actual API.")
    mock_response = "Сулейман Демирель Университет (СДУ) - это международный университет, расположенный в городе Каскелен, Алматинская область, Казахстан. Университет был основан в 1996 году и назван в честь бывшего президента Турции Сулеймана Демиреля. СДУ известен своими образовательными программами в области инженерии, информационных технологий, бизнеса и социальных наук."
    print(mock_response)