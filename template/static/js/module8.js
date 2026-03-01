const scenarios = [
    {
        title: "The Monologue",
        desc: "A coworker is explaining their 400-slide vacation deck. You need to look 'Politely Interested' but not overly excited.",
        target: "Neutral",
        failMsg: "Your face dropped. You looked bored, which is a social death sentence."
    },
    {
        title: "The Passive Aggressive Remark",
        desc: "A peer just made a backhanded compliment. Maintain a 'Professional Composure' without scowling.",
        target: "Unfazed",
        failMsg: "Your brow furrowed! Keep it steady next time."
    },
    {
        title: "The Bad Joke",
        desc: "The CEO just told a joke that wasn't funny. Maintain a 'Mild, Supportive Smile' without bursting into fake laughter.",
        target: "Steady Smile",
        failMsg: "You lost the smile. Now it looks like you're judging them."
    }
];

let currentScenarioIdx = 0;
let faceLandmarker;
let video, startBtn, nextBtn, timerBar, statusOverlay, statusText, videoWrapper, feedbackPanel, feedbackText;
let isChallenging = false;
let challengeStartTime = 0;
const CHALLENGE_DURATION = 3000; 

function updateScenarioUI() {
    const s = scenarios[currentScenarioIdx];
    const title = document.getElementById('scenario-title');
    const desc = document.getElementById('scenario-desc');
    const target = document.getElementById('target-expression');
    
    if (title) title.innerText = s.title;
    if (desc) desc.innerHTML = s.desc;
    if (target) target.innerText = s.target;
    
    if (startBtn) {
        startBtn.innerHTML = `<i class="fa-solid fa-eye"></i> Start Focus`;
        startBtn.className = "bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 px-8 py-3 rounded-full font-bold transition-all flex items-center gap-3 shadow-lg shadow-indigo-500/20 active:scale-95";
        startBtn.disabled = !faceLandmarker;
    }
    if (feedbackPanel) feedbackPanel.classList.add('hidden');
    if (timerBar) timerBar.style.width = "0%";
}

async function init() {
    video = document.getElementById("webcam");
    startBtn = document.getElementById("start-btn");
    nextBtn = document.getElementById("next-btn");
    timerBar = document.getElementById("timer-bar");
    statusOverlay = document.getElementById("status-overlay");
    statusText = document.getElementById("status-text");
    videoWrapper = document.getElementById("video-wrapper");
    feedbackPanel = document.getElementById("feedback-panel");
    feedbackText = document.getElementById("feedback-text");

    if (!video || !startBtn || !nextBtn) return;

    try {
        updateScenarioUI();

        let visionLib = null;
        for (let i = 0; i < 50; i++) {
            if (window.vision && window.vision.FaceLandmarker) {
                visionLib = window.vision;
                break;
            }
            await new Promise(r => setTimeout(r, 200));
        }

        if (!visionLib) {
            throw new Error("MediaPipe libraries failed to load.");
        }

        // Create FaceLandmarker with options
        const filesetResolver = await visionLib.FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
        );
        
        faceLandmarker = await visionLib.FaceLandmarker.createFromOptions(filesetResolver, {
            baseOptions: {},
            numFaces: 1,
            runningMode: 'VIDEO',
            minFaceDetectionConfidence: 0.5,
            minFacePresenceConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        
        setupWebcam();
        
        startBtn.addEventListener("click", startChallenge);
        nextBtn.addEventListener("click", () => {
            currentScenarioIdx = (currentScenarioIdx + 1) % scenarios.length;
            updateScenarioUI();
        });
    } catch (err) {
        console.error("Initialization error:", err);
        if (statusText) {
            statusText.innerText = "Vision engine failure. Check camera permissions.";
        }
    }
}

function setupWebcam() {
    const constraints = { 
        video: { 
            width: { ideal: 640 }, 
            height: { ideal: 480 },
            facingMode: "user"
        } 
    };

    navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
        video.srcObject = stream;
        video.onloadedmetadata = () => {
            video.play();
            if(statusOverlay) {
                statusOverlay.style.opacity = "0";
                setTimeout(() => statusOverlay.classList.add('hidden'), 500);
            }
            startBtn.disabled = false;
            processVideo();
        };
    }).catch(err => {
        console.error("Webcam Error:", err);
        if (statusText) statusText.innerText = "Camera access required.";
    });
}

async function processVideo() {
    if (faceLandmarker && video.readyState >= 2) {
        const results = faceLandmarker.detectForVideo(video, Date.now());
        onResults(results);
    }
    requestAnimationFrame(processVideo);
}

function onResults(results) {
    if (!results.faceLandmarks || results.faceLandmarks.length === 0) return;
    
    const landmarks = results.faceLandmarks[0];
    
    // Reference: Eye width for scaling
    const eyeWidth = Math.sqrt(Math.pow(landmarks[33].x - landmarks[133].x, 2)); 
    
    // --- SMILE LOGIC ---
    const leftCorner = landmarks[61];
    const rightCorner = landmarks[291];
    const mouthWidth = Math.sqrt(Math.pow(rightCorner.x - leftCorner.x, 2) + Math.pow(rightCorner.y - leftCorner.y, 2));
    // Lowered multiplier from 2.5 to 1.5 and increased threshold to reduce sensitivity
    const smileScore = Math.max(0, (mouthWidth / eyeWidth - 1.65) * 1.5);

    // --- BROW LOGIC ---
    // Distance from eye to brow. 
    // landmarks[159] (top of left eye), landmarks[52] (left eyebrow)
    const leftDist = landmarks[159].y - landmarks[52].y;
    const rightDist = landmarks[386].y - landmarks[282].y;
    const avgDist = (leftDist + rightDist) / 2;
    
    // Neutral range is roughly 0.05 - 0.06. 
    // We want browScore to rise as avgDist gets SMALLER (furrowing)
    const neutralThreshold = 0.055; 
    const browScore = Math.max(0, (neutralThreshold - avgDist) * 25);

    const smilePct = Math.min(100, Math.round(smileScore * 100));
    const browPct = Math.min(100, Math.round(browScore * 100));

    const valSmile = document.getElementById('val-smile');
    const barSmile = document.getElementById('bar-smile');
    const valBrow = document.getElementById('val-brow');
    const barBrow = document.getElementById('bar-brow');

    if (valSmile) valSmile.innerText = smilePct + "%";
    if (barSmile) barSmile.style.width = smilePct + "%";
    if (valBrow) valBrow.innerText = browPct + "%";
    if (barBrow) barBrow.style.width = browPct + "%";

    if (isChallenging) {
        checkChallenge(smilePct, browPct);
    }
}

function checkChallenge(smile, brow) {
    const now = performance.now();
    let isViolated = false;
    
    const scenario = scenarios[currentScenarioIdx];
    if (scenario.target === "Neutral" || scenario.target === "Unfazed") {
        // Buffer to allow for natural micro-movements
        if (smile > 30 || brow > 45) isViolated = true;
    } else if (scenario.target === "Steady Smile") {
        if (smile < 10 || brow > 50) isViolated = true;
    }

    if (isViolated) {
        failChallenge();
    } else {
        const elapsed = now - challengeStartTime;
        const progress = (elapsed / CHALLENGE_DURATION) * 100;
        if (timerBar) timerBar.style.width = Math.min(100, progress) + "%";

        if (elapsed >= CHALLENGE_DURATION) {
            winChallenge();
        }
    }
}

function startChallenge() {
    if (isChallenging) return;
    isChallenging = true;
    challengeStartTime = performance.now();
    if (timerBar) timerBar.style.width = "0%";
    if (feedbackPanel) feedbackPanel.classList.add('hidden');
    startBtn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Monitoring...`;
    startBtn.classList.replace('bg-indigo-600', 'bg-slate-800');
    videoWrapper.classList.add('ring-4', 'ring-indigo-500/50');
}

function failChallenge() {
    isChallenging = false;
    if (timerBar) timerBar.style.width = "0%";
    videoWrapper.classList.remove('ring-4', 'ring-indigo-500/50');
    videoWrapper.classList.add('failure-shake', 'ring-4', 'ring-rose-500/50');
    
    startBtn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Try Again`;
    startBtn.classList.replace('bg-slate-800', 'bg-indigo-600');

    setTimeout(() => {
        videoWrapper.classList.remove('failure-shake', 'ring-4', 'ring-rose-500/50');
    }, 500);
}

function winChallenge() {
    isChallenging = false;
    videoWrapper.classList.remove('ring-4', 'ring-indigo-500/50');
    videoWrapper.classList.add('ring-4', 'ring-emerald-500/50');
    
    startBtn.innerHTML = `<i class="fa-solid fa-check"></i> Passed`;
    startBtn.classList.replace('bg-slate-800', 'bg-emerald-600');

    if (feedbackPanel) feedbackPanel.classList.remove('hidden');
    if (feedbackText) feedbackText.innerText = `Excellent. You maintained facial control during ${scenarios[currentScenarioIdx].title}.`;
    
    const xpEl = document.getElementById('user-xp');
    if (xpEl) {
        let currentXp = parseInt(xpEl.innerText.replace(',', ''));
        xpEl.innerText = (currentXp + 100).toLocaleString();
    }

    setTimeout(() => {
        videoWrapper.classList.remove('ring-4', 'ring-emerald-500/50');
    }, 2000);
}


window.addEventListener('load', init);