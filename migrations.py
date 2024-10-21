from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scratchpad.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(120), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        migrate.init_app(app, db)
        migrate.upgrade()

    print("Migration complete. The 'file_path' column has been added to the 'drawing' table.")
