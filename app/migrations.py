import sqlite3
import os
import logging
from flask import Flask, current_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the path to the SQLite database."""
    try:
        return current_app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    except:
        # Fallback to the default database path
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'instance', 'app.db')

def check_share_token_column():
    """Check if the share_token column exists in the user table."""
    # First try using SQLAlchemy
    try:
        from sqlalchemy import text
        from flask import current_app
        from app import db
        
        with current_app.app_context():
            # Execute PRAGMA statement through SQLAlchemy
            result = db.session.execute(text("PRAGMA table_info(user)")).fetchall()
            column_names = [column[1] for column in result]
            
            if 'share_token' in column_names:
                logger.info("share_token column already exists in user table")
                return True
            else:
                logger.warning("share_token column does not exist in user table")
                return False
    except Exception as e:
        logger.error(f"Error checking for share_token column using SQLAlchemy: {e}")
        # Fall back to direct SQLite connection
        
    # Fallback to direct SQLite connection
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'share_token' in column_names:
            logger.info("share_token column already exists in user table")
            return True
        else:
            logger.warning("share_token column does not exist in user table")
            return False
    except Exception as e:
        logger.error(f"Error checking for share_token column: {e}")
        return False
    finally:
        conn.close()

def add_share_token_column():
    """Add the share_token column to the user table."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found at {db_path}")
        return False
    
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'share_token' not in column_names:
            logger.info("Adding share_token column to user table...")
            
            # Add the share_token column
            cursor.execute("ALTER TABLE user ADD COLUMN share_token VARCHAR(64) UNIQUE")
            
            # Create index for faster lookups
            cursor.execute("CREATE INDEX ix_user_share_token ON user (share_token)")
            
            # Commit the changes
            conn.commit()
            logger.info("Successfully added share_token column and index")
            return True
        else:
            logger.info("share_token column already exists")
            return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def run_migrations():
    """Run all necessary migrations."""
    logger.info("Running database migrations...")
    
    # Check if share_token column exists
    if not check_share_token_column():
        # Add share_token column
        if add_share_token_column():
            logger.info("Migration successful: Added share_token column to user table")
        else:
            logger.warning("Migration failed: Could not add share_token column to user table")
    
    logger.info("Database migrations completed")