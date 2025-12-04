from flask import Flask, render_template, request, jsonify
import openai
import base64 

app = Flask(__name__)

# 🔑 Your OpenAI API Key
openai.api_key = "YOUR_OPENAI_API_KEY"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/process_audio", methods=["POST"])
def process_audio():
    audio_file = request.files["audio"]

    # Convert audio to base64
    audio_bytes = audio_file.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # 🧠 Send audio to OpenAI Realtime Speech Model
    response = openai.chat.completions.create(
        model="gpt-4o-mini-tts",
        messages=[
            {"role": "user", "content": [
                {"type": "input_audio", "audio": audio_base64},
                {"type": "text", "text": "Convert the speech to text and answer it."}
            ]}
        ]
    )

    ai_reply = response.choices[0].message["content"][0]["text"]

    return jsonify({"reply": ai_reply})

if __name__ == "__main__":
    app.run(debug=True)
