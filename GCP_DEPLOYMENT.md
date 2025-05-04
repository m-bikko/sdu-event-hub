# SDU Event Hub - Google Cloud VM Deployment Guide

This guide provides simplified instructions for deploying the SDU Event Hub application on a Google Cloud VM instance using just the external IP (no domain name).

## Prerequisites

- Google Cloud Platform account
- VM instance with Ubuntu 20.04+ (e.g., e2-medium or larger)
- External IP assigned to your VM

## Deployment Steps

### 1. Set Up Your VM Instance

1. Log in to Google Cloud Console
2. Go to Compute Engine > VM Instances
3. Create a new instance:
   - Select Ubuntu 20.04 or newer
   - Recommend at least 2 vCPUs and 4GB RAM
   - Enable HTTP/HTTPS traffic in the firewall rules
   - Assign an external static IP

### 2. Connect to Your VM

```bash
# SSH into your VM using the Google Cloud console or gcloud command
gcloud compute ssh YOUR_VM_NAME --zone YOUR_ZONE
```

### 3. Install Docker and Docker Compose

```bash
# Update packages
sudo apt update
sudo apt upgrade -y

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to the docker group
sudo usermod -aG docker $USER

# Apply group changes (or log out and back in)
newgrp docker
```

### 4. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/sdu-event-hub.git
cd sdu-event-hub
```

### 5. Configure the Application for External IP

Create or edit an `.env` file:

```bash
# Get your VM's external IP
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "Your external IP is: $EXTERNAL_IP"

# Create .env file
cat > .env << EOF
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
TELEGRAM_BOT_TOKEN=8100465500:AAFq0ZVr1EhZUuUksRc3nfUXJUZi2pIXgOI
TELEGRAM_BOT_USERNAME=SDUEventHubBot
BASE_URL=http://$EXTERNAL_IP
EOF
```

### 6. Modify the Nginx Configuration for External IP

Create a simplified Nginx configuration:

```bash
# Create directory if it doesn't exist
mkdir -p nginx/conf.d

# Create Nginx configuration file
cat > nginx/conf.d/app.conf << EOF
server {
    listen 80;
    
    # No server_name directive to accept all hostnames
    
    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias /usr/share/nginx/html/static;
    }
}
EOF
```

### 7. Modify Docker Compose File for Simplified Setup

Create a simplified docker-compose.yml file:

```bash
cat > docker-compose.yml << EOF
version: '3.8'

services:
  # Web application
  web:
    build: .
    container_name: sdu_event_hub_web
    restart: always
    depends_on:
      - postgres
    environment:
      - FLASK_APP=run.py
      - FLASK_ENV=production
      # Using SQLite for simplicity - uncomment next line if you prefer PostgreSQL
      # - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/sdu_event_hub
      - SECRET_KEY=\${SECRET_KEY:-default_secret_key_change_in_production}
      - TELEGRAM_BOT_TOKEN=\${TELEGRAM_BOT_TOKEN:-8100465500:AAFq0ZVr1EhZUuUksRc3nfUXJUZi2pIXgOI}
      - TELEGRAM_BOT_USERNAME=\${TELEGRAM_BOT_USERNAME:-SDUEventHubBot}
      - BASE_URL=\${BASE_URL:-http://localhost}
    volumes:
      - static_data:/app/app/static
      - db_data:/app/instance
    expose:
      - 5000

  # Nginx service for serving static files and as a reverse proxy
  nginx:
    image: nginx:alpine
    container_name: sdu_event_hub_nginx
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - static_data:/usr/share/nginx/html/static
    depends_on:
      - web

  # PostgreSQL database (needed for dependencies even if using SQLite)
  postgres:
    image: postgres:14-alpine
    container_name: sdu_event_hub_postgres
    restart: always
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=sdu_event_hub
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  static_data:
  db_data:  # Added for SQLite database storage
EOF
```

### 8. Start the Services

```bash
# Build and start all services
docker-compose up -d

# Wait for services to initialize
sleep 15
```

### 9. Create an Admin User

```bash
# Create an admin user
docker-compose exec -T web python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    admin = User(first_name='Admin', last_name='User', email='admin@sdu.edu.kz', 
                 password='admin_password', role='admin')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully')
"
```

### 10. Access Your Application

Your application is now running and accessible at:
- `http://YOUR_EXTERNAL_IP`

You can log in with:
- Email: admin@sdu.edu.kz
- Password: admin_password

## Managing Your Application

### View Application Logs

```bash
# View logs from the web application
docker-compose logs -f web

# View logs from Nginx
docker-compose logs -f nginx
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart a specific service
docker-compose restart web
```

### Update the Application

```bash
# Pull the latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup the Database

```bash
# Backup the database
docker-compose exec postgres pg_dump -U postgres sdu_event_hub > backup_$(date +%Y%m%d).sql
```

## Testing the Shareable Links Feature

1. Log in as the admin user
2. Go to User Management
3. For any user, click "Generate" to create a shareable link
4. Copy the link and open it in a different browser (or incognito window)
5. You should see the user's profile without needing to log in

## Troubleshooting

### Database Connection Issues

If you see errors like `sqlite3.OperationalError: unable to open database file`:

```bash
# Check if instance directory exists in the container
docker-compose exec web ls -la /app/instance

# Verify database file ownership and permissions
docker-compose exec web ls -la /app/instance/app.db

# You can recreate the database if needed
docker-compose exec web rm -f /app/instance/app.db
docker-compose exec web python init_db.py
docker-compose restart web
```

### Manually Creating the Share Tokens Table

If the share tokens feature isn't working, you can manually create the table:

```bash
docker-compose exec web python create_share_tokens_table.py
```

### Container Startup Issues

If the container won't start:

```bash
# Check the container logs
docker-compose logs web

# Try rebuilding the container
docker-compose down
docker-compose build
docker-compose up -d
```

## Security Considerations

Since this setup uses HTTP without SSL, consider these security recommendations:

1. Set up a firewall rule to restrict access to your VM (Google Cloud Firewall)
2. Change the default admin password immediately
3. Use a strong SECRET_KEY value in your .env file
4. Consider setting up a VPN for accessing the admin features if working in a public environment
5. Regularly backup your database