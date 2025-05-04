# Deploying SDU Event Hub on Google Cloud VM

This guide provides simple steps to deploy SDU Event Hub on a Google Cloud VM using Docker.

## Prerequisites

- Google Cloud account with Compute Engine access
- VM instance with at least 2 vCPUs and 4GB RAM
- Basic knowledge of Linux commands

## Deployment Steps

### 1. Set Up Your VM Instance

1. Log in to Google Cloud Console
2. Go to **Compute Engine > VM Instances**
3. Click **Create Instance**
4. Configure your VM:
   - Name: `sdu-event-hub`
   - Region/Zone: Choose one close to your users
   - Machine Type: e2-medium (2 vCPU, 4 GB memory) or larger
   - Boot Disk: Ubuntu 20.04 LTS
   - **Important:** Allow HTTP/HTTPS traffic in the firewall settings
5. Click **Create**

### 2. Connect to Your VM

Connect to your VM using SSH (either through Google Cloud Console or `gcloud` command).

### 3. Install Docker and Docker Compose

```bash
# Update package index
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to the docker group to avoid using sudo
sudo usermod -aG docker $USER

# Apply the group change (or log out and back in)
newgrp docker
```

### 4. Download the Application

```bash
# Clone the repository
git clone https://github.com/yourusername/sdu-event-hub.git
cd sdu-event-hub
```

### 5. Configure the Application

Create a `.env` file with basic configuration:

```bash
# Get the external IP address of your VM
EXTERNAL_IP=$(curl -s ifconfig.me)

# Create .env file
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 24)
FLASK_ENV=production
BASE_URL=http://$EXTERNAL_IP
TELEGRAM_BOT_TOKEN=8100465500:AAFq0ZVr1EhZUuUksRc3nfUXJUZi2pIXgOI
TELEGRAM_BOT_USERNAME=SDUEventHubBot
EOF

echo "Your app will be accessible at: http://$EXTERNAL_IP:5004"
```

### 6. Start the Application

```bash
# Build and start the application
docker-compose up -d

# Check if containers are running
docker-compose ps
```

### 7. Create an Admin User

```bash
# Create an admin user
docker-compose exec web python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    if not User.query.filter_by(email='admin@sdu.edu.kz').first():
        admin = User(first_name='Admin', last_name='User', email='admin@sdu.edu.kz', 
                    password='admin123', role='admin')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')
"
```

### 8. Access Your Application

Open your browser and navigate to `http://YOUR_VM_EXTERNAL_IP:5004`

Login with:
- Email: `admin@sdu.edu.kz`
- Password: `admin123`

**Important:** Change the admin password immediately after your first login!

## Managing Your Application

### View Logs

```bash
# View application logs
docker-compose logs -f web
```

### Stop the Application

```bash
# Stop the application
docker-compose down
```

### Update the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup the Database

```bash
# Backup the SQLite database
docker-compose cp web:/app/instance/app.db ./backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Database Connection Issues

If you encounter database errors:

```bash
# Check database file permissions
docker-compose exec web ls -la /app/instance/

# Manually initialize the database
docker-compose exec web python init_db.py

# Manually create share tokens table
docker-compose exec web python create_share_tokens_table.py
```

### Container Won't Start

```bash
# Check container logs
docker-compose logs web

# Rebuild the container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Shareable Links Feature

The application supports shareable user profile links. To use this feature:

1. Log in as an admin user
2. Go to User Management
3. For any user, click "Generate" to create a shareable link
4. The link will be accessible without login and display the user's profile information and tickets

## Security Recommendations

1. Change the default admin password immediately
2. Update `SECRET_KEY` in your `.env` file
3. Set up Google Cloud Firewall rules to limit access to your application
4. Regularly backup your database
5. Keep your system and Docker images updated