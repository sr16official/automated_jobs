import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'jobs.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with the required tables."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create jobs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            url TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score INTEGER DEFAULT 0,
            match_reasons TEXT
        )
    ''')
    
    # Simple migration: Add columns if they don't exist (for existing DBs)
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN score INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column likely exists
        
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN match_reasons TEXT")
    except sqlite3.OperationalError:
        pass # Column likely exists

    try:
        c.execute("ALTER TABLE jobs ADD COLUMN contact_email TEXT")
    except sqlite3.OperationalError:
        pass # Column likely exists
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")
