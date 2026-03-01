const scenarios =[
    { title: "The Monologue", desc: "A peer is explaining their complex hobby. Listen and maintain 'Politely Interested'.", target: "Neutral" },
    { title: "The Critique", desc: "You just received unexpected feedback. Listen and stay 'Unfazed'.", target: "Unfazed" },
    { title: "The Bad Joke", desc: "A teacher tells a joke that lands flat. Listen and maintain a 'Steady Smile'.", target: "Steady Smile" },
    { title: "The Endless Meeting", desc: "A colleague is reading through an incredibly dry spreadsheet line by line. Listen and keep it together.", target: "Neutral" },
    { title: "The Spilled Coffee", desc: "Someone accidentally knocks over a drink dangerously close to your laptop. Listen and show no panic.", target: "Unfazed" },
    { title: "The Terrible Gift", desc: "You just unwrapped a present you absolutely hate while the giver watches. Listen and look appreciative.", target: "Steady Smile" },
    { title: "The Elevator Ride", desc: "You are sharing a tiny elevator with your boss in complete silence. Listen and stare calmly.", target: "Neutral" },
    { title: "The Wrong Name", desc: "An acquaintance confidently calls you by the wrong name for the third time. Listen and let it slide.", target: "Unfazed" },
    { title: "The Family Photo", desc: "The photographer is taking forever to figure out the camera settings. Listen and hold the pose.", target: "Steady Smile" },
    { title: "The Overheard Argument", desc: "Two strangers are bickering loudly on public transit. Listen and look straight ahead.", target: "Neutral" },
    { title: "The Sudden Noise", desc: "A heavy textbook is dropped right behind your chair. Listen and don't jump or flinch.", target: "Unfazed" },
    { title: "The Over-Sharer", desc: "A distant relative is telling a very long, slightly uncomfortable story at dinner. Listen and keep it polite.", target: "Steady Smile" },
    { title: "The Instruction Manual", desc: "You are listening to a flight attendant's safety briefing for the hundredth time. Listen and pay calm attention.", target: "Neutral" },
    { title: "The Tech Glitch", desc: "Your presentation freezes right in the middle of a crucial slide. Listen and stay cool while it loads.", target: "Unfazed" },
    { title: "The Awkward Silence", desc: "The conversation dies out completely at a networking event. Listen and fill the gap with a pleasant look.", target: "Steady Smile" },
    { title: "The Waiting Room", desc: "Your appointment is running twenty minutes late. Listen and sit calmly without checking your phone.", target: "Neutral" },
    { title: "The Accidental Reply-All", desc: "A coworker hits 'Reply All' with a mildly embarrassing message. Listen and keep a poker face.", target: "Unfazed" },
    { title: "The Retail Shift", desc: "A customer is complaining to you about something completely out of your control. Listen and nod pleasantly.", target: "Steady Smile" }
];

let currentScenarioIdx = 0;
let faceApiDetector;
let video, startBtn, nextBtn, timerBar, statusOverlay, statusText, videoWrapper, feedbackPanel, feedbackText, scenarioAudio;
let isChallenging = false;
let challengeStartTime = 0;
let passCount = 0;
let modelReady = false;

// Performance tracking
let correctFrames = 0;
let totalFrames = 0;
let currentPerformanceScore = 0; // 0-100
let audioDuration = 0;
let audioStartTime = 0;
const COUNTDOWN_DURATION = 5000; // 5 seconds before audio starts 

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

function updateBorderColor(accuracy) {
    /**
     * Update the video wrapper border color based on accuracy score.
     * Dark green (80%+) → Yellow (60-80%) → Orange (40-60%) → Red (<40%)
     */
    let borderColor;
    
    if (accuracy >= 80) {
        // Dark green
        borderColor = 'rgb(34, 120, 71)'; // emerald-700
    } else if (accuracy >= 60) {
        // Light green
        borderColor = 'rgb(74, 222, 128)'; // lime-400
    } else if (accuracy >= 40) {
        // Yellow
        borderColor = 'rgb(234, 179, 8)'; // yellow-500
    } else if (accuracy >= 20) {
        // Orange
        borderColor = 'rgb(239, 105, 37)'; // orange-500
    } else {
        // Dark red
        borderColor = 'rgb(127, 29, 29)'; // red-900
    }
    
    videoWrapper.style.borderColor = borderColor;
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
    scenarioAudio = document.getElementById("scenario-audio");
    
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
    navigator.mediaDevices.getUserMedia({ video: { width: 1280/2, height: 720/2, facingMode: "user" } })
        .then((stream) => {
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                
                video.width = video.videoWidth;
                video.height = video.videoHeight;
                
                const options = {
                    withLandmarks: true,
                    withDescriptors: false,
                    withExpressions: true
                };
                
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
    if (statusText) statusText.innerText = "Ready. Click Start Challenge to begin.";
    
    detectFaces();
}

async function detectFaces() {
    if (!modelReady || !faceApiDetector) {
        requestAnimationFrame(detectFaces);
        return;
    }
    
    try {
        faceApiDetector.detect(onFaceDetected);
    } catch (err) {
        console.error("Detection error:", err);
        requestAnimationFrame(detectFaces);
    }
}

function onFaceDetected(err, results) {
    if (err) {
        console.error("Face detection error:", err);
        resetEmotionDisplay();
        requestAnimationFrame(detectFaces);
        return;
    }
    
    if (results && results.length > 0) {
        const prediction = results[0];
        const expressions = prediction.expressions || {}; 
        const emotion = emotionToLabel(expressions);
        updateEmotionDisplay(emotion, expressions);
        
        if (isChallenging) {
            trackChallengePerformance(emotion);
        }
    } else {
        resetEmotionDisplay();
    }
    
    requestAnimationFrame(detectFaces);
}

function trackChallengePerformance(emotion) {
    /**
     * Track performance throughout the audio playback.
     * Update border color in real-time based on accuracy.
     */
    const scenario = scenarios[currentScenarioIdx];
    const isCorrect = isCorrectExpression(emotion.label, scenario.target);
    
    totalFrames++;
    if (isCorrect) {
        correctFrames++;
    }
    
    // Calculate running accuracy
    currentPerformanceScore = Math.round((correctFrames / totalFrames) * 100);
    
    // Update border color based on current performance
    updateBorderColor(currentPerformanceScore);
    
    // Update timer bar to show audio progress
    if (audioStartTime > 0 && audioDuration > 0) {
        const elapsed = performance.now() - audioStartTime;
        const progress = Math.min(100, (elapsed / audioDuration) * 100);
        timerBar.style.width = progress + "%";
    }
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

async function loadAudio(scenarioIdx) {
    /**
     * Request audio from backend and load it into the audio element.
     */
    try {
        const response = await fetch(`/module8/audio/${scenarioIdx}`);
        const data = await response.json();
        
        if (data.error) {
            console.error("Audio generation error:", data.message);
            if (statusText) statusText.innerText = "Could not load audio. Try again.";
            startBtn.disabled = false;
            startBtn.innerText = "Start Challenge";
            return false;
        }
        
        scenarioAudio.src = data.url;
        return true;
    } catch (err) {
        console.error("Error loading audio:", err);
        if (statusText) statusText.innerText = "Could not load audio. Try again.";
        startBtn.disabled = false;
        startBtn.innerText = "Start Challenge";
        return false;
    }
}

function startChallenge() {
    startBtn.disabled = true;
    startBtn.innerText = "Loading...";
    feedbackPanel.classList.add('hidden');
    timerBar.style.width = "0%";
    
    // Load audio first
    loadAudio(currentScenarioIdx).then((success) => {
        if (!success) return;
        
        // Start countdown
        let countdownSeconds = COUNTDOWN_DURATION / 1000;
        if (statusText) statusText.innerText = `Starting in ${countdownSeconds} seconds...`;
        statusOverlay.classList.remove('hidden');
        
        const countdownInterval = setInterval(() => {
            countdownSeconds--;
            if (statusText) {
                statusText.innerText = countdownSeconds > 0 
                    ? `Starting in ${countdownSeconds} second${countdownSeconds > 1 ? 's' : ''}...`
                    : "Go!";
            }
        }, 1000);
        
        setTimeout(() => {
            clearInterval(countdownInterval);
            statusOverlay.classList.add('hidden');
            
            // Reset performance tracking
            correctFrames = 0;
            totalFrames = 0;
            currentPerformanceScore = 0;
            
            // Play audio and start challenge
            isChallenging = true;
            challengeStartTime = performance.now();
            audioStartTime = performance.now();
            scenarioAudio.play();
            
            startBtn.innerText = "Challenge Running...";
            
            // Handle audio end
            scenarioAudio.onended = onAudioEnded;
            
            // Get audio duration for progress bar (may not be immediately available)
            scenarioAudio.onloadedmetadata = () => {
                audioDuration = scenarioAudio.duration * 1000;
            };
        }, COUNTDOWN_DURATION);
    });
}

function onAudioEnded() {
    /**
     * Called when audio playback ends.
     * Calculate final score, show feedback, and submit XP.
     */
    isChallenging = false;
    startBtn.disabled = false;
    startBtn.innerText = "Start Challenge";
    timerBar.style.width = "100%";
    
    // Final performance score
    const finalScore = currentPerformanceScore;
    const scenario = scenarios[currentScenarioIdx];
    
    // Calculate XP based on accuracy (0-100 accuracy → 0-100 XP)
    const xpEarned = Math.round(finalScore);
    
    // Show feedback
    feedbackPanel.classList.remove('hidden');
    feedbackText.innerText = `You maintained a ${scenario.target} expression with ${finalScore}% accuracy throughout the challenge.`;
    document.getElementById('final-xp').innerText = xpEarned;
    
    // Update border to reflect final score
    updateBorderColor(finalScore);
    
    // Submit to backend
    submitResultToBackend(finalScore, xpEarned);
    
    passCount++;
}

async function submitResultToBackend(accuracyScore, xpEarned) {
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
                scenario: scenarios[currentScenarioIdx].title,
                accuracy_score: accuracyScore,
                xp: xpEarned
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
        console.error('Error submitting result:', err);
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
        startBtn.innerText = "Start Challenge";
        startBtn.className = "bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 px-8 py-3 rounded-full font-bold transition-all shadow-lg shadow-indigo-500/20 active:scale-95 flex items-center gap-3";
        startBtn.disabled = false;
    }
    if (feedbackPanel) feedbackPanel.classList.add('hidden');
    if (timerBar) timerBar.style.width = "0%";
    updateBorderColor(0); // Reset border to neutral
}

window.addEventListener('load', init);