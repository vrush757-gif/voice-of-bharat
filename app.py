# app.py
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, g, render_template, request, redirect, url_for

DATABASE = Path("mini_twitter.db")  # SQLite file in project root

app = Flask(__name__)


def get_db():
    """Return a DB connection (saved on flask.g)."""
    db = getattr(g, "_database", None)
    if db is None:
        # ensure file exists (sqlite will create automatically on connect)
        db = sqlite3.connect(str(DATABASE), detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        g._database = db
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """
    Create tables if they don't exist.
    This is safe to call multiple times.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()


@app.before_first_request
def startup():
    # ensure DB exists and tables created
    init_db()


@app.route("/")
def index():
    # simple home page
    return render_template("index.html")


@app.route("/feed")
def feed():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM posts ORDER BY datetime(created_at) DESC")
    posts = cur.fetchall()
    return render_template("feed.html", posts=posts)


@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        username = request.form.get("username", "").strip() or "Anonymous"
        content = request.form.get("content", "").strip()
        if content:
            db = get_db()
            cur = db.cursor()
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO posts (username, content, created_at) VALUES (?, ?, ?)",
                (username, content, now),
            )
            db.commit()
            return redirect(url_for("feed"))
        else:
            # nothing posted — re-render page with a message (very simple)
            return render_template("create_post.html", error="Please write something.")
    return render_template("create_post.html")


@app.route("/about")
def about():
    return render_template("about.html")


# simple handlers for like/repost — non-auth, very lightweight (no protection)
@app.route("/like/<int:post_id>")
def like(post_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    db.commit()
    return redirect(url_for("feed"))


@app.route("/repost/<int:post_id>")
def repost(post_id):
    db = get_db()
    cur = db.cursor()
    # increment reposts count and redirect
    cur.execute("UPDATE posts SET reposts = reposts + 1 WHERE id = ?", (post_id,))
    db.commit()
    return redirect(url_for("feed"))


if __name__ == "__main__":
    # For local debugging only.
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
