import sqlite3


conn = sqlite3.connect('blog.db')

conn = sqlite3.connect('blog.db')
with open('schema.sql') as f:
    conn.executescript(f.read())
cur = conn.cursor()
"""inserting a default user and one category to see if it works """
cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('admin', 'password'))
cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", ('General',))
"""insert one sample post to see if it works """
cur.execute("INSERT OR IGNORE INTO posts (title, content, user_id, category_id) VALUES (?, ?, ?, ?)",
            ('Welcome Post', 'This is the 1st post!', 1, 1))
conn.commit()
conn.close()
