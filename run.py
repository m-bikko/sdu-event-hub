from app import create_app
from app.services.telegram_service import start_bot

app = create_app()

# Start the Telegram bot in development mode
try:
    with app.app_context():
        start_bot()
except Exception as e:
    print(f"Failed to start Telegram bot: {e}")
    print("Telegram functionality will be disabled")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)