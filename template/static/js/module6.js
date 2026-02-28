// module6.js handles the pitch exercise, xp display, and backend recording
// the reusable backend helpers are loaded via backend.js and attached to
// `window.backend`.

// we still keep a handful of local state variables but all communication
// with the server goes through window.backend.

// --- the rest of the script copied/adapted from the provided HTML sample ---

// --- State Variables ---
let isRecording = false;
let isRecognizing = false; // Add explicit tracker for Speech API state
let confidenceScore = 100;
let fillerCount = 0;
let hesitationCount = 0;
let fullTranscript = "";
let pitchTimer = null;
let timeRemaining = 0;
let pitchDuration = 0; // length of the pitch session (calculated from xp)
        
// --- DOM Elements ---
const micBtn = document.getElementById('mic-btn');
const micIcon = document.getElementById('mic-icon');
const micText = document.getElementById('mic-text');
const confidenceBar = document.getElementById('confidence-bar');
const confidenceText = document.getElementById('confidence-text');
const fillerCounter = document.getElementById('filler-counter');
const pauseCounter = document.getElementById('pause-counter');
const transcriptBox = document.getElementById('transcript-box');
const feedbackPanel = document.getElementById('feedback-panel');
const feedbackText = document.getElementById('feedback-text');
const timerDisplay = document.getElementById('timer-display');
const xpAwardSpan = document.getElementById('xp-award');

// --- APIs & Audio Context ---
let recognition = null;
let audioContext = null;
let mediaStreamSource = null;
let scriptProcessor = null;
let silenceTimer = null;
let isCurrentlySpeaking = false;

// Initialize Web Speech API
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();

    // Allows filler words to be picked up by the js and browser
    recognition.continuous = true;
    recognition.interimResults = true;

    // Track state closely to prevent race condition crashes
    recognition.onstart = () => {
        isRecognizing = true;
    };

    recognition.onend = () => {
        isRecognizing = false;
        // If the user started holding the button again while the engine was still asynchronously stopping, start it back up now.
        if (isRecording) {
            try { recognition.start(); } catch(e) {}
        }
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscriptChunk = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscriptChunk += event.results[i][0].transcript;
                fullTranscript += event.results[i][0].transcript + " ";
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        // Display transcript
        transcriptBox.innerHTML = fullTranscript + '<span class="text-slate-500">' + interimTranscript + '</span>';

        // Check for filler words in the final chunks
        if (finalTranscriptChunk) {
            checkFillerWords(finalTranscriptChunk);
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        isRecognizing = false;
    };
} else {
    console.warn("Web Speech API is not supported in this browser. Please use Chrome.");
}

// --- Core Logic ---

function checkFillerWords(text) {
    // Regex to find standalone filler words
    const fillerRegex = /\b(um|uh|like|you know|basically)\b/gi;
    const matches = text.match(fillerRegex);
    
    if (matches) {
        fillerCount += matches.length;
        fillerCounter.innerHTML = `Filler Words (Um/Uh): <span class="text-rose-400 font-bold">${fillerCount}</span>`;
        applyPenalty(5 * matches.length, fillerCounter); // -5% per filler word
    }
}

function applyPenalty(amount, elementToFlash) {
    confidenceScore = Math.max(0, confidenceScore - amount);
    
    // Update UI
    confidenceBar.style.width = `${confidenceScore}%`;
    confidenceText.innerText = `${confidenceScore}%`;
    
    // Color changing logic based on score
    if (confidenceScore < 50) {
        confidenceBar.className = "bg-gradient-to-r from-rose-500 to-orange-400 h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(225,29,72,0.5)]";
        confidenceText.className = "text-rose-400 font-bold";
    } else if (confidenceScore < 80) {
        confidenceBar.className = "bg-gradient-to-r from-yellow-500 to-orange-400 h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(234,179,8,0.5)]";
        confidenceText.className = "text-yellow-400 font-bold";
    }

    // Visual flash feedback
    elementToFlash.classList.remove('flash-penalty');
    void elementToFlash.offsetWidth; // trigger reflow
    elementToFlash.classList.add('flash-penalty');
    
    transcriptBox.classList.remove('flash-penalty');
    void transcriptBox.offsetWidth;
    transcriptBox.classList.add('flash-penalty');
}

// --- Custom Audio Context for Hesitation (Hark.js alternative) ---
async function setupAudioProcessing() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') {
        await audioContext.resume();
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        mediaStreamSource = audioContext.createMediaStreamSource(stream);
        
        // createScriptProcessor is deprecated but works universally without external workers for hackathons
        scriptProcessor = audioContext.createScriptProcessor(2048, 1, 1);
        
        mediaStreamSource.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        scriptProcessor.onaudioprocess = function(event) {
            if (!isRecording) return;
            
            const input = event.inputBuffer.getChannelData(0);
            let sum = 0;
            for (let i = 0; i < input.length; i++) {
                sum += input[i] * input[i];
            }
            const rms = Math.sqrt(sum / input.length);
            const volume = rms * 100;

            // Threshold for speaking
            if (volume > 1.5) {
                if (!isCurrentlySpeaking) {
                    isCurrentlySpeaking = true;
                    clearTimeout(silenceTimer); // User started talking, clear hesitation penalty
                }
            } else {
                if (isCurrentlySpeaking) {
                    isCurrentlySpeaking = false;
                    // User stopped talking, start hesitation timer
                    silenceTimer = setTimeout(() => {
                        if (isRecording) {
                            handleHesitation();
                        }
                    }, 1500); // 1.5 second pause allowed
                }
            }
        };
    } catch (err) {
        console.error("Microphone access denied", err);
    }
}

function handleHesitation() {
    hesitationCount++;
    pauseCounter.innerHTML = `Hesitations (>1.5s): <span class="text-rose-400 font-bold">${hesitationCount}</span>`;
    applyPenalty(10, pauseCounter); // -10% per long pause
    
    // Automatically restart timer in case they stay silent
    silenceTimer = setTimeout(() => {
        if (isRecording) handleHesitation();
    }, 1500);
}

// --- Interaction Handlers ---

async function startRecording() {
    try {
        if (isRecording) return; // Prevent multiple simultaneous triggers
        
        isRecording = true;
        fullTranscript = "";
        transcriptBox.classList.remove('hidden');
        transcriptBox.innerHTML = '<span class="text-slate-500 italic">Listening...</span>';
        feedbackPanel.classList.add('hidden');
        
        // Visuals
        micBtn.classList.add('recording-active');
        micBtn.classList.replace('border-slate-700', 'border-cyan-500');
        micIcon.classList.replace('text-slate-400', 'text-cyan-400');
        micText.innerText = "Listening...";
        micText.classList.replace('text-slate-400', 'text-cyan-400');

        // Calculate Timer based on XP (20s to 45s)
        const xpText = document.getElementById('user-xp').innerText.replace(/,/g, '');
        const xp = parseInt(xpText) || 0;
        // Formula: Base 20s + 1s per 100 XP, capped at 45s
        pitchDuration = Math.min(45, Math.max(20, 20 + Math.floor(xp / 100)));
        timeRemaining = pitchDuration;
        
        timerDisplay.innerText = `00:${timeRemaining.toString().padStart(2, '0')}`;
        timerDisplay.classList.remove('opacity-0');

        pitchTimer = setInterval(() => {
            timeRemaining--;
            if (timeRemaining <= 0) {
                stopRecording();
            } else {
                timerDisplay.innerText = `00:${timeRemaining.toString().padStart(2, '0')}`;
            }
        }, 1000);

        // Start APIs
        await setupAudioProcessing();
        
        if (recognition && !isRecognizing) {
            try {
                recognition.start();
            } catch (e) {
                console.warn("Speech recognition initialization blocked (Safe Mode).", e);
            }
        }
        
        // Start initial hesitation timer (if they click hold but don't speak immediately)
        silenceTimer = setTimeout(() => {
            if(isRecording && !isCurrentlySpeaking) handleHesitation();
        }, 2000);
    } catch (err) {
        console.error("Failed to start recording properly:", err);
    }
}

function stopRecording() {
    try {
        if (!isRecording) return;
        isRecording = false;
        
        // Stop Timer
        clearInterval(pitchTimer);
        timerDisplay.classList.add('opacity-0');

        // Visuals
        micBtn.classList.remove('recording-active');
        micBtn.classList.replace('border-cyan-500', 'border-slate-700');
        micIcon.classList.replace('text-cyan-400', 'text-slate-400');
        micText.innerText = "Tap to Start";
        micText.classList.replace('text-cyan-400', 'text-slate-400');

        // Stop APIs safely
        if (recognition && isRecognizing) {
            try {
                recognition.stop();
            } catch (e) {
                console.warn("Error stopping speech recognition gracefully.", e);
            }
        }
        clearTimeout(silenceTimer);
        if (mediaStreamSource) mediaStreamSource.disconnect();
        if (scriptProcessor) scriptProcessor.disconnect();

        analyzePitch();
    } catch(err) {
        console.error("Failed to stop recording properly:", err);
    }
}

// --- AI-Powered Evaluation ---
async function analyzePitch() {
    transcriptBox.innerHTML += '<br><br><span class="text-cyan-400 animate-pulse">Sending to Gemini AI for evaluation...</span>';
    
    // Get the current user token for authentication
    const token = localStorage.getItem('auth_token');
    if (!token) {
        feedbackText.innerText = "Error: Not authenticated. Please log in again.";
        feedbackPanel.classList.remove('hidden');
        return;
    }
    
    // Call AI evaluation endpoint
    try {
        const response = await fetch('/api/chat/evaluate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                module: 'module6',
                user_message: fullTranscript || "No audio detected",
                pitchDuration: pitchDuration,
                hesitationCount: hesitationCount,
                fillerCount: fillerCount
            })
        });

        const data = await response.json();
        
        // Hide loading indicator and show transcript
        transcriptBox.innerHTML = fullTranscript || "<span class=\"text-slate-500\">No audio detected.</span>";
        feedbackPanel.classList.remove('hidden');
        
        if (data.status === 'success') {
            // Display AI feedback
            feedbackText.innerText = data.feedback || "Great effort on your pitch!";
            
            // Update XP display and award
            const xpGain = data.xp || 0;
            xpAwardSpan.textContent = `+${xpGain}`;
            
            // The backend already updated XP, so we'll just display it
            if (xpGain > 0) {
                console.log(`Awarded ${xpGain} XP for module 6 completion`);
            }
        } else {
            feedbackText.innerText = data.message || "Unable to get feedback at this moment. Great effort!";
            xpAwardSpan.textContent = `+25`;
        }
    } catch (err) {
        console.error("Error calling AI evaluation:", err);
        feedbackText.innerText = "Great effort on your pitch! (Feedback service temporarily unavailable)";
        
        // Fallback XP award
        let xpGain = Math.round((confidenceScore / 100) * pitchDuration);
        xpGain = Math.max(25, xpGain);
        xpAwardSpan.textContent = `+${xpGain}`;
    }
}

// --- Event Listeners ---
// Toggle recording on click/tap
micBtn.addEventListener('click', (e) => {
    e.preventDefault();
    if (isRecording) {
        stopRecording(); // Allows user to end early
    } else {
        startRecording();
    }
});

// populate initial XP
backend.fetchMe();
