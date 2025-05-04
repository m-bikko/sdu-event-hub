import os
import google.generativeai as genai
import json

# Test the Gemini API directly first to verify it works
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyA7zgkfPqewfQsGhQi7L8OYXxsiZuOguSU")

def test_gemini_api():
    """Test if the Gemini API works with the given API key"""
    print(f"Using API key: {API_KEY}")
    
    try:
        # Configure API
        genai.configure(api_key=API_KEY)
        
        # Test available models
        print("Trying to get available models...")
        models = genai.list_models()
        models_list = [model.name for model in models]
        print(f"Available models: {models_list}")
        
        # Choose model
        MODEL_NAME = 'gemini-pro'
        print(f"Trying to initialize model {MODEL_NAME}...")
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Test simple prompt
        print("Testing simple API call...")
        response = model.generate_content("Hello, how are you?")
        
        if response and response.text:
            print(f"\nAPI test successful! Response: {response.text[:100]}...")
            return True
        else:
            print("\nAPI call successful but no text in response")
            return False
            
    except Exception as e:
        print(f"\nAPI test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_result = test_gemini_api()
    print(f"\nFinal result: API {'works' if test_result else 'does not work'} with the provided key")