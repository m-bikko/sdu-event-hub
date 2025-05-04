import sqlite3
import os

# Path to the SQLite database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')

def add_share_token_column():
    """
    Add the share_token column to the user table in the SQLite database
    """
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
            print("Adding share_token column to user table...")
            
            # Add the share_token column
            cursor.execute("ALTER TABLE user ADD COLUMN share_token VARCHAR(64) UNIQUE")
            
            # Create index for faster lookups
            cursor.execute("CREATE INDEX ix_user_share_token ON user (share_token)")
            
            # Commit the changes
            conn.commit()
            print("Successfully added share_token column and index")
        else:
            print("share_token column already exists")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("\n=== Share Token Database Migration ===\n")
    print("This script will add the share_token column to the user table.")
    print("This is required for the shareable user profile links feature to work.")
    
    add_share_token_column()
    
    print("\n=== Migration Complete ===\n")
    print("To use this feature, restart your Flask application.")