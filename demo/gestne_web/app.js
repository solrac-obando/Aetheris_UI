const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let pyodide = null;
let engine = null;
let mouse = { x: -1, y: -1, mode: 'attract' };
let fpsFrames = 0, fpsTime = performance.now();

// Resize handling
function resize() {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.parentElement.clientWidth * dpr;
    canvas.height = canvas.parentElement.clientHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (engine) {
        engine.set_canvas_size(canvas.width/dpr, canvas.height/dpr);
    }
}
window.addEventListener('resize', resize);
resize();

// Input handling
canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
});
canvas.addEventListener('mouseleave', () => { mouse.x = -1; });

function setMode(m) {
    mouse.mode = m;
    document.querySelectorAll('.ctrl-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + m).classList.add('active');
}

async function init() {
    try {
        pyodide = await loadPyodide();
        await pyodide.loadPackage('numpy');
        
        // Load data and logic
        const [dataResp, codeResp] = await Promise.all([
            fetch('data.json'),
            fetch('gestne_wasm.py')
        ]);
        
        const jsonData = await dataResp.text();
        const pyCode = await codeResp.text();
        
        await pyodide.runPythonAsync(pyCode);
        
        // Initialize engine
        const initFn = pyodide.globals.get('init_engine');
        initFn(jsonData);
        
        engine = pyodide.globals.get('EngineInstance');
        engine.set_canvas_size(window.innerWidth - 360, window.innerHeight - 150);

        // Update counts
        const raw = JSON.parse(jsonData);
        document.getElementById('val-metabolic').textContent = raw.filter(d => d.Cluster_Cuantitativo === 1).length;
        document.getElementById('val-reproductive').textContent = raw.filter(d => d.Cluster_Cuantitativo === 2).length;

        // Hide loader
        document.getElementById('loader').classList.add('hidden');
        
        requestAnimationFrame(loop);
    } catch (err) {
        console.error('Fallo al iniciar WASM:', err);
    }
}

function loop() {
    const w = canvas.width / (window.devicePixelRatio || 1);
    const h = canvas.height / (window.devicePixelRatio || 1);
    
    ctx.clearRect(0, 0, w, h);
    
    // Draw centroids (subtle glow)
    drawCentroid(w * 0.3, h * 0.5, '#ff6b4a');
    drawCentroid(w * 0.7, h * 0.5, '#4ac2ff');

    if (engine) {
        const buffer = engine.tick(mouse.x, mouse.y, mouse.mode);
        const data = buffer.toJs();
        const n = data.length / 5;
        
        for (let i = 0; i < n; i++) {
            const x = data[i * 5];
            const y = data[i * 5 + 1];
            const r = data[i * 5 + 2];
            const cluster = data[i * 5 + 3];
            const speed = data[i * 5 + 4];
            
            drawPatient(x, y, r, cluster, speed);
        }
    }

    // FPS Counter
    fpsFrames++;
    const now = performance.now();
    if (now - fpsTime >= 1000) {
        document.getElementById('stat-fps').textContent = fpsFrames;
        fpsFrames = 0;
        fpsTime = now;
    }

    requestAnimationFrame(loop);
}

function drawCentroid(x, y, color) {
    const grad = ctx.createRadialGradient(x, y, 0, x, y, 150);
    grad.addColorStop(0, color + '11');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, 150, 0, Math.PI * 2);
    ctx.fill();
}

function drawPatient(x, y, r, cluster, speed) {
    const color = cluster === 1 ? '#ff6b4a' : '#4ac2ff';
    
    // Outer Glow
    ctx.shadowBlur = 10 + speed;
    ctx.shadowColor = color;
    
    ctx.fillStyle = color + 'dd';
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    
    // Inner center
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#ffffffaa';
    ctx.beginPath();
    ctx.arc(x, y, r * 0.4, 0, Math.PI * 2);
    ctx.fill();
}

init();
