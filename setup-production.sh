#!/bin/bash

# SDU Event Hub - Production Setup Script

set -e  # Exit on any error

# Check if running as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root"
    exit 1
fi

# Installation directory
INSTALL_DIR="$(pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display status messages
function echo_status() {
    echo -e "${GREEN}[+] $1${NC}"
}

# Function to display warning messages
function echo_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Function to display error messages
function echo_error() {
    echo -e "${RED}[!] $1${NC}"
}

# Check if Docker is installed
echo_status "Checking for Docker installation..."
if ! command -v docker &> /dev/null; then
    echo_warning "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $SUDO_USER
    systemctl enable docker
    systemctl start docker
else
    echo_status "Docker is already installed."
fi

# Check if Docker Compose is installed
echo_status "Checking for Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    echo_warning "Docker Compose not found. Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
else
    echo_status "Docker Compose is already installed."
fi

# Create .env file if it doesn't exist
echo_status "Setting up environment variables..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f "$INSTALL_DIR/.env.example" ]; then
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        echo_warning "Created .env file from .env.example. Please edit it with your production settings."
        echo_warning "Run: nano $INSTALL_DIR/.env"
    else
        echo_error ".env.example file not found. Please create a .env file manually."
        exit 1
    fi
else
    echo_status ".env file already exists."
fi

# Create required directories
echo_status "Creating required directories..."
mkdir -p "$INSTALL_DIR/nginx/certbot/conf"
mkdir -p "$INSTALL_DIR/nginx/certbot/www"
mkdir -p "$INSTALL_DIR/nginx/ssl"
mkdir -p "$INSTALL_DIR/instance"

# Ask for domain name
read -p "Enter your domain name (e.g., events.sdu.edu.kz): " DOMAIN_NAME

# Update Nginx configuration
echo_status "Updating Nginx configuration..."
if [ -f "$INSTALL_DIR/nginx/conf.d/app.conf" ]; then
    sed -i "s/events.sdu.edu.kz/$DOMAIN_NAME/g" "$INSTALL_DIR/nginx/conf.d/app.conf"
    echo_status "Updated domain name in Nginx configuration."
else
    echo_error "Nginx configuration file not found."
    exit 1
fi

# Ask for email for SSL certificate
read -p "Enter your email for SSL certificate notifications: " EMAIL

# Generate SSL certificates
echo_status "Setting up SSL certificates..."
docker-compose up -d nginx
echo_status "Getting SSL certificate from Let's Encrypt..."
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot \
    --email "$EMAIL" -d "$DOMAIN_NAME" --agree-tos --no-eff-email

# Update .env file with domain
echo_status "Updating BASE_URL in .env file..."
sed -i "s|BASE_URL=.*|BASE_URL=https://$DOMAIN_NAME|g" "$INSTALL_DIR/.env"

# Start all services
echo_status "Starting all services..."
docker-compose down
docker-compose up -d

# Wait for services to be ready
echo_status "Waiting for services to be ready..."
sleep 10

# Run database migrations
echo_status "Running database migrations..."
docker-compose exec -T web flask db upgrade

echo_status "SDU Event Hub has been successfully set up!"
echo_status "You can access it at: https://$DOMAIN_NAME"
echo_warning "Remember to create an admin user (see DEPLOYMENT.md for instructions)"
echo_status "To monitor the application, run: docker-compose logs -f"