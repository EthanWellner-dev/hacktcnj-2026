# hacktcnj-2026
The winners ofc 🤪

🌐 Social Sandbox: Project Overview

Elevator Pitch: Social Sandbox is a gamified, privacy-focused training platform designed to help users practice and improve their real-world social skills in a safe, low-stakes digital environment. Powered by a custom-hosted local AI, the platform provides highly specific, actionable feedback to build social confidence without compromising user data.

🛑 The Problem

Post-pandemic isolation and the rise of digital-first communication have left many people—especially young adults—struggling with real-world social anxiety. Whether it's reading a room, navigating a hostile work conversation, or simply keeping small talk alive, there are few places to actively practice these soft skills without the fear of real-world embarrassment.

💡 The Solution

Social Sandbox acts as a "flight simulator" for human interaction. By breaking down social skills into gamified, bite-sized modules across three distinct "Gyms," users can safely train their communication muscles, earn XP (Humanity Score), and climb a global leaderboard.

🏛️ The Three Training Gyms

📱 Gym 1: The Digital Comm Suite

A hyper-realistic texting simulator to decode subtext and build conversational stamina.

Sarcasm Sweeper: Users read a pre-generated chat and must successfully identify texts hiding passive-aggression or sarcasm.

The Icebreaker: Practice initiating conversation with a "stranger" at a networking event and finding common ground within 5 messages.

Hint Hunter: The AI drops subtle hints that it needs to leave the conversation. The user must recognize the social cue and politely exit.

The Ping-Pong Protocol: Practice active listening by keeping a conversation alive for 6 turns without relying on conversation-killing "yes/no" questions.

🎙️ Gym 2: The Vocal Sandbox

Voice-based roleplay to practice conflict resolution and presentation confidence.

Tone Check: Users hold a button to verbally respond to a stressful prompt (e.g., an angry boss). The AI evaluates their de-escalation skills, while ElevenLabs generates a realistic, emotional audio reply.

The Pitch: Users practice introducing themselves. The browser tracks vocal pauses, "ums," and "uhs" to generate a real-time Confidence Score.

🎭 Gym 3: The Facial Gym

Client-side computer vision to practice reading and managing non-verbal cues.

Expression Reader: A fast-paced visual flashcard game to correctly identify complex human emotions.

Face Emotions Helper: Live "masking" practice. Given a specific situational prompt (e.g., "Your friend just got a promotion"), the user must use their webcam to hold the socially appropriate expression (e.g., "Happy") for 3 continuous seconds.

🛠️ The Tech Stack

Frontend (The Body)

Core: HTML5, Vanilla JavaScript, Tailwind CSS (via CDN).

State Management: Vue.js (via CDN) mounted specifically for the complex Chat UI.

Client-Side ML: face-api.js (Webcam Emotion Tracking), Native Web Speech API (Speech-to-Text), Hark.js (Vocal pause tracking).

Backend & Data (The Bridge)

API: Python / Flask (Local routing).

Database: MongoDB Atlas (User Profiles, XP, Leaderboard).

AI & Cloud Infrastructure (The Brain)

Cloud Hardware: Vultr Cloud GPU Instance (NVIDIA).

Local LLM: Ollama running LLaMA 3 8B strictly localized on the Vultr server for absolute data privacy.

Voice Generation: ElevenLabs API for realistic Text-to-Speech in the Vocal Sandbox.

Privacy First: By bypassing standard OpenAI wrappers and running LLaMA 3 locally on a Vultr GPU, we protect vulnerable user data (like their voice and social anxieties).

---

## Local development

1. **Backend** – from the project root:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # or activate.bat on cmd
   # make sure you installed PyJWT not the conflicting `jwt` package
   pip uninstall jwt -y || echo "no jwt package"
   pip install -r requirements.txt
   # set MONGODB_URI if using a remote Atlas or non-default host
   # $env:MONGODB_URI="mongodb://user:pass@host:27017/"
   python app.py
   ```
   The Flask API will start on `http://127.0.0.1:5000` and also serve the static front-end.  It now supports `/api/users/signup`, `/api/users/login` (both POST with json `{username,password,persona}`) and `/api/users/leaderboard`.  The UI has separate pages: `/` for login, `/dashboard` for the user lounge (logout is top‑right), and `/modules` for the module directory.  The dashboard no longer shows sensitive cluster info and logout lives in the header.

2. **Frontend** – the HTML/JS lives in the `template/` folder. Open `http://127.0.0.1:5000/` in a browser after the backend is running. The initial page provides a login/signup form and leaderboard.  Further UI modules will be built in this directory.

### Running tests

From `backend/` while the virtualenv is activated you can run:
```powershell
pytest test_app.py
```
which will exercise signup/login/leaderboard against a temporary database state.

---

Deep Technical Breadth: Integrates client-side Computer Vision (face-api.js), local Cloud GPU infrastructure, and external APIs (ElevenLabs) into a single cohesive platform.

High Polish, Low Friction: The hybrid architecture (Vanilla HTML pages + highly specific Vue components) allows for a massive suite of mini-games without the bugs of a complex Single Page Application.