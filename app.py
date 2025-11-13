from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = os.path.join(app.root_path, 'database.db')

# ---------- Database Setup ----------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/feed')
def feed():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    return render_template('feed.html', posts=posts)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        username = request.form['username']
        content = request.form['content']
        db = get_db()
        db.execute("INSERT INTO posts (username, content) VALUES (?, ?)", (username, content))
        db.commit()
        return redirect(url_for('feed'))
    return render_template('create_post.html')

# ---------- Main ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000, debug=False)
