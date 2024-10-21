document.addEventListener('DOMContentLoaded', () => {
    const scratchPad = document.getElementById('scratchPad');
    const drawCanvas = document.getElementById('handwritingPad');
    const ctx = drawCanvas.getContext('2d');
    const clearButton = document.getElementById('clear');
    const writeModeButton = document.getElementById('writeMode');
    const drawModeButton = document.getElementById('drawMode');
    const breathingStartButton = document.getElementById('breathingStart');
    const convertButton = document.getElementById('convert');
    const colorPicker = document.getElementById('color-picker');
    const doneButton = document.getElementById('doneButton');
    const imageAnalysis = document.getElementById('imageAnalysis');
    const analyzedImageContainer = document.getElementById('analyzedImageContainer');

    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    let currentTool = 'pen';
    let currentColor = '#000000';
    let currentMode = 'draw'; // 'draw' or 'write'

    // Set canvas size
    function resizeCanvas() {
        drawCanvas.width = drawCanvas.offsetWidth;
        drawCanvas.height = drawCanvas.offsetWidth * 0.75; // 4:3 aspect ratio
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Mode switching
    writeModeButton.addEventListener('click', () => setMode('write'));
    drawModeButton.addEventListener('click', () => setMode('draw'));

    function setMode(mode) {
        currentMode = mode;
        if (mode === 'write') {
            scratchPad.style.display = 'block';
            drawCanvas.style.display = 'none';
            writeModeButton.classList.add('active');
            drawModeButton.classList.remove('active');
        } else {
            scratchPad.style.display = 'none';
            drawCanvas.style.display = 'block';
            writeModeButton.classList.remove('active');
            drawModeButton.classList.add('active');
        }
    }

    // Tool selection
    document.getElementById('pen').addEventListener('click', () => setTool('pen'));
    document.getElementById('eraser').addEventListener('click', () => setTool('eraser'));
    colorPicker.addEventListener('input', (e) => setColor(e.target.value));
    clearButton.addEventListener('click', clearAll);
    convertButton.addEventListener('click', convertHandwriting);
    breathingStartButton.addEventListener('click', startBreathingExercise);
    doneButton.addEventListener('click', captureAndAnalyze);

    function setTool(tool) {
        currentTool = tool;
        document.querySelectorAll('.btn-group .btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById(tool).classList.add('active');
    }

    function setColor(color) {
        currentColor = color;
    }

    // Drawing functions
    function startDrawing(e) {
        isDrawing = true;
        [lastX, lastY] = [e.offsetX, e.offsetY];
    }

    function draw(e) {
        if (!isDrawing) return;
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(e.offsetX, e.offsetY);
        ctx.strokeStyle = currentTool === 'eraser' ? '#ffffff' : currentColor;
        ctx.lineWidth = currentTool === 'eraser' ? 20 : 2;
        ctx.lineCap = 'round';
        ctx.stroke();
        [lastX, lastY] = [e.offsetX, e.offsetY];
    }

    function stopDrawing() {
        isDrawing = false;
    }

    // Event listeners for pointer events
    drawCanvas.addEventListener('pointerdown', startDrawing);
    drawCanvas.addEventListener('pointermove', draw);
    drawCanvas.addEventListener('pointerup', stopDrawing);
    drawCanvas.addEventListener('pointerout', stopDrawing);

    // Clear all
    function clearAll() {
        ctx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        scratchPad.value = '';
    }

    // Convert handwriting
    function convertHandwriting() {
        let dataToConvert;
        if (currentMode === 'draw') {
            dataToConvert = drawCanvas.toDataURL('image/png');
        } else {
            dataToConvert = scratchPad.value;
        }

        fetch('/convert_handwriting', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data: dataToConvert, mode: currentMode }),
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('convertedText').value = data.converted_text;
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Error converting handwriting');
        });
    }

    // Breathing exercise
    function startBreathingExercise() {
        let count = 0;
        const totalBreaths = 3;
        const breathDuration = 4000; // 4 seconds for each inhale/exhale

        function breathe(action) {
            breathingStartButton.textContent = action;
            setTimeout(() => {
                count++;
                if (count < totalBreaths * 2) {
                    breathe(action === 'Inhale' ? 'Exhale' : 'Inhale');
                } else {
                    breathingStartButton.textContent = 'Start Breathing Exercise';
                    alert('Breathing exercise complete!');
                }
            }, breathDuration);
        }

        breathe('Inhale');
    }

    // Capture and analyze
    function captureAndAnalyze() {
        const imageData = drawCanvas.toDataURL('image/png');

        saveImageToBackend(imageData)
            .then(drawingId => {
                return fetch('/upload', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ drawing_id: drawingId }),
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                imageAnalysis.value = data.analysis;

                // Display the analyzed image
                const analyzedImage = document.createElement('img');
                analyzedImage.src = `data:image/png;base64,${data.image}`;
                analyzedImage.style.maxWidth = '100%';
                analyzedImageContainer.innerHTML = '';
                analyzedImageContainer.appendChild(analyzedImage);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error analyzing image: ' + error.message);
            });
    }

    // Save image to backend
    function saveImageToBackend(imageData) {
        return fetch('/save_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Image saved successfully. ID:', data.id);
            return data.id;
        })
        .catch(error => {
            console.error('Error saving image:', error);
            throw error;
        });
    }

    // Set initial mode
    setMode('draw');
});
