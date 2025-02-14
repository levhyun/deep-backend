import sqlite3
import os

os.makedirs("database", exist_ok=True)

conn = sqlite3.connect("database/database.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def init_db():
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        extra_info TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS deepers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        extra_info TEXT,
        memo TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')

    conn.commit()
