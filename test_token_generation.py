#!/usr/bin/env python
"""
Test script to validate the token generation functionality.
This script will:
1. Create a test user if necessary
2. Generate a share token for the test user
3. Retrieve the token and print its details
"""
import os
import sys
from app import create_app, db
from app.models import User, UserShareToken

# Initialize the app with test config
app = create_app()
app.config['SERVER_NAME'] = 'localhost:5000'  # Add SERVER_NAME for URL generation
app.app_context().push()

def test_token_generation():
    """Test the token generation functionality."""
    print("=== Testing Share Token Generation ===")
    
    # Look for an existing user
    test_user = User.query.filter_by(email='test@example.com').first()
    if not test_user:
        print("Creating test user...")
        test_user = User(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password="password",
            role="student"
        )
        db.session.add(test_user)
        db.session.commit()
        print(f"Test user created with ID {test_user.id}")
    else:
        print(f"Using existing test user: {test_user.get_full_name()} (ID: {test_user.id})")
    
    # Check if the user already has a token
    existing_token = UserShareToken.query.filter_by(user_id=test_user.id).first()
    if existing_token:
        print(f"User already has a token: {existing_token.token}")
        print("Regenerating token...")
    
    # Generate a new token
    try:
        token = test_user.generate_share_token()
        print(f"Token successfully generated: {token}")
        
        # Retrieve token via get_share_token method
        retrieved_token = test_user.get_share_token()
        if retrieved_token == token:
            print("Token retrieval method works correctly.")
        else:
            print("ERROR: Token retrieval method returned a different token.")
            
        # Test share URL generation
        with app.test_request_context():
            share_url = test_user.get_share_url()
            if share_url:
                print(f"Share URL generated: {share_url}")
                print(f"Public profile URL: http://localhost:5000{share_url}")
            else:
                print("ERROR: Failed to generate share URL.")
            
        # Check if token exists in database
        db_token = UserShareToken.query.filter_by(token=token).first()
        if db_token:
            print(f"Token found in database: id={db_token.id}, user_id={db_token.user_id}")
            print("All token generation tests PASSED!")
            return True
        else:
            print("ERROR: Token not found in database.")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to generate token: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing share token functionality...")
    success = test_token_generation()
    if success:
        print("\nAll tests passed successfully!")
        print("\nTo view the public profile, run the application and navigate to:")
        print("http://localhost:5000/user/<token>")
        print("\nReplace <token> with the token value shown above.")
    else:
        print("\nTests failed.")
        sys.exit(1)