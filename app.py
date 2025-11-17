from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Create database table (runs once)
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/feed")
def feed():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()
    conn.close()
    return render_template("feed.html", posts=posts)

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        content = request.form.get("content")
        if content:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO posts (content) VALUES (?)", (content,))
            conn.commit()
            conn.close()
            return redirect(url_for("feed"))
    return render_template("create.html")

@app.route("/like/<int:id>")
def like(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("feed"))

@app.route("/repost/<int:id>")
def repost(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("UPDATE posts SET reposts = reposts + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("feed"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
