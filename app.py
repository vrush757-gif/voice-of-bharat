from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------------------------
# DATABASE SETUP
# ---------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# HOME PAGE (FEED)
# ---------------------------
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, timestamp FROM posts ORDER BY id DESC")
    posts = cursor.fetchall()
    conn.close()

    return render_template("index.html", posts=posts)

# ---------------------------
# WRITE PAGE (FORM)
# ---------------------------
@app.route("/write", methods=["GET", "POST"])
def write():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("write.html")

# ---------------------------
# RUN APP
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
