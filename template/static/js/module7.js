// module7.js - The Emotion Matrix Game Logic
// Manages multimodal emotion detection flashcards with visual + audio feedback

// --- Global State ---
let emotionDeck = [];
let currentCardIndex = 0;
let score = 0;
let correctCount = 0;
let totalAnswered = 0;
let isGameActive = false;
let sessionStartTime = 0;
let gameTimer = null;
let timeRemaining = 60;

// --- DOM Elements ---
const countdownOverlay = document.getElementById('countdown-overlay');
const countdownText = document.getElementById('countdown-text');
const flashcardContainer = document.getElementById('flashcard-container');
const choicesContainer = document.getElementById('choices-container');
const feedbackFlash = document.getElementById('feedback-flash');
const summaryScreen = document.getElementById('summary-screen');
const emotionImage = document.getElementById('emotion-image');
const emotionAudio = document.getElementById('emotion-audio');
const playAudioBtn = document.getElementById('play-audio-btn');
const transcriptHint = document.getElementById('transcript-hint');
const timerText = document.getElementById('timer-text');
const timerBar = document.getElementById('timer-bar');
const accuracyCounter = document.getElementById('accuracy-counter');
const cardCounter = document.getElementById('card-counter');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch the emotion matrix deck
        const response = await fetch('/static/data/emotion-matrix-deck.json');
        const data = await response.json();
        emotionDeck = data.cards;
        
        // Start the game with countdown
        startCountdown();
    } catch (error) {
        console.error('Error loading emotion matrix deck:', error);
        alert('Failed to load game data. Please refresh.');
    }
});

/**
 * 3-2-1 Countdown animation
 */
async function startCountdown() {
    countdownOverlay.classList.remove('hidden');
    
    for (let i = 3; i > 0; i--) {
        countdownText.textContent = i;
        countdownText.style.animation = 'none';
        // Trigger reflow to restart animation
        void countdownText.offsetWidth;
        countdownText.style.animation = 'pulse 1s ease-out';
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    countdownText.textContent = 'GO!';
    countdownText.style.color = '#34d399'; // Emerald
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    countdownOverlay.classList.add('hidden');
    initializeGame();
}

/**
 * Initialize the game after countdown
 */
function initializeGame() {
    isGameActive = true;
    sessionStartTime = Date.now();
    currentCardIndex = 0;
    score = 0;
    correctCount = 0;
    totalAnswered = 0;
    timeRemaining = 60;
    
    // Start the timer
    startGameTimer();
    
    // Load the first card
    loadCard(emotionDeck[currentCardIndex]);
}

/**
 * 60-second countdown timer
 */
function startGameTimer() {
    gameTimer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            endGame();
        }
    }, 1000);
}

/**
 * Update timer display and bar
 */
function updateTimerDisplay() {
    const seconds = Math.max(0, timeRemaining);
    timerText.textContent = `${seconds}s`;
    
    // Update timer bar width (60 second max)
    const percentageComplete = (60 - Math.max(0, timeRemaining)) / 60;
    timerBar.style.width = `${(1 - percentageComplete) * 100}%`;
    
    // Change color as time runs out
    if (timeRemaining <= 10) {
        timerBar.style.background = 'linear-gradient(to right, from-red-500 to-pink-400)';
    } else if (timeRemaining <= 30) {
        timerBar.style.background = 'linear-gradient(to right, from-yellow-500 to-orange-400)';
    }
}

/**
 * Load a flashcard from the deck
 */
function loadCard(card) {
    // Reset states
    flashcardContainer.classList.remove('hidden');
    choicesContainer.classList.remove('hidden');
    feedbackFlash.classList.add('hidden');
    
    // Set image
    emotionImage.src = card.imageSrc;
    emotionImage.alt = `Emotion: ${card.options[card.correctAnswerIndex]}`;
    
    // Set audio
    emotionAudio.src = card.audioSrc;
    
    // Set transcript hint
    transcriptHint.textContent = `"${card.transcriptHint}"`;
    
    // Update card counter
    cardCounter.innerHTML = `Card <span class="text-white">${currentCardIndex + 1}</span> of 10`;
    
    // Populate choice buttons
    const choiceButtons = document.querySelectorAll('.choice-btn');
    choiceButtons.forEach((btn, index) => {
        btn.querySelector('.choice-text').textContent = card.options[index];
        btn.dataset.index = index;
        btn.dataset.correct = (index === card.correctAnswerIndex);
        btn.classList.remove('border-emerald-500', 'border-red-500', 'cursor-not-allowed');
        btn.disabled = false;
        
        // Attach click handler
        btn.onclick = () => handleSelection(btn, card);
    });
    
    // Auto-play audio
    setTimeout(() => {
        emotionAudio.play().catch(e => console.log('Audio autoplay prevented:', e));
    }, 300);
    
    // Animate in
    flashcardContainer.style.opacity = '0';
    choicesContainer.style.opacity = '0';
    setTimeout(() => {
        flashcardContainer.style.opacity = '1';
        choicesContainer.style.opacity = '1';
    }, 100);
}

/**
 * Handle answer selection
 */
function handleSelection(buttonEl, card) {
    const selectedIndex = parseInt(buttonEl.dataset.index);
    const isCorrect = selectedIndex === card.correctAnswerIndex;
    
    // Increment total answered
    totalAnswered++;
    
    // Calculate XP
    let xpGain = 50; // Base XP for correct answer
    if (isCorrect) {
        correctCount++;
        buttonEl.classList.add('border-emerald-500', 'shadow-[0_0_20px_rgba(16,185,129,0.6)]');
        buttonEl.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
        
        // Bonus XP for speed (more time remaining = more bonus)
        const speedBonus = Math.floor((timeRemaining / 60) * 30);
        xpGain += speedBonus;
        
        score += xpGain;
    } else {
        xpGain = -10; // Penalty for incorrect
        buttonEl.classList.add('border-red-500', 'shadow-[0_0_20px_rgba(239,68,68,0.6)]');
        buttonEl.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
        
        // Show correct answer
        const choiceButtons = document.querySelectorAll('.choice-btn');
        choiceButtons[card.correctAnswerIndex].classList.add('border-emerald-500');
        choiceButtons[card.correctAnswerIndex].style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
        
        score = Math.max(0, score + xpGain);
    }
    
    // Disable all buttons
    document.querySelectorAll('.choice-btn').forEach(btn => btn.disabled = true);
    
    // Show feedback
    showFeedback(isCorrect, card.feedbackText, xpGain);
    
    // Update accuracy display
    const accuracy = Math.round((correctCount / totalAnswered) * 100);
    accuracyCounter.innerHTML = `Accuracy: <span class="text-white">${accuracy}%</span>`;
    
    // Move to next card after delay
    setTimeout(() => {
        currentCardIndex++;
        
        if (currentCardIndex >= emotionDeck.length || timeRemaining <= 0) {
            endGame();
        } else {
            loadCard(emotionDeck[currentCardIndex]);
        }
    }, 1500);
}

/**
 * Show feedback flash
 */
function showFeedback(isCorrect, feedbackText, xpChange) {
    const feedbackIcon = document.getElementById('feedback-icon');
    const feedbackLabel = document.getElementById('feedback-label');
    const feedbackDetail = document.getElementById('feedback-detail');
    
    if (isCorrect) {
        feedbackIcon.className = 'fa-solid fa-check text-emerald-400 text-lg';
        feedbackLabel.textContent = 'CORRECT!';
        feedbackLabel.style.color = '#34d399';
        feedbackFlash.classList.remove('border-red-500/50');
        feedbackFlash.classList.add('border-emerald-500/50');
    } else {
        feedbackIcon.className = 'fa-solid fa-times text-red-400 text-lg';
        feedbackLabel.textContent = 'INCORRECT';
        feedbackLabel.style.color = '#f87171';
        feedbackFlash.classList.remove('border-emerald-500/50');
        feedbackFlash.classList.add('border-red-500/50');
    }
    
    feedbackDetail.textContent = feedbackText;
    
    feedbackFlash.classList.remove('hidden');
    feedbackFlash.style.opacity = '0';
    setTimeout(() => {
        feedbackFlash.style.opacity = '1';
    }, 50);
}

/**
 * Play/Replay audio
 */
playAudioBtn.addEventListener('click', () => {
    emotionAudio.currentTime = 0;
    emotionAudio.play().catch(e => console.log('Audio playback error:', e));
});

/**
 * End the game and show summary
 */
async function endGame() {
    isGameActive = false;
    clearInterval(gameTimer);
    
    // Hide game elements
    flashcardContainer.classList.add('hidden');
    choicesContainer.classList.add('hidden');
    feedbackFlash.classList.add('hidden');
    
    // Calculate final stats
    const finalAccuracy = totalAnswered > 0 
        ? Math.round((correctCount / totalAnswered) * 100) 
        : 0;
    
    // Show summary
    showSummary(finalAccuracy);
    
    // Save to backend
    await saveGameResults(finalAccuracy);
}

/**
 * Show the summary screen
 */
function showSummary(accuracy) {
    const finalAccuracy = document.getElementById('final-accuracy');
    const finalXP = document.getElementById('final-xp');
    const cardsScored = document.getElementById('cards-scored');
    const summaryText = document.getElementById('summary-text');
    
    finalAccuracy.textContent = `${accuracy}%`;
    finalXP.textContent = `+${score}`;
    cardsScored.textContent = `${correctCount}/10`;
    
    // Generate summary based on performance
    let summaryMessage = '';
    if (accuracy === 100) {
        summaryMessage = '🌟 Perfect score! You have an exceptional ability to detect emotional subtext. You caught every conflict between visual and vocal cues.';
    } else if (accuracy >= 80) {
        summaryMessage = '✨ Excellent work! Your emotional perception is highly refined. You successfully identified most multimodal contradictions.';
    } else if (accuracy >= 60) {
        summaryMessage = '💡 Good job! You\'re developing strong skills at reading hidden emotions. Keep practicing to improve your detection accuracy.';
    } else if (accuracy >= 40) {
        summaryMessage = '🎯 You\'re getting there! Emotional subtext detection takes practice. Review your missed cards and try again.';
    } else {
        summaryMessage = '💪 Keep practicing! Multimodal emotion detection is a complex skill. The more you play, the better you\'ll become at spotting the conflicts.';
    }
    
    summaryText.textContent = summaryMessage;
    
    // Show summary screen
    summaryScreen.classList.remove('hidden');
    summaryScreen.style.opacity = '0';
    setTimeout(() => {
        summaryScreen.style.opacity = '1';
    }, 100);
}

/**
 * Save game results to MongoDB via backend
 */
async function saveGameResults(accuracy) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            console.log('No authentication token found. Results not saved.');
            return;
        }
        
        const response = await fetch('/api/module7/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                xp: score,
                accuracy: accuracy,
                correctCount: correctCount,
                totalAnswered: totalAnswered,
                timestamp: new Date().toISOString()
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            console.log('Game results saved. New XP total:', data.xp);
        } else {
            console.error('Failed to save results:', data.message);
        }
    } catch (error) {
        console.error('Error saving game results:', error);
    }
}

// Add some CSS interactivity with animations
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.1);
        }
        100% {
            transform: scale(1);
            opacity: 0;
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .choice-btn {
        animation: slideIn 0.4s ease-out backwards;
    }
    
    .choice-btn:nth-child(1) { animation-delay: 0s; }
    .choice-btn:nth-child(2) { animation-delay: 0.1s; }
    .choice-btn:nth-child(3) { animation-delay: 0.2s; }
    .choice-btn:nth-child(4) { animation-delay: 0.3s; }
`;
document.head.appendChild(style);
