import sqlite3

def init_db():
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
    c.execute("SELECT user, content, timestamp FROM posts ORDER BY timestamp DESC")
    posts = c.fetchall()
    conn.close()
    return posts