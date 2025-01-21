Scratch Pad
## Overview
The Apple Pencil Scratch Pad is an educational web application that allows users to draw and convert handwriting into text, specifically designed to assist with math problems on the fly. It includes features for webcam image capture and audio analysis, leveraging OpenAI for handwriting recognition and user interactions.
## Features
- **Handwriting Conversion**: Users can draw on a canvas, and it converts the handwriting into text, including mathematical expressions.
- **Webcam Capture**: Users can capture images and audio from their webcam.
- **Audio Transcription**: Recorded audio can be transcribed for analysis.
- **Math Problem Assistance**: The application helps with solving and analyzing math problems in real-time.
- **Database Support**: Uses Flask-SQLAlchemy to save drawings and user information.
## Technologies
- Flask
- Flask-SQLAlchemy
- OpenAI API
- HTML/CSS/JavaScript
- Bootstrap for styling
## Installation
1. Clone the repository or download the files.
2. Make sure you have the required environment variables set:
   - `FLASK_SECRET_KEY`: A secret key for your Flask app.
   - `DATABASE_URL`: The URL for your database (for example, SQLite).
   - `OPENAI_API_KEY`: Your OpenAI API key.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
Running the Application
To start the application, run:

python main.py
The app will be available at http://0.0.0.0:5000 on your Replit environment.

Usage
Navigate to the homepage.
Use the Scratch Pad to draw or write using the Apple Pencil (or mouse).
Click "Convert to Text" to see the handwriting converted into text, including solving math problems.
Use the Webcam Capture section for image and audio analysis.
Contributing
Contributions are welcome! Feel free to submit a pull request with your suggestions or improvements.

License
This project is licensed under the MIT License - see the LICENSE file for details.