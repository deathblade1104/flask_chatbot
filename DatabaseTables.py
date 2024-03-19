import sqlite3
import os

# Load database file path from environment variable
DATABASE = os.getenv('DATABASE_PATH', 'database.db')

class DatabaseTables:
    @staticmethod
    def create_user_table():
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON users (email)')

    @staticmethod
    def create_chat_log_table():
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    request TEXT NOT NULL,
                    response TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON chat_log (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_active ON chat_log (is_active)')
