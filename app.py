import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

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

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
