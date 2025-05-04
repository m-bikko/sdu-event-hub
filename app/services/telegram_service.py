import os
import uuid
import threading
import logging
from app import db
from app.models import User, Event
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Use environment variable for bot token or the provided token
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8100465500:AAFq0ZVr1EhZUuUksRc3nfUXJUZi2pIXgOI")

# Check if python-telegram-bot is installed
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
    from telegram.ext import (
        Updater, CommandHandler, CallbackQueryHandler, 
        MessageHandler, Filters, CallbackContext, ConversationHandler
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("python-telegram-bot is not installed. Using mock implementation.")
    TELEGRAM_AVAILABLE = False
    
    # Mock classes and functions
    class Update:
        pass
        
    class CallbackContext:
        pass
        
    ParseMode = type('obj', (object,), {
        'HTML': 'HTML',
        'MARKDOWN': 'MARKDOWN'
    })
        
    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None, url=None):
            self.text = text
            self.callback_data = callback_data
            self.url = url
    
    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard):
            self.inline_keyboard = inline_keyboard

# States for ConversationHandler
AWAITING_CODE = 0

# Callback query data identifiers
EVENT_PREFIX = "event_"
TICKET_PREFIX = "ticket_"

# If python-telegram-bot is installed, create a real bot
if TELEGRAM_AVAILABLE:
    updater = Updater(token=BOT_TOKEN)
    bot = updater.bot
    dp = updater.dispatcher
else:
    # Mock implementation for Telegram bot
    class MockTelegramBot:
        def __init__(self, token):
            self.token = token
            logger.info(f"Mock Telegram Bot initialized with token: {token[:5]}...")
        
        def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
            logger.info(f"[MOCK TELEGRAM] Message to {chat_id}: {text[:50]}...")
            return True
            
        def send_photo(self, chat_id, photo, caption=None, parse_mode=None, reply_markup=None):
            logger.info(f"[MOCK TELEGRAM] Photo to {chat_id}: {caption[:50] if caption else 'No caption'}...")
            return True
    
    # Initialize the mock bot
    bot = MockTelegramBot(token=BOT_TOKEN)
    
    # Mock classes for updater
    class MockUpdater:
        def __init__(self, bot):
            self.bot = bot
            
        def start_polling(self):
            logger.info("[MOCK TELEGRAM] Updater started polling...")
            
        def idle(self):
            logger.info("[MOCK TELEGRAM] Updater is idle...")
            
        def stop(self):
            logger.info("[MOCK TELEGRAM] Updater stopped...")
    
    updater = MockUpdater(bot)

def send_notification(chat_id, text, reply_markup=None):
    """
    Sends a text message to a user via Telegram.
    
    Args:
        chat_id (str): The user's Telegram chat ID.
        text (str): The message to send.
        reply_markup (InlineKeyboardMarkup, optional): Inline keyboard markup for interactive buttons.
        
    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    try:
        bot.send_message(
            chat_id=chat_id, 
            text=text, 
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        logger.error(f"Error sending Telegram message to chat_id {chat_id}: {e}")
        return False

def generate_telegram_connect_code(user_id):
    """
    Generates a unique code for connecting a user's account to Telegram.
    
    Args:
        user_id (int): The user's ID.
        
    Returns:
        str: The generated code, or None if an error occurred.
    """
    try:
        # Get user
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Generate a unique code
        connect_code = str(uuid.uuid4())
        
        # Save the code to the user's record
        user.telegram_connect_code = connect_code
        db.session.commit()
        
        return connect_code
    except Exception as e:
        print(f"Error generating Telegram connect code: {e}")
        db.session.rollback()
        return None

def verify_telegram_connect_code(code, chat_id):
    """
    Verifies a Telegram connection code and links the user's account to their Telegram ID.
    
    Args:
        code (str): The connection code provided by the user.
        chat_id (str): The Telegram chat ID to link.
        
    Returns:
        tuple: (bool, str) indicating success/failure and a message.
    """
    try:
        # Find user with this code
        user = User.query.filter_by(telegram_connect_code=code).first()
        
        if not user:
            return False, "Invalid code. Please generate a new code from the SDU Event Hub website."
        
        # Link the chat ID to the user
        user.telegram_chat_id = str(chat_id)
        user.telegram_connect_code = None  # Code is used only once
        db.session.commit()
        
        return True, f"Success! Your Telegram account is now linked to SDU Event Hub. You will receive notifications for events and updates."
    except Exception as e:
        print(f"Error verifying Telegram connect code: {e}")
        db.session.rollback()
        return False, "An error occurred while processing your request. Please try again later."

def send_event_notification(event_id, notification_type='new'):
    """
    Sends notifications about an event to relevant users.
    
    Args:
        event_id (int): The ID of the event.
        notification_type (str): The type of notification ('new', 'reminder_24h', 'reminder_1h').
        
    Returns:
        int: The number of notifications sent.
    """
    try:
        event = Event.query.get(event_id)
        if not event:
            return 0
        
        sent_count = 0
        
        if notification_type == 'new':
            # Notify club subscribers about new event
            message = f"🎉 <b>New Event Alert!</b>\n\n"
            message += f"<b>{event.name}</b> by {event.club.name}\n"
            message += f"📅 {event.date_time.strftime('%Y-%m-%d %H:%M')}\n"
            message += f"📍 {event.location.name}\n\n"
            message += f"{event.description[:100]}...\n\n"
            message += f"Price: {event.price} KZT" if event.price > 0 else "Free entry"
            
            # Send to all subscribers of the club who have Telegram connected
            for subscriber in event.club.subscribers:
                if subscriber.telegram_chat_id:
                    if send_notification(subscriber.telegram_chat_id, message):
                        sent_count += 1
        
        elif notification_type in ['reminder_24h', 'reminder_1h']:
            # Prepare reminder message
            time_str = "24 hours" if notification_type == 'reminder_24h' else "1 hour"
            message = f"⏰ <b>Event Reminder!</b>\n\n"
            message += f"<b>{event.name}</b> is happening in {time_str}\n"
            message += f"📅 {event.date_time.strftime('%Y-%m-%d %H:%M')}\n"
            message += f"📍 {event.location.name}\n\n"
            if event.price > 0:
                message += "Don't forget your ticket!"
            
            # Send to all users with tickets for this event
            for ticket in event.tickets:
                if ticket.user.telegram_chat_id and ticket.status in ['paid', 'pending']:
                    if send_notification(ticket.user.telegram_chat_id, message):
                        sent_count += 1
        
        return sent_count
    except Exception as e:
        print(f"Error sending event notifications: {e}")
        return 0

def send_ticket_confirmation(user_id, event_name, qr_code_url):
    """
    Sends a ticket confirmation notification.
    
    Args:
        user_id (int): The user's ID.
        event_name (str): The name of the event.
        qr_code_url (str): The URL to the ticket's QR code.
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise.
    """
    try:
        user = User.query.get(user_id)
        if not user or not user.telegram_chat_id:
            return False
        
        base_url = os.environ.get("BASE_URL", "http://localhost:5004")
        
        message = f"🎫 <b>Ticket Confirmed!</b>\n\n"
        message += f"Your ticket for <b>{event_name}</b> has been confirmed.\n\n"
        message += f"You can view your ticket and QR code at:\n"
        message += f"{base_url}{qr_code_url}\n\n"
        message += "Show this QR code at the entrance of the event."
        
        return send_notification(user.telegram_chat_id, message)
    except Exception as e:
        print(f"Error sending ticket confirmation: {e}")
        return False

def send_reminders():
    """
    Sends reminders for upcoming events (24h and 1h before the event).
    Should be scheduled to run periodically.
    
    Returns:
        dict: Counts of reminders sent for each type.
    """
    try:
        now = datetime.utcnow()
        
        # Find events happening in ~24 hours
        time_24h_from_now = now + timedelta(hours=24)
        time_23h_from_now = now + timedelta(hours=23)  # Add a 1-hour window
        events_24h = Event.query.filter(
            Event.date_time > time_23h_from_now,
            Event.date_time <= time_24h_from_now
        ).all()
        
        # Find events happening in ~1 hour
        time_1h_from_now = now + timedelta(hours=1)
        time_50min_from_now = now + timedelta(minutes=50)  # Add a 10-minute window
        events_1h = Event.query.filter(
            Event.date_time > time_50min_from_now,
            Event.date_time <= time_1h_from_now
        ).all()
        
        # Send reminders
        count_24h = 0
        for event in events_24h:
            count_24h += send_event_notification(event.id, 'reminder_24h')
        
        count_1h = 0
        for event in events_1h:
            count_1h += send_event_notification(event.id, 'reminder_1h')
        
        return {
            'reminder_24h': count_24h,
            'reminder_1h': count_1h
        }
    except Exception as e:
        logger.error(f"Error in reminder scheduler: {e}")
        return {'error': str(e)}

# Telegram Bot Command Handlers

def start_command(update: Update, context: CallbackContext):
    """Handler for /start command"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "there"
    
    # Check if user is already linked
    user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
    
    if user:
        message = (
            f"👋 Welcome back, <b>{user.first_name}</b>!\n\n"
            "I'm the SDU Event Hub bot. I'll help you discover events "
            "and manage your tickets.\n\n"
            "Use /help to see what I can do."
        )
    else:
        message = (
            f"👋 Hello {username}!\n\n"
            "I'm the SDU Event Hub bot. I'll help you discover events "
            "and manage your tickets.\n\n"
            "To get started, please link your SDU Event Hub account "
            "using the /link command.\n\n"
            "Use /help to see what I can do."
        )
    
    # Create keyboard with main commands
    keyboard = [
        [InlineKeyboardButton("Link Account", callback_data="cmd_link")],
        [InlineKeyboardButton("Browse Events", callback_data="cmd_events")],
        [InlineKeyboardButton("My Tickets", callback_data="cmd_tickets")],
        [InlineKeyboardButton("Help", callback_data="cmd_help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    chat_id = update.effective_chat.id
    
    message = (
        "🤖 <b>SDU Event Hub Bot Commands</b>\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/link - Link your SDU Event Hub account\n"
        "/events - Browse upcoming events\n"
        "/mytickets - View your tickets\n\n"
        "You will automatically receive notifications for:\n"
        "• New events from clubs you follow\n"
        "• Reminders for events you have tickets for\n"
        "• Ticket confirmations"
    )
    
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML
    )
    
    return ConversationHandler.END

def link_command(update: Update, context: CallbackContext):
    """Handler for /link command"""
    chat_id = update.effective_chat.id
    
    # Check if user is already linked
    user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
    
    if user:
        message = (
            f"Your Telegram account is already linked to <b>{user.first_name} {user.last_name}</b>.\n\n"
            "If you want to link to a different account, please visit the SDU Event Hub website "
            "and unlink your Telegram account first."
        )
        
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    message = (
        "To link your Telegram account to SDU Event Hub:\n\n"
        "1. Login to the SDU Event Hub website\n"
        "2. Go to your Profile → Settings\n"
        "3. Click on 'Link Telegram Account'\n"
        "4. You'll receive a unique code\n"
        "5. Send that code to me\n\n"
        "Please send your code now:"
    )
    
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML
    )
    
    return AWAITING_CODE

def link_code_handler(update: Update, context: CallbackContext):
    """Handler for receiving the link code"""
    chat_id = update.effective_chat.id
    code = update.message.text.strip()
    
    success, message = verify_telegram_connect_code(code, chat_id)
    
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML
    )
    
    if success:
        # If linking was successful, show the main menu
        keyboard = [
            [InlineKeyboardButton("Browse Events", callback_data="cmd_events")],
            [InlineKeyboardButton("My Tickets", callback_data="cmd_tickets")],
            [InlineKeyboardButton("Help", callback_data="cmd_help")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        bot.send_message(
            chat_id=chat_id,
            text="What would you like to do next?",
            reply_markup=reply_markup
        )
    
    return ConversationHandler.END

def events_command(update: Update, context: CallbackContext):
    """Handler for /events command"""
    chat_id = update.effective_chat.id
    
    # Get upcoming events (next 7 days)
    events = Event.get_upcoming_events(7)
    
    if not events:
        message = "There are no upcoming events in the next 7 days."
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    message = "<b>📅 Upcoming Events</b>\n\n"
    
    # Create buttons for each event
    keyboard = []
    
    for i, event in enumerate(events[:10]):  # Limit to 10 events to avoid too many buttons
        # Format the date
        event_date = event.date_time.strftime("%d %b, %H:%M")
        
        # Add event to message
        message += f"{i+1}. <b>{event.name}</b>\n"
        message += f"   📅 {event_date} | 📍 {event.location.name}\n"
        message += f"   {event.club.name}\n\n"
        
        # Add button for this event
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {event.name}",
            callback_data=f"{EVENT_PREFIX}{event.id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

def mytickets_command(update: Update, context: CallbackContext):
    """Handler for /mytickets command"""
    chat_id = update.effective_chat.id
    
    # Check if user is linked
    user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
    
    if not user:
        message = (
            "You need to link your SDU Event Hub account first.\n\n"
            "Use the /link command to connect your account."
        )
        
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    # Get user's tickets for upcoming events
    now = datetime.utcnow()
    tickets = []
    
    for ticket in user.tickets:
        if ticket.event.date_time > now and ticket.status != 'cancelled':
            tickets.append(ticket)
    
    if not tickets:
        message = (
            "You don't have any tickets for upcoming events.\n\n"
            "Use /events to browse and register for events."
        )
        
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    message = "<b>🎫 Your Tickets</b>\n\n"
    
    # Create buttons for each ticket
    keyboard = []
    
    for i, ticket in enumerate(tickets):
        event = ticket.event
        event_date = event.date_time.strftime("%d %b, %H:%M")
        
        # Add ticket to message
        message += f"{i+1}. <b>{event.name}</b>\n"
        message += f"   📅 {event_date} | 📍 {event.location.name}\n"
        message += f"   Status: <b>{ticket.status.capitalize()}</b>\n\n"
        
        # Add button for this ticket
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {event.name}",
            callback_data=f"{TICKET_PREFIX}{ticket.id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

def event_callback(update: Update, context: CallbackContext):
    """Handler for event button callbacks"""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    # Extract event ID from callback data
    event_id = int(query.data.replace(EVENT_PREFIX, ""))
    
    # Get event details
    event = Event.query.get(event_id)
    
    if not event:
        query.answer("Event not found!")
        return
    
    # Answer callback query to stop loading animation
    query.answer()
    
    # Format the date and time
    event_date = event.date_time.strftime("%A, %d %B %Y")
    event_time = event.date_time.strftime("%H:%M")
    
    message = f"<b>🎉 {event.name}</b>\n\n"
    message += f"<b>Club:</b> {event.club.name}\n"
    message += f"<b>Date:</b> {event_date}\n"
    message += f"<b>Time:</b> {event_time}\n"
    message += f"<b>Location:</b> {event.location.name}\n"
    
    if event.price > 0:
        message += f"<b>Price:</b> {event.price} KZT\n"
    else:
        message += "<b>Price:</b> Free\n"
    
    if event.max_attendees:
        tickets_sold = len(event.tickets)
        spots_left = event.max_attendees - tickets_sold
        message += f"<b>Spots left:</b> {spots_left}/{event.max_attendees}\n"
    
    message += f"\n<b>Description:</b>\n{event.description}\n"
    
    # Create URL to the event page on the website
    base_url = os.environ.get("BASE_URL", "http://localhost:5004")
    event_url = f"{base_url}/events/{event.id}"
    
    # Create keyboard for event actions
    keyboard = [
        [InlineKeyboardButton("Register on Website", url=event_url)],
        [InlineKeyboardButton("Back to Events", callback_data="cmd_events")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the message to show event details
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

def ticket_callback(update: Update, context: CallbackContext):
    """Handler for ticket button callbacks"""
    query = update.callback_query
    chat_id = update.effective_chat.id
    
    # Extract ticket ID from callback data
    ticket_id = int(query.data.replace(TICKET_PREFIX, ""))
    
    # Get ticket details
    ticket = db.session.query(User.tickets).get(ticket_id)
    
    if not ticket:
        query.answer("Ticket not found!")
        return
    
    # Answer callback query to stop loading animation
    query.answer()
    
    event = ticket.event
    
    # Format the date and time
    event_date = event.date_time.strftime("%A, %d %B %Y")
    event_time = event.date_time.strftime("%H:%M")
    
    message = f"<b>🎫 Ticket for {event.name}</b>\n\n"
    message += f"<b>Date:</b> {event_date}\n"
    message += f"<b>Time:</b> {event_time}\n"
    message += f"<b>Location:</b> {event.location.name}\n"
    message += f"<b>Status:</b> {ticket.status.capitalize()}\n"
    
    if ticket.qr_code_path:
        message += "\nYou can see your QR code on the website.\n"
    
    # Create URL to the ticket page on the website
    base_url = os.environ.get("BASE_URL", "http://localhost:5004")
    ticket_url = f"{base_url}/student/tickets/{ticket.id}"
    
    # Create keyboard for ticket actions
    keyboard = [
        [InlineKeyboardButton("View Ticket on Website", url=ticket_url)],
        [InlineKeyboardButton("Back to My Tickets", callback_data="cmd_tickets")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the message to show ticket details
    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

def command_callback(update: Update, context: CallbackContext):
    """Handler for command button callbacks"""
    query = update.callback_query
    command = query.data.replace("cmd_", "")
    
    # Answer callback query to stop loading animation
    query.answer()
    
    # Call the appropriate command handler
    if command == "link":
        return link_command(update, context)
    elif command == "events":
        return events_command(update, context)
    elif command == "tickets":
        return mytickets_command(update, context)
    elif command == "help":
        return help_command(update, context)
    
    return ConversationHandler.END

# Initialize command handlers if the telegram library is available
def setup_handlers():
    """Set up the command handlers for the Telegram bot"""
    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram library not available. Skipping handler setup.")
        return
    
    # Command handlers
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("events", events_command))
    dp.add_handler(CommandHandler("mytickets", mytickets_command))
    
    # Link command with conversation
    link_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("link", link_command)],
        states={
            AWAITING_CODE: [MessageHandler(Filters.text & ~Filters.command, link_code_handler)]
        },
        fallbacks=[CommandHandler("start", start_command)]
    )
    dp.add_handler(link_conv_handler)
    
    # Callback query handlers
    dp.add_handler(CallbackQueryHandler(event_callback, pattern=f"^{EVENT_PREFIX}"))
    dp.add_handler(CallbackQueryHandler(ticket_callback, pattern=f"^{TICKET_PREFIX}"))
    dp.add_handler(CallbackQueryHandler(command_callback, pattern="^cmd_"))
    
    logger.info("Telegram bot handlers initialized")

# Function to start the bot in a separate thread
def start_bot():
    """Start the Telegram bot in a separate thread"""
    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram library not available. Using mock bot.")
        return
    
    # Set up handlers
    setup_handlers()
    
    def run_bot():
        # Start the Bot
        logger.info("Starting Telegram bot...")
        updater.start_polling()
        updater.idle()
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True  # This ensures the thread will exit when the main program exits
    bot_thread.start()
    
    logger.info("Telegram bot started in background thread")

# Initialize the bot when this module is imported
if TELEGRAM_AVAILABLE:
    # Only try to set up and start the bot if we have the required library
    try:
        setup_handlers()
        logger.info(f"Telegram bot initialized with token starting with {BOT_TOKEN[:5]}...")
    except Exception as e:
        logger.error(f"Error initializing Telegram bot: {e}")