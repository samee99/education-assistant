import os
import base64
import tempfile
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///scratchpad.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)
migrate = Migrate(app, db)

# Import models after initializing db and migrate
from models import Drawing, User

# Set the upload folder where images will be saved
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

# Modify this to save image in the file system
@app.route('/save_image', methods=['POST'])
def save_image():
    data = request.json
    image_data = base64.b64decode(data['image'].split(',')[1])

    # Create a unique file name and save the image to the file system
    file_name = f"{tempfile.mktemp(dir=UPLOAD_FOLDER, suffix='.png').split('/')[-1]}"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    # Save the image to the file system
    with open(file_path, 'wb') as f:
        f.write(image_data)

    # Save the file path in the database (instead of image binary data)
    drawing = Drawing(data=data['image'], file_path=file_name)
    db.session.add(drawing)
    db.session.commit()

    return jsonify({"message": "Drawing saved successfully", "id": drawing.id, "file_path": file_name})

# Load the image from the file system
@app.route('/load_image/<int:drawing_id>', methods=['GET'])
def load_image(drawing_id):
    drawing = Drawing.query.get_or_404(drawing_id)
    file_path = os.path.join(UPLOAD_FOLDER, drawing.file_path)

    # Read the image from the file system and return as base64-encoded string
    with open(file_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    return jsonify({"image": encoded_image})

# Serve the uploaded file directly from the file system
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/convert_handwriting', methods=['POST'])
def convert_handwriting():
    data = request.json
    mode = data.get('mode', 'draw')
    input_data = data.get('data', '')

    if mode == 'draw':
        # Here you would integrate with a handwriting recognition API
        # For now, we'll use a placeholder
        converted_text = "This is a placeholder for converted text from drawing."
    else:  # mode == 'write'
        converted_text = input_data

    return jsonify({"converted_text": converted_text})

def analyze_image(drawing_id):
    try:
        drawing = Drawing.query.get_or_404(drawing_id)
        file_path = os.path.join(UPLOAD_FOLDER, drawing.file_path)

        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Check the problem, step by step, and show me its been done correctly",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            },
                        },
                    ],
                }
            ],
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in analyze_image: {str(e)}")
        return f"Error analyzing image: {str(e)}"

@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.json
    drawing_id = data.get('drawing_id')

    if not drawing_id:
        return jsonify({"error": "No drawing ID provided"}), 400

    try:
        analysis = analyze_image(drawing_id)
        drawing = Drawing.query.get_or_404(drawing_id)

        # Return the analysis result and the base64-encoded image
        file_path = os.path.join(UPLOAD_FOLDER, drawing.file_path)
        with open(file_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        return jsonify({"analysis": analysis, "image": encoded_image})
    except Exception as e:
        print(f"Error in upload_image: {str(e)}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
