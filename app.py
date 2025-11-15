from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# Example POST route (if you need form handling)
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    message = request.form.get("message")
    return f"Received: {name} - {message}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
