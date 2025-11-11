from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ✅ DATABASE INITIALIZATION
def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()

        # users table
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT,
            profile_pic TEXT
        )
        """)

        # posts table (✅ includes image_filename column)
        c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            caption TEXT,
            image_filename TEXT,
            likes INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0
        )
        """)

        # comments table (✅ new addition)
        c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
        """)

        conn.commit()


# ✅ HOME (LOGIN PAGE)
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()

        if user:
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")


# ✅ REGISTER PAGE
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash("Account created! Please log in.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username already exists")
                return redirect(url_for("register"))

    return render_template("register.html")


# ✅ HOME FEED (AFTER LOGIN)
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM posts ORDER BY id DESC")
        posts = c.fetchall()

    return render_template("home.html", username=username, posts=posts)


# ✅ ADD POST
@app.route("/add_post", methods=["POST"])
def add_post():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    caption = request.form["caption"]
    image = request.files["image"]

    image_filename = None
    if image:
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO posts (username, caption, image_filename) VALUES (?, ?, ?)",
                  (username, caption, image_filename))
        conn.commit()

    return redirect(url_for("home"))


# ✅ FEED ROUTE (GLOBAL FEED)
@app.route("/feed")
def feed():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("""
        SELECT posts.id, posts.username, posts.caption, posts.image_filename, posts.likes, posts.reposts,
               users.profile_pic
        FROM posts
        LEFT JOIN users ON posts.username = users.username
        ORDER BY posts.id DESC
        """)
        posts = c.fetchall()

        # Fetch all comments for all posts
        c.execute("""
        SELECT post_id, username, text, created_at FROM comments ORDER BY created_at ASC
        """)
        comments = c.fetchall()

    # Group comments by post_id
    comment_dict = {}
    for post_id, username, text, created_at in comments:
        if post_id not in comment_dict:
            comment_dict[post_id] = []
        comment_dict[post_id].append((username, text, created_at))

    return render_template("feed.html", posts=posts, comments=comment_dict)


# ✅ ADD COMMENT ROUTE
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    text = request.form["comment"]

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, username, text) VALUES (?, ?, ?)", (post_id, username, text))
        conn.commit()

    return redirect(url_for("feed"))


# ✅ LOGOUT
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


# ✅ RUN APP
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000, debug=False)  
