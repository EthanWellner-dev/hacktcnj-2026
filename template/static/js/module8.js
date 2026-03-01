const scenarios =[
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
let faceApiDetector;
let video, startBtn, nextBtn, timerBar, statusOverlay, statusText, videoWrapper, feedbackPanel, feedbackText;
let isChallenging = false;
let challengeStartTime = 0;
let passCount = 0;
const CHALLENGE_DURATION = 3000;
let modelReady = false; 

function emotionToLabel(emotionScores) {
    if (!emotionScores) return { label: "unknown", confidence: 0 };
    
    let maxEmotion = "neutral";
    let maxValue = emotionScores.neutral || 0;
    
    Object.entries(emotionScores).forEach(([emotion, value]) => {
        if (value > maxValue) {
            maxValue = value;
            maxEmotion = emotion;
        }
    });
    
    // Require minimum confidence to report (avoid noise)
    const MIN_CONFIDENCE = 0.2;
    if (maxValue < MIN_CONFIDENCE) {
        return { label: "Neutral", confidence: 0, detected: "indeterminate" };
    }
    
    // Map to our three target categories
    let label = "Neutral";
    let detected = maxEmotion;
    
    if (maxEmotion === "happy") {
        label = "Happy";
    } else if (maxEmotion === "angry" || maxEmotion === "fear" || maxEmotion === "disgusted") {
        label = "Unfazed";
    } else if (maxEmotion === "sad" || maxEmotion === "disgust") {
        label = "Concerned";
    } else if (maxEmotion === "surprised") {
        // Surprised can be either happy or neutral depending on context
        label = "Happy";
    }
    
    return { label, confidence: Math.round(maxValue * 100), detected };
}

function isCorrectExpression(detectedLabel, targetExpression) {
    if (targetExpression === "Neutral") {
        return detectedLabel === "Neutral";
    } else if (targetExpression === "Steady Smile") {
        return detectedLabel === "Happy";
    } else if (targetExpression === "Unfazed") {
        return detectedLabel === "Neutral" || detectedLabel === "Unfazed";
    }
    return false;
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
    
    try {
        updateScenarioUI();
        
        let attempts = 0;
        const maxAttempts = 100;
        while (!window.ml5 && attempts < maxAttempts) {
            await new Promise(r => setTimeout(r, 100));
            attempts++;
        }
        
        if (!window.ml5) {
            if (statusText) statusText.innerText = "Error: ml5.js failed to load. Please refresh.";
            return;
        }
        
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
                
                // FIX: Explicitly set the video dimensions to prevent resizeResults crash
                video.width = video.videoWidth;
                video.height = video.videoHeight;
                
                const options = {
                    withLandmarks: true,
                    withDescriptors: false,
                    withExpressions: true // FIX: Force emotion engine to activate
                };
                
                // FIX: Assign directly to global faceApiDetector 
                faceApiDetector = ml5.faceApi(video, options, modelLoadedCallback);
            };
        })
        .catch(err => {
            if (statusText) statusText.innerText = "Camera denied. Please enable access.";
            console.error("Camera error:", err);
        });
}

function modelLoadedCallback() {
    console.log("ml5.faceApi model loaded!");
    modelReady = true;
    statusOverlay.classList.add('hidden');
    startBtn.disabled = false;
    if (statusText) statusText.innerText = "Face detection ready. Center your face and click Start.";
    
    detectFaces();
}

async function detectFaces() {
    if (!modelReady || !faceApiDetector) {
        requestAnimationFrame(detectFaces);
        return;
    }
    
    try {
        // FIX: Directly call detect. Do not re-initialize the model.
        faceApiDetector.detect(onFaceDetected);
    } catch (err) {
        console.error("Detection error:", err);
        requestAnimationFrame(detectFaces);
    }
    // FIX: Removed trailing requestAnimationFrame from here. Now called in the callback.
}

function onFaceDetected(err, results) {
    if (err) {
        console.error("Face detection error:", err);
        resetEmotionDisplay();
        requestAnimationFrame(detectFaces); // Continue loop on error
        return;
    }
    
    if (results && results.length > 0) {
        const prediction = results[0];
        
        // FIX: Provide empty object fallback if undefined to prevent crashing
        const expressions = prediction.expressions || {}; 
        
        const emotion = emotionToLabel(expressions);
        updateEmotionDisplay(emotion, expressions);
        
        if (isChallenging) {
            checkChallenge(emotion);
        }
    } else {
        resetEmotionDisplay();
    }
    
    // FIX: Queue next frame ONLY after this frame completes its processing
    requestAnimationFrame(detectFaces);
}

function updateEmotionDisplay(emotion, allExpressions) {
    const emotionBarMap = {
        'angry': 'angry',
        'disgust': 'disgusted',
        'fear': 'fearful',
        'happy': 'happy',
        'neutral': 'neutral',
        'sad': 'sad',
        'surprised': 'surprised'
    };
    
    Object.entries(emotionBarMap).forEach(([ml5Emotion, barName]) => {
        const val = document.getElementById('val-' + barName);
        const bar = document.getElementById('bar-' + barName);
        const pct = Math.round((allExpressions[ml5Emotion] || 0) * 100);
        
        if (val) val.innerText = pct + "%";
        if (bar) bar.style.width = pct + "%";
    });
}

function resetEmotionDisplay() {
    const emotions =['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised'];
    emotions.forEach(e => {
        const val = document.getElementById('val-' + e);
        const bar = document.getElementById('bar-' + e);
        if (val) val.innerText = "0%";
        if (bar) bar.style.width = "0%";
    });
}

function checkChallenge(emotion) {
    const scenario = scenarios[currentScenarioIdx];
    const isCorrect = isCorrectExpression(emotion.label, scenario.target);
    const elapsed = performance.now() - challengeStartTime;
    
    if (elapsed > 30000) {
        isChallenging = false;
        videoWrapper.classList.add('failure-shake');
        startBtn.innerText = "Try Again";
        startBtn.classList.replace('bg-slate-700', 'bg-indigo-600');
        timerBar.style.width = "0%";
        feedbackPanel.classList.remove('hidden');
        feedbackText.innerText = `Challenge timed out. Make sure your face is visible and well-lit.`;
        setTimeout(() => videoWrapper.classList.remove('failure-shake'), 500);
        return;
    }
    
    if (!isCorrect) {
        if (emotion.confidence > 70) {
            isChallenging = false;
            videoWrapper.classList.add('failure-shake');
            startBtn.innerText = "Try Again";
            startBtn.classList.replace('bg-slate-700', 'bg-indigo-600');
            timerBar.style.width = "0%";
            feedbackPanel.classList.remove('hidden');
            feedbackText.innerText = `Expected ${scenario.target}, detected ${emotion.detected || emotion.label}. Try again!`;
            setTimeout(() => videoWrapper.classList.remove('failure-shake'), 500);
        } else {
            timerBar.style.width = "5%";
        }
    } else {
        timerBar.style.width = Math.min(100, (elapsed / CHALLENGE_DURATION) * 100) + "%";
        
        if (elapsed >= CHALLENGE_DURATION) {
            isChallenging = false;
            startBtn.innerText = "Passed!";
            startBtn.classList.replace('bg-slate-700', 'bg-emerald-600');
            feedbackPanel.classList.remove('hidden');
            feedbackText.innerText = `Excellent! You maintained a ${scenario.target} expression for 3 seconds.`;
            if (typeof renderConfetti === "function") renderConfetti();
            passCount++;
            submitPassToBackend(passCount);
        }
    }
}

function startChallenge() {
    isChallenging = true;
    challengeStartTime = performance.now();
    feedbackPanel.classList.add('hidden');
    startBtn.innerText = "Focusing...";
    startBtn.classList.replace('bg-indigo-600', 'bg-slate-700');
    timerBar.style.width = "0%";
}

async function submitPassToBackend(passNum) {
    try {
        const token = localStorage.getItem('ss_token') || localStorage.getItem('auth_token');
        if (!token) return;
        
        const response = await fetch('/module8/result', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                pass_number: passNum,
                scenario: scenarios[currentScenarioIdx].title,
                xp: 100
            })
        });
        
        const data = await response.json();
        if (data.xp_current !== undefined) {
            const xpDisplay = document.getElementById('user-xp');
            if (xpDisplay) {
                xpDisplay.textContent = data.xp_current.toLocaleString();
            }
        }
    } catch (err) {
        console.error('Error submitting pass:', err);
    }
}

function updateScenarioUI() {
    const s = scenarios[currentScenarioIdx];
    const title = document.getElementById('scenario-title');
    const desc = document.getElementById('scenario-desc');
    const target = document.getElementById('target-expression');
    
    if (title) title.innerText = s.title;
    if (desc) desc.innerHTML = s.desc.replace(s.target, `<span class="text-white font-bold">${s.target}</span>`);
    if (target) target.innerText = s.target;
    
    if (startBtn) {
        startBtn.innerText = "Start Focus";
        startBtn.className = "bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 px-8 py-3 rounded-full font-bold transition-all shadow-lg active:scale-95 flex items-center gap-3";
    }
    if (feedbackPanel) feedbackPanel.classList.add('hidden');
    if (timerBar) timerBar.style.width = "0%";
}

window.addEventListener('load', init);