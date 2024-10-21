import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import openai
from werkzeug.utils import secure_filename
import tempfile

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///scratchpad.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Set up OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/save', methods=['POST'])
def save_drawing():
    data = request.json
    drawing = models.Drawing(data=data['image'])
    db.session.add(drawing)
    db.session.commit()
    return jsonify({"message": "Drawing saved successfully", "id": drawing.id})

@app.route('/load/<int:drawing_id>', methods=['GET'])
def load_drawing(drawing_id):
    drawing = models.Drawing.query.get_or_404(drawing_id)
    return jsonify({"image": drawing.data})

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
        # For text input, we'll just return the input as is
        converted_text = input_data

    return jsonify({"converted_text": converted_text})

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        try:
            analysis = analyze_image(temp_file_path)
            os.unlink(temp_file_path)  # Delete the temporary file
            return jsonify({"analysis": analysis})
        except Exception as e:
            os.unlink(temp_file_path)  # Delete the temporary file
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_image(image_path):
    with open(image_path, "rb") as image_file:
        response = openai.Image.create_analysis(
            image=image_file,
            model="gpt-4-vision-preview",
            max_tokens=300,
        )
    return response.choices[0].text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
