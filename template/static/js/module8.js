const scenarios = [
    { title: "The Monologue", desc: "A peer is explaining their complex hobby. Look 'Politely Interested'.", target: "Neutral" },
    { title: "The Critique", desc: "You just received unexpected feedback. Stay 'Unfazed'.", target: "Unfazed" },
    { title: "The Bad Joke", desc: "A teacher tells a joke that lands flat. Maintain a 'Steady Smile'.", target: "Steady Smile" },
    { title: "The Endless Meeting", desc: "A colleague is reading through an incredibly dry spreadsheet line by line. Keep it together.", target: "Neutral" },
    { title: "The Spilled Coffee", desc: "Someone accidentally knocks over a drink dangerously close to your laptop. Show no panic.", target: "Unfazed" },
    { title: "The Terrible Gift", desc: "You just unwrapped a present you absolutely hate while the giver watches. Look appreciative.", target: "Steady Smile" },
    { title: "The Elevator Ride", desc: "You are sharing a tiny elevator with your boss in complete silence. Stare at the doors calmly.", target: "Neutral" },
    { title: "The Wrong Name", desc: "An acquaintance confidently calls you by the wrong name for the third time. Let it slide.", target: "Unfazed" },
    { title: "The Family Photo", desc: "The photographer is taking forever to figure out the camera settings. Hold the pose.", target: "Steady Smile" },
    { title: "The Overheard Argument", desc: "Two strangers are bickering loudly on public transit. Look straight ahead, minding your business.", target: "Neutral" },
    { title: "The Sudden Noise", desc: "A heavy textbook is dropped right behind your chair. Don't jump or flinch.", target: "Unfazed" },
    { title: "The Over-Sharer", desc: "A distant relative is telling a very long, slightly uncomfortable story at dinner. Keep it polite.", target: "Steady Smile" },
    { title: "The Instruction Manual", desc: "You are listening to a flight attendant's safety briefing for the hundredth time. Pay calm attention.", target: "Neutral" },
    { title: "The Tech Glitch", desc: "Your presentation freezes right in the middle of a crucial slide. Stay cool while it loads.", target: "Unfazed" },
    { title: "The Awkward Silence", desc: "The conversation dies out completely at a networking event. Fill the gap with a pleasant look.", target: "Steady Smile" },
    { title: "The Waiting Room", desc: "Your appointment is running twenty minutes late. Sit calmly without checking your phone.", target: "Neutral" },
    { title: "The Accidental Reply-All", desc: "A coworker hits 'Reply All' with a mildly embarrassing message. Keep a poker face.", target: "Unfazed" },
    { title: "The Retail Shift", desc: "A customer is complaining to you about something completely out of your control. Nod pleasantly.", target: "Steady Smile" }
];

let currentScenarioIdx = 0;
let faceMesh;
let video, startBtn, nextBtn, timerBar, statusOverlay, statusText, videoWrapper, feedbackPanel, feedbackText;
let isChallenging = false;
let challengeStartTime = 0;
const CHALLENGE_DURATION = 3000; 
async function init() {
    // Assign DOM elements first
    video = document.getElementById("webcam");
    startBtn = document.getElementById("start-btn");
    nextBtn = document.getElementById("next-btn");
    timerBar = document.getElementById("timer-bar");
    statusOverlay = document.getElementById("status-overlay");
    statusText = document.getElementById("status-text");
    videoWrapper = document.getElementById("video-wrapper");
    feedbackPanel = document.getElementById("feedback-panel");
    feedbackText = document.getElementById("feedback-text");
    try {
        // Now safe to update UI as variables are assigned
        updateScenarioUI();
        // Poll for MediaPipe Global
        let mpFaceMesh = null;
        for (let i = 0; i < 100; i++) {
            if (window.FaceMesh) {
                mpFaceMesh = window.FaceMesh;
                break;
            }
            await new Promise(r => setTimeout(r, 100));
        }
        if (!mpFaceMesh) {
            if (statusText) statusText.innerText = "Error: Face Mesh library failed to load.";
            return;
        }
        faceMesh = new mpFaceMesh({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4.1633559619/${file}`
        });
        faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: true,
            minDetectionConfidence: 0.6,
            minTrackingConfidence: 0.6
        });
        faceMesh.onResults(onResults);
        setupWebcam();
        
        startBtn.addEventListener("click", startChallenge);
        nextBtn.addEventListener("click", () => {
            currentScenarioIdx = (currentScenarioIdx + 1) % scenarios.length;
            updateScenarioUI();
        });
    } catch (err) {
        console.error("Init Error:", err);
        if (statusText) statusText.innerText = "Engine Error. Refreshing might help.";
    }
}
function setupWebcam() {
    navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720, facingMode: "user" } })
        .then((stream) => {
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                statusOverlay.classList.add('hidden');
                startBtn.disabled = false;
                processVideo();
            };
        })
        .catch(err => {
            if (statusText) statusText.innerText = "Camera denied. Please enable access.";
        });
}
async function processVideo() {
    if (faceMesh && video.readyState >= 2) {
        await faceMesh.send({image: video});
    }
    requestAnimationFrame(processVideo);
}
function onResults(results) {
    if (!results.multiFaceLandmarks?.[0]) return;
    const landmarks = results.multiFaceLandmarks[0];
    const eyeWidth = Math.sqrt(Math.pow(landmarks[33].x - landmarks[133].x, 2)); 
    
    // Smile calculation
    const mouthWidth = Math.sqrt(Math.pow(landmarks[291].x - landmarks[61].x, 2) + Math.pow(landmarks[291].y - landmarks[61].y, 2));
    const smileScore = Math.max(0, (mouthWidth / eyeWidth - 1.65) * 1.5);
    // Brow calculation
    const avgDist = ((landmarks[159].y - landmarks[52].y) + (landmarks[386].y - landmarks[282].y)) / 2;
    const browScore = Math.max(0, (0.055 - avgDist) * 25);
    const smilePct = Math.min(100, Math.round(smileScore * 100));
    const browPct = Math.min(100, Math.round(browScore * 100));
    const sVal = document.getElementById('val-smile');
    const sBar = document.getElementById('bar-smile');
    const bVal = document.getElementById('val-brow');
    const bBar = document.getElementById('bar-brow');
    if (sVal) sVal.innerText = smilePct + "%";
    if (sBar) sBar.style.width = smilePct + "%";
    if (bVal) bVal.innerText = browPct + "%";
    if (bBar) bBar.style.width = browPct + "%";
    if (isChallenging) checkChallenge(smilePct, browPct);
}
function checkChallenge(smile, brow) {
    const scenario = scenarios[currentScenarioIdx];
    let violated = (scenario.target !== "Steady Smile") ? (smile > 30 || brow > 45) : (smile < 12 || brow > 50);
    if (violated) {
        isChallenging = false;
        videoWrapper.classList.add('failure-shake');
        startBtn.innerText = "Try Again";
        startBtn.classList.replace('bg-slate-700', 'bg-indigo-600');
        setTimeout(() => videoWrapper.classList.remove('failure-shake'), 500);
    } else {
        const elapsed = performance.now() - challengeStartTime;
        timerBar.style.width = Math.min(100, (elapsed / CHALLENGE_DURATION) * 100) + "%";
        if (elapsed >= CHALLENGE_DURATION) {
            isChallenging = false;
            startBtn.innerText = "Passed!";
            startBtn.classList.replace('bg-slate-700', 'bg-emerald-600');
            feedbackPanel.classList.remove('hidden');
            feedbackText.innerText = `Great job maintaining focus!`;
        }
    }
}
function startChallenge() {
    isChallenging = true;
    challengeStartTime = performance.now();
    feedbackPanel.classList.add('hidden');
    startBtn.innerText = "Focusing...";
    startBtn.classList.replace('bg-indigo-600', 'bg-slate-700');
}
function updateScenarioUI() {
    const s = scenarios[currentScenarioIdx];
    const title = document.getElementById('scenario-title');
    const desc = document.getElementById('scenario-desc');
    const target = document.getElementById('target-expression');
    
    if (title) title.innerText = s.title;
    if (desc) {
        // Use innerHTML because scenario desc might contain spans
        desc.innerHTML = s.desc.replace(s.target, `<span class="text-white font-bold">${s.target}</span>`);
    }
    if (target) target.innerText = s.target;
    
    if (startBtn) {
        startBtn.innerText = "Start Focus";
        startBtn.className = "bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 px-8 py-3 rounded-full font-bold transition-all shadow-lg active:scale-95";
    }
    if (feedbackPanel) feedbackPanel.classList.add('hidden');
    if (timerBar) timerBar.style.width = "0%";
}
window.addEventListener('load', init);