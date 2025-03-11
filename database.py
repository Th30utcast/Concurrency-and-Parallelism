import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Users table
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    preferences TEXT DEFAULT '{"notifications": true}'
                )
            ''')
            
            # Messages table
            c.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP,
                    is_file BOOLEAN DEFAULT FALSE,
                    file_path TEXT,
                    FOREIGN KEY (sender_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def get_username(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            return result[0] if result else None