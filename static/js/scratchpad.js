document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('scratchpad');
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    let currentTool = 'pen';
    let currentColor = '#000000';

    // Set canvas size
    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetWidth * 0.75; // 4:3 aspect ratio
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Tool selection
    document.getElementById('pen').addEventListener('click', () => setTool('pen'));
    document.getElementById('eraser').addEventListener('click', () => setTool('eraser'));
    document.getElementById('color-picker').addEventListener('input', (e) => setColor(e.target.value));
    document.getElementById('clear').addEventListener('click', clearCanvas);
    document.getElementById('save').addEventListener('click', saveDrawing);
    document.getElementById('load').addEventListener('click', loadDrawing);

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

    // Event listeners for mouse and touch
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    canvas.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    canvas.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    canvas.addEventListener('touchend', (e) => {
        const mouseEvent = new MouseEvent('mouseup', {});
        canvas.dispatchEvent(mouseEvent);
    });

    // Clear canvas
    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    // Save drawing
    function saveDrawing() {
        const imageData = canvas.toDataURL('image/png');
        fetch('/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData }),
        })
        .then(response => response.json())
        .then(data => {
            alert(`Drawing saved successfully. ID: ${data.id}`);
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Error saving drawing');
        });
    }

    // Load drawing
    function loadDrawing() {
        const drawingId = document.getElementById('load-id').value;
        if (!drawingId) {
            alert('Please enter a drawing ID');
            return;
        }

        fetch(`/load/${drawingId}`)
        .then(response => response.json())
        .then(data => {
            const img = new Image();
            img.onload = function() {
                clearCanvas();
                ctx.drawImage(img, 0, 0);
            }
            img.src = data.image;
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Error loading drawing');
        });
    }
});
