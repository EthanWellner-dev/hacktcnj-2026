function renderConfetti() {
    const canvasId = 'global-confetti-canvas';
    let canvas = document.getElementById(canvasId);
    // 1. Setup or reuse Canvas
    if (!canvas) {
        canvas = document.createElement('canvas');
        canvas.id = canvasId;
        Object.assign(canvas.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100vw',
            height: '100vh',
            pointerEvents: 'none',
            zIndex: '9999'
        });
        document.body.appendChild(canvas);
    }
    const ctx = canvas.getContext('2d');
    const particles = [];
    const particleCount = 150;
    const colors = ['#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', '#ff9800', '#ff5722'];
    // 2. Adjust for screen resolution
    function resize() {
        canvas.width = window.innerWidth * window.devicePixelRatio;
        canvas.height = window.innerHeight * window.devicePixelRatio;
        ctx.resetTransform(); // Clear previous scale
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    resize();
    window.addEventListener('resize', resize);
    // 3. Particle Logic
    class Particle {
        constructor() {
            this.x = Math.random() * window.innerWidth;
            this.y = Math.random() * window.innerHeight - window.innerHeight;
            this.size = (Math.random() * 8) + 4;
            this.color = colors[Math.floor(Math.random() * colors.length)];
            this.speed = (Math.random() * 3) + 2;
            this.angle = Math.random() * 360;
            this.spin = (Math.random() * 0.2) - 0.1;
            this.wind = (Math.random() * 2) - 1;
        }
        update() {
            this.y += this.speed;
            this.x += this.wind;
            this.angle += this.spin;
        }
        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.angle);
            ctx.fillStyle = this.color;
            ctx.fillRect(-this.size / 2, -this.size / 2, this.size, this.size / 2);
            ctx.restore();
        }
    }
    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    // 4. Animation Loop
    function animate() {
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
        
        let alive = false;
        particles.forEach(p => {
            p.update();
            p.draw();
            if (p.y < window.innerHeight + 20) {
                alive = true;
            }
        });
        if (alive) {
            requestAnimationFrame(animate);
        } else {
            window.removeEventListener('resize', resize);
            if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
        }
    }
    animate();
}