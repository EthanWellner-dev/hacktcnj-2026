// module5.js - Tone Check (The De-Escalator)
// Handles conflict scenario with audio recording and AI evaluation

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recordingStartTime = null;
let recordingTimer = null;
let scenarioInitialized = false;
let currentScenarioText = '';

// DOM Elements
const warningScreen = document.getElementById('warning-screen');
const acceptBtn = document.getElementById('accept-btn');
const lockedState = document.getElementById('locked-state');
const moduleContent = document.getElementById('module-content');
const recordBtn = document.getElementById('record-btn');
const recordIcon = document.getElementById('record-icon');
const recordText = document.getElementById('record-text');
const timerDisplay = document.getElementById('timer-display');
const startScenarioBtn = document.getElementById('start-scenario-btn');
const bossAudio = document.getElementById('boss-audio');
const bossMessage = document.getElementById('boss-message');
const analysisPlaceholder = document.getElementById('analysis-placeholder');
const analysisResults = document.getElementById('analysis-results');
const responseAudioContainer = document.getElementById('response-audio-container');
const responseAudio = document.getElementById('response-audio');

// Initialize module
async function initModule() {
    try {
        // Accept button handler
        acceptBtn.addEventListener('click', async () => {
            warningScreen.classList.add('hidden');
            
            // Check user status
            const user = await backend.fetchMe();
            
            // Check XP gate
            if (user.xp < 5000) {
                // Show locked state
                lockedState.classList.remove('hidden');
                moduleContent.classList.add('hidden');
                document.getElementById('locked-xp').textContent = user.xp.toLocaleString();
                return;
            }
            
            // Show module content
            moduleContent.classList.remove('hidden');
            lockedState.classList.add('hidden');
            
            // Setup MediaRecorder
            setupMediaRecorder();
        });
        
    } catch (err) {
        console.error('Init error:', err);
    }
}

async function setupMediaRecorder() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            isRecording = false;
            recordBtn.classList.remove('recording-active');
            recordBtn.classList.replace('border-cyan-500', 'border-slate-700');
            recordIcon.classList.replace('text-cyan-400', 'text-slate-400');
            recordText.innerText = 'Hold & Speak';
            recordText.classList.replace('text-cyan-400', 'text-slate-400');
            
            clearInterval(recordingTimer);
            timerDisplay.classList.add('opacity-0');
            
            // Process the recording
            submitAudioResponse();
        };
        
        console.log('✓ MediaRecorder ready');
    } catch (err) {
        console.error('Microphone access denied:', err);
        recordBtn.disabled = true;
        recordText.innerText = 'Mic disabled';
    }
}

function startRecording() {
    if (!mediaRecorder) return;
    
    audioChunks = [];
    isRecording = true;
    recordingStartTime = Date.now();
    
    mediaRecorder.start();
    
    // Update UI
    recordBtn.classList.add('recording-active');
    recordBtn.classList.replace('border-slate-700', 'border-cyan-500');
    recordIcon.classList.replace('text-slate-400', 'text-cyan-400');
    recordText.innerText = 'Click to Stop';
    recordText.classList.replace('text-slate-400', 'text-cyan-400');
    
    // Timer
    let seconds = 0;
    timerDisplay.classList.remove('opacity-0');
    recordingTimer = setInterval(() => {
        seconds++;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        timerDisplay.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        // Auto-stop after 60 seconds
        if (seconds >= 60) {
            stopRecording();
        }
    }, 1000);
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        isRecording = false;
        mediaRecorder.stop();
        recordBtn.classList.remove('recording-active');
        recordBtn.classList.replace('border-cyan-500', 'border-slate-700');
        recordIcon.classList.replace('text-cyan-400', 'text-slate-400');
        recordText.innerText = 'Click to Record';
        recordText.classList.replace('text-cyan-400', 'text-slate-400');
        clearInterval(recordingTimer);
        timerDisplay.classList.add('opacity-0');
    }
}

async function startScenario() {
    if (scenarioInitialized) return;
    
    const token = localStorage.getItem('ss_token');
    if (!token) {
        console.error('Not authenticated');
        bossMessage.innerText = 'Error: Not authenticated';
        return;
    }
    
    startScenarioBtn.disabled = true;
    startScenarioBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Generating Scenario...';
    
    try {
        // Call backend to generate dynamic scenario with audio
        const response = await fetch('/api/module5/generate-scenario', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'locked') {
            console.error('Module locked:', data.message);
            return;
        }
        
        if (data.status === 'success') {
            // Store scenario text
            currentScenarioText = data.scenario_text;
            
            // Display scenario text
            bossMessage.innerText = currentScenarioText;
            
            // Play audio if available
            if (data.audio_url) {
                bossAudio.src = data.audio_url;
                bossAudio.classList.remove('hidden');
                bossAudio.style.display = 'block';
                document.getElementById('boss-waveform').classList.remove('hidden');
                
                // Auto-play
                try {
                    await bossAudio.play();
                } catch (e) {
                    console.warn('Auto-play blocked, user can click play:', e);
                }
            }
            
            scenarioInitialized = true;
            startScenarioBtn.innerHTML = '<i class="fa-solid fa-check mr-2"></i>Scenario Ready';
            startScenarioBtn.style.opacity = '0.5';
        } else {
            startScenarioBtn.innerHTML = '<i class="fa-solid fa-exclamation-circle mr-2"></i>Error';
            bossMessage.innerText = data.message || 'Failed to generate scenario';
        }
    } catch (err) {
        console.error('Error generating scenario:', err);
        startScenarioBtn.innerHTML = '<i class="fa-solid fa-exclamation-circle mr-2"></i>Error';
        bossMessage.innerText = `Error: ${err.message}`;
    }
}

async function submitAudioResponse() {
    const token = localStorage.getItem('ss_token');
    if (!token) {
        console.error('Not authenticated');
        return;
    }
    
    // Create blob from audio chunks
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    
    if (audioBlob.size === 0) {
        console.error('Empty audio blob');
        return;
    }
    
    // Show loading
    analysisPlaceholder.innerHTML = '<p class="text-cyan-400 animate-pulse">Analyzing your response...</p>';
    analysisResults.classList.add('hidden');
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'response.webm');
        formData.append('scenario', 'angry_boss');
        
        // Send to backend
        const response = await fetch('/api/module5/tone-check', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.status === 'locked') {
            console.error('Module locked:', data.message);
            return;
        }
        
        if (data.status === 'success') {
            displayAnalysis(data);
            
            // Play response audio if available
            if (data.audio_url) {
                responseAudio.src = data.audio_url;
                responseAudioContainer.classList.remove('hidden');
            }
        } else {
            analysisPlaceholder.innerHTML = `<p class="text-rose-400">${data.message || 'Analysis failed'}</p>`;
        }
    } catch (err) {
        console.error('Error submitting audio:', err);
        analysisPlaceholder.innerHTML = `<p class="text-rose-400">Error: ${err.message}</p>`;
    }
}

function displayAnalysis(data) {
    // Hide placeholder, show results
    analysisPlaceholder.classList.add('hidden');
    analysisResults.classList.remove('hidden');
    
    // Update metrics
    document.getElementById('score-display').textContent = `${data.score}%`;
    document.getElementById('tone-display').textContent = data.detected_tone || '--';
    document.getElementById('professionalism-display').textContent = `${data.professionalism}%`;
    document.getElementById('boundary-display').textContent = `${data.boundary_setting}%`;
    document.getElementById('composure-display').textContent = `${data.vocal_composure}%`;
    document.getElementById('feedback-display').textContent = data.feedback || '--';
    document.getElementById('xp-display').textContent = `+${data.xp_awarded || 0}`;
    
    // Update XP display in header
    if (document.getElementById('user-xp')) {
        document.getElementById('user-xp').textContent = data.xp_current || 0;
    }
    
    // Show resolution status
    if (data.is_resolved || data.is_escalating) {
        const resolutionStatus = document.getElementById('resolution-status');
        resolutionStatus.classList.remove('hidden');
        const resolutionText = document.getElementById('resolution-text');
        
        if (data.is_resolved) {
            resolutionText.innerHTML = '<i class="fa-solid fa-check-circle mr-2"></i>Conflict Resolved!';
            resolutionText.className = 'text-sm font-bold text-emerald-400';
            // Render confetti on successful resolution
            renderConfetti();
        } else if (data.is_escalating) {
            resolutionText.innerHTML = '<i class="fa-solid fa-exclamation-circle mr-2"></i>Situation Escalated';
            resolutionText.className = 'text-sm font-bold text-rose-400';
        }
    }
}

// Event Listeners
recordBtn.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

startScenarioBtn.addEventListener('click', startScenario);

// Audio Reset Handlers
const resetBossAudioBtn = document.getElementById('reset-boss-audio-btn');
const resetResponseAudioBtn = document.getElementById('reset-response-audio-btn');

if (resetBossAudioBtn) {
    resetBossAudioBtn.addEventListener('click', () => {
        bossAudio.currentTime = 0;
        bossAudio.play();
    });
    
    bossAudio.addEventListener('play', () => {
        resetBossAudioBtn.classList.add('hidden');
    });
    
    bossAudio.addEventListener('pause', () => {
        resetBossAudioBtn.classList.remove('hidden');
    });
    
    bossAudio.addEventListener('ended', () => {
        resetBossAudioBtn.classList.remove('hidden');
    });
}

if (resetResponseAudioBtn) {
    resetResponseAudioBtn.addEventListener('click', () => {
        responseAudio.currentTime = 0;
        responseAudio.play();
    });
    
    responseAudio.addEventListener('play', () => {
        resetResponseAudioBtn.classList.add('hidden');
    });
    
    responseAudio.addEventListener('pause', () => {
        resetResponseAudioBtn.classList.remove('hidden');
    });
    
    responseAudio.addEventListener('ended', () => {
        resetResponseAudioBtn.classList.remove('hidden');
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initModule);
