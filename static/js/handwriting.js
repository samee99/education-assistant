document.addEventListener('DOMContentLoaded', () => {
    const scratchPad = document.getElementById('scratchPad');
    const drawCanvas = document.getElementById('handwritingPad');
    const ctx = drawCanvas.getContext('2d');
    const clearButton = document.getElementById('clear');
    const writeModeButton = document.getElementById('writeMode');
    const drawModeButton = document.getElementById('drawMode');
    const convertButton = document.getElementById('convert');
    const doneButton = document.getElementById('doneButton');
    const imageAnalysis = document.getElementById('imageAnalysis');
    const analyzedImageContainer = document.getElementById('analyzedImageContainer');

    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    let currentTool = 'pen';
    let currentColor = '#000000';
    let currentMode = 'draw'; // 'draw' or 'write'
    let drawingId = null; // Store drawing ID here

    // Initialize the canvas with a white background
    function initializeCanvas() {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, drawCanvas.width, drawCanvas.height);
    }

    // Set canvas size
    function resizeCanvas() {
        drawCanvas.width = drawCanvas.offsetWidth;
        drawCanvas.height = drawCanvas.offsetWidth * 0.75;
        initializeCanvas();
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
        } else {
            scratchPad.style.display = 'none';
            drawCanvas.style.display = 'block';
        }
    }

    // Tool selection
    document.getElementById('pen').addEventListener('click', () => setTool('pen'));
    document.getElementById('eraser').addEventListener('click', () => setTool('eraser'));
    document.getElementById('color-picker').addEventListener('input', (e) => setColor(e.target.value));
    clearButton.addEventListener('click', clearAll);
    doneButton.addEventListener('click', captureAndAnalyze);

    function setTool(tool) {
        currentTool = tool;
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

    drawCanvas.addEventListener('pointerdown', startDrawing);
    drawCanvas.addEventListener('pointermove', draw);
    drawCanvas.addEventListener('pointerup', stopDrawing);
    drawCanvas.addEventListener('pointerout', stopDrawing);

    function clearAll() {
        ctx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        initializeCanvas();
        scratchPad.value = '';
    }

    // Capture and analyze the drawing
    function captureAndAnalyze() {
        const emptyCanvas = drawCanvas.toDataURL('image/jpeg').length === 750;
        if (emptyCanvas) {
            alert("Please draw something before submitting.");
            return;
        }

        const imageData = drawCanvas.toDataURL('image/jpeg', 0.8);

        fetch('/save_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            drawingId = data.id;
            return fetch('/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ drawing_id: drawingId })
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            // Insert analysis and render LaTeX
            imageAnalysis.innerHTML = data.analysis;
            MathJax.typesetPromise([imageAnalysis]);

            // Display analyzed image
            const analyzedImage = document.createElement('img');
            analyzedImage.src = `data:image/jpeg;base64,${data.image}`;
            analyzedImage.style.maxWidth = '100%';
            analyzedImageContainer.innerHTML = '';
            analyzedImageContainer.appendChild(analyzedImage);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error analyzing image: ' + error.message);
        });
    }
});
