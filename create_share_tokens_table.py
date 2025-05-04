#!/usr/bin/env python
"""
Script to create the user_share_tokens table in the database.
Run this script to set up the shareable links feature.
"""
import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

def create_user_share_tokens_table_sqlite():
    """Create the user_share_tokens table in SQLite database if it doesn't exist."""
    # Path to the SQLite database
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    print(f"Looking for SQLite database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: SQLite database file not found at {DB_PATH}")
        return False
    
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_share_tokens'")
        if cursor.fetchone():
            print("user_share_tokens table already exists in SQLite.")
            return True
        
        # Create the table
        print("Creating user_share_tokens table in SQLite...")
        cursor.execute('''
        CREATE TABLE user_share_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token VARCHAR(64) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
        ''')
        
        # Create index on token for faster lookups
        cursor.execute('CREATE INDEX ix_user_share_tokens_token ON user_share_tokens (token)')
        
        # Create index on user_id for faster lookups
        cursor.execute('CREATE INDEX ix_user_share_tokens_user_id ON user_share_tokens (user_id)')
        
        # Commit the changes
        conn.commit()
        print("Successfully created user_share_tokens table and indexes in SQLite.")
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def create_user_share_tokens_table_postgres():
    """Create the user_share_tokens table in PostgreSQL database if it doesn't exist."""
    # Get PostgreSQL connection details from environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        return False
    
    if not database_url.startswith('postgresql://'):
        print(f"Not a PostgreSQL database URL: {database_url}")
        return False
    
    print(f"Using PostgreSQL database URL: {database_url}")
    
    # Parse the database URL
    parsed_url = urlparse(database_url)
    dbname = parsed_url.path[1:]  # Remove leading slash
    user = parsed_url.username
    password = parsed_url.password
    host = parsed_url.hostname
    port = parsed_url.port or 5432
    
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if the table already exists
        cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name='user_share_tokens')")
        if cursor.fetchone()[0]:
            print("user_share_tokens table already exists in PostgreSQL.")
            return True
        
        # Create the table
        print("Creating user_share_tokens table in PostgreSQL...")
        cursor.execute('''
        CREATE TABLE user_share_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token VARCHAR(64) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES "user"(id)
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX ix_user_share_tokens_token ON user_share_tokens (token)')
        cursor.execute('CREATE INDEX ix_user_share_tokens_user_id ON user_share_tokens (user_id)')
        
        # Commit the changes
        conn.commit()
        print("Successfully created user_share_tokens table and indexes in PostgreSQL.")
        return True
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def create_user_share_tokens_table():
    """Create the user_share_tokens table in the appropriate database."""
    # Check if we're using PostgreSQL
    if 'DATABASE_URL' in os.environ and os.environ['DATABASE_URL'].startswith('postgresql://'):
        return create_user_share_tokens_table_postgres()
    else:
        return create_user_share_tokens_table_sqlite()

if __name__ == "__main__":
    print("=== User Share Tokens Table Creation ===")
    success = create_user_share_tokens_table()
    if success:
        print("\nTable created successfully.")
        print("You can now generate share tokens for users in the admin interface.")
    else:
        print("\nFailed to create table.")
        sys.exit(1)