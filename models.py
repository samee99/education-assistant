from app import db

class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=True)  # Optional: Original base64 data (can be removed if not needed)
    file_path = db.Column(db.String(120), nullable=False)  # Store the path to the image file instead of binary data

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
