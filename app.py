import os
import base64
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from openai import OpenAI
from flask_migrate import Migrate


class Base(DeclarativeBase):
    pass


# Initialize the Flask app and SQLAlchemy
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL") or "sqlite:///scratchpad.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)
migrate = Migrate(app, db)

from models import Drawing, User

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert')
def convert():
    return render_template('convert.html')


@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json
    image_data = data['image'].split(',')[1]
    decoded_image_data = base64.b64decode(image_data)
    file_name = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    with open(file_path, 'wb') as f:
        f.write(decoded_image_data)

    drawing = Drawing(data=data['image'], file_path=file_name)
    db.session.add(drawing)
    db.session.commit()

    return jsonify({
        "message": "Drawing saved successfully",
        "id": drawing.id,
        "file_path": file_name
    })


@app.route('/load_image/<int:drawing_id>', methods=['GET'])
def load_image(drawing_id):
    drawing = Drawing.query.get_or_404(drawing_id)
    file_path = os.path.join(UPLOAD_FOLDER, drawing.file_path)
    with open(file_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    return jsonify({"image": encoded_image})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/convert_handwriting', methods=['POST'])
def convert_handwriting():
    data = request.json
    mode = data.get('mode', 'draw')
    input_data = data.get('data', '')
    converted_text = "This is a placeholder for converted text from drawing." if mode == 'draw' else input_data
    return jsonify({"converted_text": converted_text})


# Helper function to generate speech for a given text
def generate_speech(text):
    try:
        speech_file_path = os.path.join(UPLOAD_FOLDER,
                                        f"{uuid.uuid4().hex}.mp3")
        response = client.audio.speech.create(model="tts-1",
                                              voice="nova",
                                              input=text)
        response.stream_to_file(speech_file_path)
        return speech_file_path
    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        return None


# Helper function to transcribe user speech
def transcribe_audio(audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file)
        return transcription["text"]
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        return None


# Analyze image with optional mic input as context
def analyze_image_with_context(drawing_id, mic_text):
    try:
        drawing = Drawing.query.get_or_404(drawing_id)
        file_path = os.path.join(UPLOAD_FOLDER, drawing.file_path)
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = "Can you perform OCR on what's written and give hints to the user on how to solve the problem, but DO NOT SOLVE IT FOR THEM. Tell them if they are on the right track. Give only one instruction at a time. The instruction should be about the next step after what they have currently completed."

        # If there is mic transcription, add it as context to the prompt
        if mic_text:
            prompt += f"\n\nUser's speech context: {mic_text}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role":
                "user",
                "content": [{
                    "type": "text",
                    "text": prompt
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"
                    }
                }],
            }],
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in analyze_image_with_context: {str(e)}")
        return f"Error analyzing image: {str(e)}"


@app.route('/process_webcam_image', methods=['POST'])
def process_webcam_image():
    # Get image data from FormData
    image_data = request.form.get('image').split(',')[1]
    decoded_image_data = base64.b64decode(image_data)
    file_name = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    with open(file_path, 'wb') as f:
        f.write(decoded_image_data)

    # Save the image as a Drawing object in the database
    drawing = Drawing(data=request.form.get('image'), file_path=file_name)
    db.session.add(drawing)
    db.session.commit()

    # Save audio file
    audio_file = request.files.get('audio')
    mic_text = None
    if audio_file:
        audio_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.mp3")
        audio_file.save(audio_path)
        mic_text = transcribe_audio(audio_path)

    # Process image with optional context from the mic
    try:
        analysis_text = analyze_image_with_context(drawing.id, mic_text)
        speech_file_path = generate_speech(analysis_text)

        return jsonify({
            "analysis":
            analysis_text,
            "file_path":
            file_name,
            "speech_url":
            f"/uploads/{os.path.basename(speech_file_path)}"
            if speech_file_path else None
        })
    except Exception as e:
        print(f"Error processing webcam image: {e}")
        return jsonify({"error": f"Error processing webcam image: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
