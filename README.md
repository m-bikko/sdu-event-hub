# SDU Event Hub

A mobile-oriented web platform for SDU (Suleyman Demirel University) students to discover, register for, and manage student club events.

## Features

- **Event Management**: Browse, search, and filter events by various criteria
- **User Roles**: Admin, Student, and Club Head with different permissions and capabilities
- **Ticket System**: Free and paid event registration with QR code tickets
- **Notifications**: Telegram integration for event updates and reminders
- **Chatbot**: AI-powered assistant using Google Gemini to answer event-related questions
- **Social Features**: Club subscriptions, event reviews, and social engagement metrics (Social GPA)
- **Responsive Design**: Mobile-first approach for optimal user experience on all devices

## Technical Implementation

This application is built using the following technologies:

- **Backend**: Python Flask with MVC architecture
- **Database**: SQLite (for prototype, PostgreSQL recommended for production)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap for responsive design
- **External APIs**:
  - Google Gemini for chatbot functionality
  - Stripe for payment processing
  - Telegram Bot API for notifications

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Telegram Bot (optional, for notifications)
- Stripe account (optional, for payments)

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd sdu-event-hub
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database with sample data:
   ```
   python init_db.py
   ```

5. Run the application:
   ```
   ./run.sh
   ```
   Or manually:
   ```
   python run.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5004
   ```

### Default Login Credentials

- **Admin**: admin@sdu.edu.kz / admin123
- **Student/Club Head**: [email]@sdu.edu.kz / password (see init_db.py for sample accounts)

## Environment Variables

For full functionality, the following environment variables can be configured:

- `GEMINI_API_KEY`: Google Gemini API key for chatbot
- `STRIPE_SECRET_KEY`: Stripe API key for payment processing
- `STRIPE_PUBLISHABLE_KEY`: Stripe public key for frontend
- `STRIPE_WEBHOOK_SECRET`: Webhook signing secret for payment verification
- `TELEGRAM_BOT_TOKEN`: Telegram bot token for notifications
- `TELEGRAM_BOT_USERNAME`: Username of your Telegram bot
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SECRET_KEY`: Flask application secret key
- `USE_MOCK_GEMINI`: Set to "true" to use mock Gemini API (default in run.sh)
- `USE_MOCK_STRIPE`: Set to "true" to use mock Stripe API (default in run.sh)

## Project Structure

```
/project_root
|-- app/
|   |-- __init__.py      # Flask application factory
|   |-- models.py        # Database models
|   |-- forms.py         # WTForms definitions
|   |-- views/           # Controllers/route handlers
|   |   |-- auth.py
|   |   |-- admin.py
|   |   |-- student.py
|   |   |-- club_head.py
|   |   |-- events.py
|   |   |-- payments.py
|   |   |-- notifications.py
|   |   |-- chatbot.py
|   |-- services/        # External service integrations
|   |   |-- gemini_service.py
|   |   |-- payment_service.py
|   |   |-- telegram_service.py
|   |   |-- social_gpa_calculator.py
|   |-- templates/       # Jinja2 HTML templates
|   |-- static/          # CSS, JS, and images
|-- config.py            # Application configuration
|-- run.py               # Application entry point
|-- init_db.py           # Database initialization script
|-- requirements.txt     # Python dependencies
|-- run.sh               # Convenience script to run the application
```

## Features by User Role

### Student
- Browse and search events
- Register for free events and purchase tickets for paid events
- View tickets with QR codes
- Leave reviews for attended events
- Subscribe to clubs for updates
- View profile with Social GPA and bonus points
- Connect Telegram account for notifications
- Chat with AI assistant about events

### Club Head
- All Student features
- Create and manage club events
- Reserve locations for events
- Manage club members
- View event attendance

### Administrator
- Manage users, clubs, and locations
- Assign Club Head roles
- Monitor events and bookings
- System-wide administration

## Mock Mode

The application includes mock implementations for external services (Gemini, Stripe, Telegram) to allow for easy development and testing without requiring actual API keys. This is enabled by default in the run.sh script.

- Mock Gemini: Provides simple chatbot responses without accessing the actual Gemini API
- Mock Stripe: Simulates payment processing without requiring a Stripe account
- Mock Telegram: Logs notification messages instead of sending them via the Telegram Bot API

To use the actual external services:
1. Obtain API keys for the services you want to use
2. Set the corresponding environment variables (GEMINI_API_KEY, STRIPE_SECRET_KEY, etc.)
3. Disable mock mode by setting USE_MOCK_GEMINI=false and USE_MOCK_STRIPE=false

## Production Deployment Considerations

For a production deployment:

1. Use PostgreSQL instead of SQLite
2. Configure proper environment variables for API keys
3. Set up a proper web server (Gunicorn/uWSGI with Nginx)
4. Implement proper error logging
5. Set up SSL/TLS for secure connections
6. Configure background tasks for sending notifications and reminders
7. Disable mock mode for external services by setting USE_MOCK_* variables to "false"

## License

[MIT License](LICENSE)