from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import os
from gtts import gTTS

app = Flask(__name__)
CORS(app)

# ----------------------------
# 🔥 ADD YOUR OPENAI API KEY HERE
# ----------------------------
openai.api_key = "YOUR_OPENAI_KEY_HERE"   # <--- paste your key inside quotes


# ----------------------------------------------------
# 🔊 ROUTE: Speech-to-Text → AI → Speech Output
# ----------------------------------------------------
@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        # Receive audio file
        audio_file = request.files["audio"]
        audio_path = "input_audio.wav"
        audio_file.save(audio_path)

        # ----------------------------
        # 1️⃣ Convert Speech → Text
        # ----------------------------
        print("Converting speech to text...")
        transcript = openai.audio.transcriptions.create(
            model="gpt-4o-mini-tts",
            file=open(audio_path, "rb")
        )

        user_text = transcript.text
        print("User said:", user_text)

        # ----------------------------
        # 2️⃣ Send Text → ChatGPT
        # ----------------------------
        print("Sending to ChatGPT...")
        ai_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Voice of Bharat. Speak short, clear answers."},
                {"role": "user", "content": user_text}
            ]
        )

        bot_text = ai_response.choices[0].message["content"]
        print("AI said:", bot_text)

        # ----------------------------
        # 3️⃣ Convert Text → Speech (Reply)
        # ----------------------------
        print("Converting AI reply to speech...")
        tts = gTTS(text=bot_text, lang="en")
        output_file = "reply.mp3"
        tts.save(output_file)

        # ----------------------------
        # 4️⃣ Return MP3 file to website
        # ----------------------------
        return send_file(output_file, mimetype="audio/mpeg")

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)})


@app.route("/")
def home():
    return "Voice of Bharat API running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
