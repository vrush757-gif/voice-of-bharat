from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --------------------------
#  CREATE DATABASE TABLES
# --------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Posts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# --------------------------
#        HOME FEED
# --------------------------
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, timestamp FROM posts ORDER BY id DESC")
    posts = cursor.fetchall()
    conn.close()
    return render_template("index.html", posts=posts)

# --------------------------
#     CREATE POST
# --------------------------
@app.route("/write", methods=["GET", "POST"])
def write():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        if title and content:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO posts (title, content, timestamp) VALUES (?, ?, ?)",
                           (title, content, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))

    return render_template("write.html")

# --------------------------
#     VIEW POST + COMMENTS
# --------------------------
@app.route("/post/<int:post_id>")
def post(post_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # get the post
    cursor.execute("SELECT id, title, content, timestamp FROM posts WHERE id=?", (post_id,))
    post = cursor.fetchone()

    # get comments
    cursor.execute("SELECT comment, timestamp FROM comments WHERE post_id=? ORDER BY id DESC",
                   (post_id,))
    comments = cursor.fetchall()

    conn.close()
    return render_template("post.html", post=post, comments=comments)

# --------------------------
#        ADD COMMENT
# --------------------------
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    text = request.form.get("comment")

    if text:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (post_id, comment, timestamp) VALUES (?, ?, ?)",
                       (post_id, text, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

    return redirect(url_for("post", post_id=post_id))


# --------------------------
#      RUN SERVER
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
