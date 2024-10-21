import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import tempfile
import base64
from openai import OpenAI

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

# Initialize OpenAI client
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
    image_data = base64.b64decode(data['image'].split(',')[1])
    drawing = models.Drawing(data=data['image'], image_data=image_data)
    db.session.add(drawing)
    db.session.commit()
    return jsonify({"message": "Drawing saved successfully", "id": drawing.id})

@app.route('/load_image/<int:drawing_id>', methods=['GET'])
def load_image(drawing_id):
    drawing = models.Drawing.query.get_or_404(drawing_id)
    return jsonify({"image": drawing.data})

@app.route('/load_last_image', methods=['GET'])
def load_last_image():
    last_drawing = models.Drawing.query.order_by(models.Drawing.id.desc()).first()
    if last_drawing:
        return jsonify({"image": last_drawing.data, "id": last_drawing.id})
    else:
        return jsonify({"error": "No drawings found"}), 404

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
    data = request.json
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({"error": "No image data provided"}), 400

    # Remove the 'data:image/png;base64,' part
    image_data = image_data.split(',')[1]
    
    # Create a temporary file to store the decoded image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        temp_file.write(base64.b64decode(image_data))
        temp_file_path = temp_file.name

    try:
        analysis = analyze_image(temp_file_path)
        with open(temp_file_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        os.unlink(temp_file_path)  # Delete the temporary file
        return jsonify({"analysis": analysis, "image": encoded_image})
    except Exception as e:
        os.unlink(temp_file_path)  # Delete the temporary file
        return jsonify({"error": str(e)}), 500

def analyze_image(image_path):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # Getting the base64 string
    base64_image = encode_image(image_path)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
