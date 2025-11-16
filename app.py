from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/feed')
def feed():
    return render_template("feed.html")

@app.route('/profile')
def profile():
    return render_template("profile.html")

@app.route('/edit_profile')
def edit_profile():
    return render_template("edit_profile.html")

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/create_profile')
def create_profile():
    return render_template("create_profile.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
