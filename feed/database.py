import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'newsfeed.db')

def init_db():
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()

    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            bio TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user) REFERENCES users(username)
        )
    ''')
    # Create interactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            post_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user) REFERENCES users(username),
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_post(user, content):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("INSERT INTO posts (user, content) VALUES (?, ?)", (user, content))
    conn.commit()
    conn.close()

def get_posts():
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT id, user, content, timestamp FROM posts ORDER BY id ASC")  # Add id to SELECT
    posts = c.fetchall()
    conn.close()
    return posts

def add_interaction(user, post_id, action):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("INSERT INTO interactions (user, post_id, action) VALUES (?, ?, ?)", (user, post_id, action))
    conn.commit()
    conn.close()

def get_user_interactions(user):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT post_id FROM interactions WHERE user = ?", (user,))
    interactions = [row[0] for row in c.fetchall()]
    conn.close()
    return interactions

def get_likes_count():
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT post_id, COUNT(*) as like_count FROM interactions WHERE action = 'like' GROUP BY post_id")
    like_counts = c.fetchall()
    conn.close()
    return like_counts

def create_user(username, password, display_name=None, bio=None):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        c.execute(
            "INSERT INTO users (username, password_hash, display_name, bio) VALUES (?, ?, ?, ?)",
            (username, password_hash, display_name or username, bio)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and check_password_hash(result[0], password):
        return True
    return False

def get_user_profile(username):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT username, display_name, bio, created_at FROM users WHERE username = ?", (username,))
    profile = c.fetchone()
    conn.close()
    return profile

def update_user_profile(username, display_name=None, bio=None):
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    if display_name and bio:
        c.execute("UPDATE users SET display_name = ?, bio = ? WHERE username = ?", 
                 (display_name, bio, username))
    elif display_name:
        c.execute("UPDATE users SET display_name = ? WHERE username = ?", 
                 (display_name, username))
    elif bio:
        c.execute("UPDATE users SET bio = ? WHERE username = ?", 
                 (bio, username))
    conn.commit()
    conn.close()