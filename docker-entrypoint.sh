#!/bin/bash
set -e

echo "Starting SDU Event Hub application..."

# Ensure database directory exists with correct permissions
echo "Setting up instance directory..."
mkdir -p /app/instance
touch /app/instance/.keep

# Determine which database to use
if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Using PostgreSQL database"
    
    # Extract host and port from DATABASE_URL
    DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]+):.*/\1/')
    DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+).*/\1/')
    DB_USER=$(echo $DATABASE_URL | sed -E 's/.*:\/\/([^:]+):.*/\1/')
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
        echo "Waiting for PostgreSQL to be ready... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "PostgreSQL did not become ready in time, but continuing anyway..."
    else
        echo "PostgreSQL is ready!"
    fi
    
    # Run database migrations for PostgreSQL
    echo "Running database migrations..."
    flask db upgrade || echo "Migration failed, but continuing as database might be already set up"
    
else
    echo "Using SQLite database at /app/instance/app.db"
    
    # Initialize SQLite database if it doesn't exist
    if [ ! -f "/app/instance/app.db" ]; then
        echo "Initializing SQLite database..."
        python init_db.py || echo "SQLite initialization failed, but continuing..."
    fi
    
    # Run migrations for SQLite
    echo "Running database migrations..."
    flask db upgrade || echo "Migration failed, but continuing as database might be already set up"
fi

# Set up share tokens table
echo "Setting up share tokens table..."
python create_share_tokens_table.py || echo "Share tokens table setup failed, but continuing"

# Start Gunicorn server
echo "Starting the web server on port 5000 (mapped to external port 5004)..."
exec gunicorn --bind 0.0.0.0:5000 \
    --workers 2 \
    --threads 2 \
    --worker-class=gthread \
    --access-logfile - \
    --error-logfile - \
    --timeout 120 \
    --log-level info \
    run:app