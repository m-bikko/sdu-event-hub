#!/bin/bash

# Kill any process using port 5004
lsof -i :5004 -t | xargs kill -9 2>/dev/null

echo "Starting SDU Event Hub application on port 5004..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database if it doesn't exist
if [ ! -f "app.db" ]; then
    echo "Initializing database..."
    # Enable mock mode for external services
    export USE_MOCK_GEMINI=true
    export USE_MOCK_STRIPE=true
    python init_db.py
fi

# Create necessary directories if they don't exist
mkdir -p app/static/qr_codes
mkdir -p app/static/profile_pics
mkdir -p app/static/event_pics
mkdir -p app/static/uploads

# Run the application with mock services enabled
# This ensures the app can run without external API dependencies
echo "Starting the application with mock mode enabled for external services..."
export USE_MOCK_GEMINI=true
export USE_MOCK_STRIPE=true
python run.py