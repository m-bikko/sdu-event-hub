# SDU Event Hub - Deployment Guide

This guide provides instructions for deploying the SDU Event Hub application using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your server
- Domain name pointing to your server (e.g., events.sdu.edu.kz)
- Basic understanding of Docker, Nginx, and SSL certificates

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sdu-event-hub.git
cd sdu-event-hub
```

### 2. Configure Environment Variables

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
nano .env
```

Make sure to update the following variables:
- `SECRET_KEY`: Generate a strong random key
- `POSTGRES_PASSWORD`: Set a secure database password
- `TELEGRAM_BOT_TOKEN`: Add your Telegram bot token (already set to 8100465500:AAFq0ZVr1EhZUuUksRc3nfUXJUZi2pIXgOI)
- `BASE_URL`: Set to your domain name with https protocol
- Any other service-specific credentials (Stripe, email, etc.)

### 3. Update Nginx Configuration

Update the server_name in the Nginx configuration:

```bash
nano nginx/conf.d/app.conf
```

Replace `events.sdu.edu.kz` with your actual domain name.

### 4. Initialize SSL Certificates

Before starting the main services, initialize SSL certificates:

```bash
# Create required directories
mkdir -p nginx/certbot/conf nginx/certbot/www

# Replace with your email and domain
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot \
    --email your-email@example.com -d your-domain.com --agree-tos --no-eff-email \
    --staging  # Remove this flag for production certificates
```

If the staging certificate works, run the command again without the `--staging` flag to get a production certificate.

### 5. Start the Services

Build and start all services:

```bash
docker-compose up -d
```

This will start:
- The Flask web application
- PostgreSQL database
- Redis cache
- Nginx web server
- Certbot for SSL certificate renewal

### 6. Initialize the Database

The first time you run the application, the database will be automatically initialized with the tables defined in your models. If you need to run migrations:

```bash
docker-compose exec web flask db upgrade
```

The database initialization now includes setting up the user_share_tokens table for the shareable links feature. This is handled automatically by the docker-entrypoint.sh script.

### 7. Create an Admin User

Create an initial admin user:

```bash
docker-compose exec web flask shell
```

In the Flask shell:

```python
from app import db
from app.models import User
admin = User(first_name="Admin", last_name="User", email="admin@sdu.edu.kz", 
             password="strong_password_here", role="admin")
db.session.add(admin)
db.session.commit()
exit()
```

### 8. Monitoring the Application

View the logs to ensure everything is running correctly:

```bash
docker-compose logs -f web  # View web application logs
docker-compose logs -f nginx  # View nginx logs
```

## Updating the Application

To update the application:

```bash
git pull  # Get the latest code
docker-compose build web  # Rebuild the web service
docker-compose up -d  # Restart services
```

## Backing Up the Database

Regularly back up your database:

```bash
docker-compose exec postgres pg_dump -U postgres sdu_event_hub > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### If the web service fails to start:

Check logs:
```bash
docker-compose logs web
```

### If Nginx fails to start:

Check the Nginx configuration:
```bash
docker-compose exec nginx nginx -t
```

### If SSL certificates aren't working:

Verify certificate paths and permissions:
```bash
docker-compose exec nginx ls -la /etc/letsencrypt/live/your-domain.com/
```

## Additional Configuration

### Telegram Bot

The Telegram bot is automatically started with the application. To verify it's working properly:

```bash
docker-compose logs web | grep "Telegram bot"
```

You should see messages indicating the bot has started successfully.

### Shareable User Links Feature

The application now supports shareable user profile links that allow admins to generate unique URLs for users. These links display the user's profile information and tickets without requiring login.

For detailed documentation on this feature, refer to the [SHAREABLE_LINKS.md](SHAREABLE_LINKS.md) file.

To verify the feature is working properly:

1. Log in as an admin user
2. Go to the User Management section
3. Generate a share token for a user
4. Test the generated link in a different browser (or incognito window)

You can check if the user_share_tokens table was created successfully with:

```bash
docker-compose exec postgres psql -U postgres -d sdu_event_hub -c "\dt user_share_tokens"
```

If there are any issues with the table creation, check the web service logs:

```bash
docker-compose logs web | grep "share tokens table"
```

### Scheduled Tasks

If you need to run scheduled tasks (like sending event reminders), consider adding a Celery worker and scheduler to the docker-compose file.

## Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Regularly update Docker images to patch security vulnerabilities
- Set up automated database backups
- Consider implementing rate limiting in Nginx for sensitive endpoints