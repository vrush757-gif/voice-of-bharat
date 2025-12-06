from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    user_text = request.json.get('text')

    # Fake AI reply (you can connect real AI later)
    reply = f"You said: {user_text}"

    return jsonify({ "reply": reply })

if __name__ == '__main__':
    app.run()
