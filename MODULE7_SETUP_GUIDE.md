# Module 7: The Emotion Matrix – Setup & Asset Guide

## ✅ What's Been Built

### Backend
- **`backend/module7.py`** – Flask blueprint with `/api/module7/complete` endpoint
- **Route integration** – Added `/module7` view route to `views.py`
- **App registration** – Module 7 blueprint registered in `app.py`

### Frontend
- **`template/module7.html`** – Complete HTML template with:
  - 3-2-1 countdown overlay
  - Flashcard display (image + audio player)
  - 4 multiple-choice buttons
  - Real-time accuracy tracker
  - 60-second timer with visual bar
  - Summary screen with stats
  - Neon green/red feedback animations

- **`template/static/js/module7.js`** – Full game logic including:
  - Countdown animation
  - Card deck loading from JSON
  - Audio playback with manual replay button
  - Answer selection handling
  - Visual feedback (green = correct, red = incorrect)
  - XP scoring with speed bonuses
  - 60-second timer management
  - Summary screen generation
  - Backend result saving

### Data
- **`template/static/data/emotion-matrix-deck.json`** – Configuration file with:
  - 10 card definitions (id, image path, audio path, options, correct answer, feedback)
  - Game configuration (XP values, timing, etc.)

### Directory Structure
```
template/
├── module7.html (NEW)
└── static/
    ├── js/
    │   └── module7.js (NEW)
    ├── data/
    │   └── emotion-matrix-deck.json (NEW)
    ├── images/
    │   └── faces/ (NEW - empty, awaiting images)
    └── audio/
        └── elevenlabs/ (NEW - empty, awaiting audio files)
```

---

## 🎯 Next Steps: Adding Assets

### Step 1: Generate ElevenLabs Audio (10-15 clips)

**Access the ElevenLabs Dashboard:**
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Create/login to your account
3. Navigate to "Text to Speech" tool

**For each emotion card, generate audio using these prompts & settings:**

| Card | Emotion | Prompt | Settings | Save As |
|------|---------|--------|----------|---------|
| 001 | Passive-Aggressive | "(Sighs) Wow, that's so great for you." | Stability: 0.3, Similarity: 0.75 | `001_passive_aggressive.mp3` |
| 002 | Anxious/Panicked | "(High pitch, quick) No no, everything is totally fine!" | Stability: 0.2, Similarity: 0.8 | `002_anxious.mp3` |
| 003 | Sarcasm/Bored | "(Flat, lifeless tone) I'm absolutely thrilled." | Stability: 0.5, Similarity: 0.7 | `003_sarcasm.mp3` |
| 004 | Confused | "(Hesitant) Wait, what did you just say?" | Stability: 0.4, Similarity: 0.75 | `004_confused.mp3` |
| 005 | Angry/Frustrated | "(Strained jaw) That's... just great. Really." | Stability: 0.25, Similarity: 0.8 | `005_angry.mp3` |
| 006 | Sad/Resigned | "(Quiet, defeated) Yeah, I guess that's fine..." | Stability: 0.6, Similarity: 0.7 | `006_sad.mp3` |
| 007 | Surprised | "(High pitch) Oh! I didn't expect that at all!" | Stability: 0.3, Similarity: 0.8 | `007_surprised.mp3` |
| 008 | Skeptical | "(Slow, doubtful) Sure, that makes total sense." | Stability: 0.4, Similarity: 0.75 | `008_skeptical.mp3` |
| 009 | Stressed/Strained | "(Controlled) I'm fine. Everything is fine." | Stability: 0.35, Similarity: 0.8 | `009_strained.mp3` |
| 010 | Genuinely Happy | "(Warm, natural) That's wonderful news!" | Stability: 0.7, Similarity: 0.8 | `010_genuinely_happy.mp3` |

**Download and save to:** `template/static/audio/elevenlabs/`

### Step 2: Find & Add Facial Expression Images

**Source options (royalty-free):**
- [Unsplash](https://unsplash.com) – Search "facial expressions"
- [Pexels](https://pexels.com) – Search "emotion faces"
- [Pixabay](https://pixabay.com) – Search "expression"

**Download images that match these descriptions:**

| Card | Expression | Description | Save As |
|------|-----------|-------------|---------|
| 001 | Passive-Aggressive | Smile with narrowed/squinted eyes | `smile_narrow_eyes.jpg` |
| 002 | Anxious | Wide eyes, looking away or sideways | `wide_eyes_looking_away.jpg` |
| 003 | Sarcasm/Bored | Flat face, neutral mouth, dead eyes | `flat_expression.jpg` |
| 004 | Confused | Furrowed brow, slightly open mouth | `furrowed_brow_open_mouth.jpg` |
| 005 | Angry/Frustrated | Tight lips, clenched jaw, eye tension | `tight_lips_clenched_jaw.jpg` |
| 006 | Sad/Resigned | Drooping eyes, downturned mouth | `drooping_eyes_downturned_mouth.jpg` |
| 007 | Surprised | Raised eyebrows, wide open eyes | `raised_eyebrows_wide_eyes.jpg` |
| 008 | Skeptical | One eyebrow raised, smirk | `one_eyebrow_raised_smirk.jpg` |
| 009 | Stressed | Tension around eyes, tight expression | `tension_around_eyes.jpg` |
| 010 | Genuinely Happy | Smile with crinkled eyes (Duchenne smile) | `genuine_smile_crinkled_eyes.jpg` |

**Download and save to:** `template/static/images/faces/`

---

## 🧪 Testing the Module

### Local Testing
```bash
# From backend/ directory
# Start the Flask server (if not already running)
python3 app.py

# Then visit in browser
http://localhost:5000/module7
```

### What to Test
1. ✅ 3-2-1 countdown displays and animates
2. ✅ First card loads with image
3. ✅ Audio plays automatically (or click replay button)
4. ✅ 4 choice buttons appear
5. ✅ Click correct answer → green glow + feedback + XP
6. ✅ Click wrong answer → red glow + shows correct answer
7. ✅ 60-second timer counts down
8. ✅ After 10 cards or timer expires → summary screen
9. ✅ Summary shows accuracy%, XP, and cards correct
10. ✅ Results saved to MongoDB (check backend logs)

---

## 🔌 API Reference

### POST `/api/module7/complete`
**Purpose:** Record game completion and award XP

**Request Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "xp": 450,
  "accuracy": 80,
  "correctCount": 8,
  "totalAnswered": 10,
  "timestamp": "2026-02-28T15:30:00.000Z"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "xp": 1750,
  "accuracy": 80,
  "message": "Module 7 completed with 80% accuracy"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "missing token" | "invalid token" | "user not found"
}
```

---

## 🎤 Game Mechanics Explained

### Scoring System
- **Correct Answer:** +50 XP base + speed bonus (up to +30 if answered within first 10 seconds)
- **Incorrect Answer:** -10 XP penalty
- **Minimum Score:** 0 (never goes negative)

### Timer
- **Duration:** 60 seconds per session
- **Cards per Session:** 10 flashcards max
- **Game Ends When:** Either all 10 cards completed OR 60 seconds elapsed (whichever comes first)

### Accuracy Calculation
```
Accuracy = (Correct Answers / Total Answers) × 100
```

### Feedback Types
- **Visual:** Neon green (correct) or neon red (incorrect)
- **Audio:** Integration ready for success/error sounds
- **Text:** Card-specific feedback explaining the emotional subtext conflict

---

## 🏆 Hackathon Pitch Talking Points

When presenting Module 7:

**Problem:** "Social cues are multimodal—people smile while saying something mean. Traditional emotion AI struggles because it processes one signal at a time."

**Solution:** "We created a gamified training module that forces rapid human interpretation of conflicting visual and auditory cues. No LLM delays—just raw data processing."

**Why It Matters:** 
- Zero latency (JSON-driven, no backend AI calls)
- Stable for demo (no API dependencies)
- Proves frontend design expertise (Vue.js-style state management in vanilla JS)
- Addresses real-world problem (emotional intelligence training)

**Key Differentiator:** "By removing the LLM for this module, we created a baseline. Compare Module 7's instant feedback loop to Module 6's AI-powered analysis—both approaches serve the same goal differently."

---

## 📝 File Checklist

Before demo day, ensure you have:

- [ ] `template/module7.html` ✅
- [ ] `template/static/js/module7.js` ✅
- [ ] `template/static/data/emotion-matrix-deck.json` ✅
- [ ] `backend/module7.py` ✅
- [ ] `backend/views.py` (module7 route added) ✅
- [ ] `backend/app.py` (module7_bp imported & registered) ✅
- [ ] `template/static/images/faces/` with 10 images
- [ ] `template/static/audio/elevenlabs/` with 10 MP3s
- [ ] All audio files referenced in JSON match filenames exactly

---

## 🐛 Troubleshooting

### Images Don't Load
- Check file paths in JSON match exactly (case-sensitive on Linux)
- Verify images are in `template/static/images/faces/`
- Open browser dev tools (F12) → Console for 404 errors

### Audio Doesn't Play
- Check audio files in `template/static/audio/elevenlabs/`
- Verify audio format is MP3 (some browsers require specific codec)
- Check browser console for CORS errors (shouldn't happen locally)

### Countdown Doesn't Display
- Check browser console for JS errors
- Verify `module7.json` loaded (Network tab in Dev Tools)
- Ensure `emotionDeck` is populated before `startCountdown()`

### Results Not Saving
- Check user is authenticated (token in localStorage)
- Verify `/api/module7/complete` endpoint exists
- Check browser Network tab → POST request → response body
- Verify MongoDB `users_col` is connected in `backend/config.py`

---

## 🚀 Future Enhancements

- [ ] Add optional audio visualization (waveform during playback)
- [ ] Implement daily leaderboard (top 10 highest accuracy)
- [ ] Add difficulty levels (Easy: clear emotions → Hard: subtle subtext)
- [ ] Generate audio programmatically (replace static ElevenLabs files)
- [ ] Add pause button + resume functionality
- [ ] Support multiple languages (different ElevenLabs voices)

