import os
import sqlite3

# Define the path for the database relative to the current file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'newsfeed.db')

def init_db():
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()

    # Create the posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create the interactions table 
    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            post_id INTEGER,
            action TEXT,  -- Example values: 'view', 'like', 'comment'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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

#def get_posts():
 #   conn = sqlite3.connect('newsfeed.db')
  #  c = conn.cursor()
   # c.execute("SELECT user, content, timestamp FROM posts ORDER BY timestamp DESC")
   # posts = c.fetchall()
   # conn.close()
   # return posts

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