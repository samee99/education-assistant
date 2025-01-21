document.addEventListener('DOMContentLoaded', () => {
    const webcamElement = document.getElementById('webcam');
    const captureButton = document.getElementById('capture');
    const snapshotCanvas = document.getElementById('snapshotCanvas');
    const capturedImage = document.getElementById('capturedImage');
    const analyzedImageContainer = document.getElementById('analyzedImageContainer');
    const analyzedResult = document.getElementById('analyzedResult');
    const ctx = snapshotCanvas.getContext('2d');

    let mediaRecorder;
    let audioChunks = [];

    // Start webcam stream
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then(stream => {
                webcamElement.srcObject = stream;

                // Initialize MediaRecorder for audio
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
            })
            .catch(err => {
                alert("Webcam and microphone access are required.");
                console.error(err);
            });
    }

    // Capture the image and audio when the button is clicked
    captureButton.addEventListener('click', () => {
        // Start recording audio
        audioChunks = [];
        mediaRecorder.start();

        // Stop audio recording after a short delay (e.g., 3 seconds)
        setTimeout(() => {
            mediaRecorder.stop();

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });

                // Capture image from webcam
                snapshotCanvas.width = webcamElement.videoWidth;
                snapshotCanvas.height = webcamElement.videoHeight;
                ctx.drawImage(webcamElement, 0, 0, webcamElement.videoWidth, webcamElement.videoHeight);

                const imageData = snapshotCanvas.toDataURL('image/jpeg');
                capturedImage.src = imageData;

                // Prepare FormData to send both image and audio
                const formData = new FormData();
                formData.append('image', imageData);
                formData.append('audio', audioBlob, 'audio.mp3');

                // Send the image and audio to the backend for processing
                fetch('/process_webcam_image', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        throw new Error(data.error);
                    }

                    // Clear previous content and prepare to display new analysis
                    analyzedImageContainer.innerHTML = '';
                    analyzedResult.innerHTML = '';

                    // Display analyzed image (if available as base64)
                    if (data.image) {
                        const analyzedImage = document.createElement('img');
                        analyzedImage.src = `data:image/jpeg;base64,${data.image}`;
                        analyzedImage.style.maxWidth = '100%';
                        analyzedImageContainer.appendChild(analyzedImage);
                    }

                    // Display analysis text
                    const analysisText = document.createElement('p');
                    analysisText.innerHTML = data.analysis;
                    analyzedResult.appendChild(analysisText);

                    // Render LaTeX (MathJax) within the text
                    MathJax.typesetPromise([analyzedResult]).catch(err => console.error('MathJax rendering error:', err));

                    // Play the audio if the speech URL is provided
                    if (data.speech_url) {
                        const audio = new Audio(data.speech_url);
                        audio.play().catch(err => console.error('Audio playback error:', err));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error processing image and audio: ' + error.message);
                });
            };
        }, 3000); // Adjust delay as needed (e.g., 3000ms for 3 seconds of recording)
    });
});
