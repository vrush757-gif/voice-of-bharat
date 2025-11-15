# app.py
import os
import sqlite3
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_from_directory, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# Configuration
DATABASE = os.path.join(os.path.dirname(__file__), "mini_twitter.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DATABASE"] = DATABASE

# ----- DB helpers -----
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        # enable row access by name
        db = g._database = sqlite3.connect(app.config["DATABASE"], check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cur = db.cursor()
    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        fullname TEXT,
        bio TEXT,
        profile_pic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Posts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        content TEXT,
        image_filename TEXT,
        likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    db.commit()

# ----- Utilities -----
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def current_user():
    if "user_id" in session:
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        return cur.fetchone()
    return None

# ----- Routes -----
@app.route("/")
def index():
    # show a simple landing page or redirect to feed if logged in
    user = current_user()
    if user:
        return redirect(url_for("feed"))
    return render_template("index.html", user=user)

@app.route("/home")
def home():
    user = current_user()
    return render_template("home.html", user=user)

@app.route("/feed")
def feed():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cur.fetchall()
    user = current_user()
    return render_template("feed.html", posts=posts, user=user)

@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    user = current_user()
    if not user:
        flash("You must be logged in to create posts.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        file = request.files.get("image")
        filename = None
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db = get_db()
        db.execute(
            "INSERT INTO posts (user_id, username, content, image_filename) VALUES (?, ?, ?, ?)",
            (user["id"], user["username"], content, filename)
        )
        db.commit()
        flash("Post created.", "success")
        return redirect(url_for("feed"))

    return render_template("create_post.html", user=user)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        fullname = request.form.get("fullname", "")
        if not username or not password:
            flash("Please provide username and password.", "warning")
            return redirect(url_for("signup"))

        db = get_db()
        try:
            hashed = generate_password_hash(password)
            db.execute("INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)",
                       (username, hashed, fullname))
            db.commit()
            flash("Account created. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger")
            return redirect(url_for("signup"))

    return render_template("signup.html", user=current_user())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("feed"))
        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html", user=current_user())

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route("/profile/<username>")
def profile(username):
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    u = cur.fetchone()
    if not u:
        flash("User not found.", "warning")
        return redirect(url_for("feed"))
    posts = db.execute("SELECT * FROM posts WHERE username = ? ORDER BY created_at DESC", (username,)).fetchall()
    return render_template("profile.html", profile_user=u, posts=posts, user=current_user())

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        fullname = request.form.get("fullname", "")
        bio = request.form.get("bio", "")
        file = request.files.get("profile_pic")
        filename = user["profile_pic"]
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"profile_{user['id']}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db = get_db()
        db.execute("UPDATE users SET fullname = ?, bio = ?, profile_pic = ? WHERE id = ?",
                   (fullname, bio, filename, user["id"]))
        db.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile", username=user["username"]))
    return render_template("edit_profile.html", user=user)

@app.route("/like/<int:post_id>")
def like(post_id):
    user = current_user()
    if not user:
        flash("Log in to like posts.", "warning")
        return redirect(url_for("login"))
    db = get_db()
    db.execute("UPDATE posts SET likes = COALESCE(likes,0) + 1 WHERE id = ?", (post_id,))
    db.commit()
    return redirect(request.referrer or url_for("feed"))

@app.route("/repost/<int:post_id>")
def repost(post_id):
    user = current_user()
    if not user:
        flash("Log in to repost.", "warning")
        return redirect(url_for("login"))
    db = get_db()
    original = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not original:
        flash("Original post not found.", "warning")
        return redirect(url_for("feed"))
    db.execute("INSERT INTO posts (user_id, username, content, image_filename) VALUES (?, ?, ?, ?)",
               (user["id"], user["username"], f"Repost: {original['content']}", original["image_filename"]))
    db.commit()
    flash("Reposted.", "success")
    return redirect(url_for("feed"))

@app.route("/admin")
def admin():
    user = current_user()
    # safety: only allow admin by username 'admin' (or extend to role)
    if not user or user["username"] != "admin":
        flash("Admin access required.", "warning")
        return redirect(url_for("login"))
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    posts = db.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", users=users, posts=posts, user=user)

# If templates reference uploaded images, this route is optional (Flask serves static by default)
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ----- Start up -----
if __name__ == "__main__":
    # initialize DB if missing
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
