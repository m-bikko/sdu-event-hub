# Docker Deployment Guide for SDU Event Hub

This guide explains how to deploy the SDU Event Hub application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Configure Environment Variables (Optional)

Create a `.env` file in the root directory of the project to customize your deployment:

```bash
# Security
SECRET_KEY=your_secure_random_key

# Application URL (use your domain or IP if deploying to a server)
BASE_URL=http://yourdomain.com

# Telegram Bot (if using telegram integration)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_BOT_USERNAME=YourBotUsername
```

### 3. Choose Database Type

By default, the application uses SQLite. To use PostgreSQL instead:

1. Open `docker-compose.yml`
2. Uncomment the `DATABASE_URL` line in the `web` service environment section

### 4. Build and Start the Application

```bash
docker-compose up -d
```

This will:
- Build the Docker image based on your Dockerfile
- Create containers for the web application and database
- Start the services in detached mode

### 5. Access the Application

Once the containers are running, access the application at:

- http://localhost:5004

### 6. Managing the Application

Stop the application:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

Restart the application:
```bash
docker-compose restart
```

### 7. Data Persistence

The application uses Docker volumes for data persistence:

- `app_data`: Stores the SQLite database and instance data
- `app_static`: Stores uploaded files and static assets
- `postgres_data`: Stores PostgreSQL data (if using PostgreSQL)

These volumes persist data even when containers are removed.

## Troubleshooting

### Database Connection Issues

If you experience database connection problems:

1. Check logs: `docker-compose logs -f web`
2. Verify PostgreSQL is running (if using PostgreSQL): `docker-compose ps`
3. Try restarting the services: `docker-compose restart`

### File Permission Issues

If you encounter permission errors for uploaded files or database:

1. Check logs for specific errors
2. Ensure volumes are properly mounted

## Updating the Application

To update to a new version:

1. Pull the latest code changes
2. Rebuild and restart:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```