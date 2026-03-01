🎨 Bridge Communications Co: Frontend UI & Module Blueprint

This document is the ultimate guide for Teammate 2 (Frontend/Systems). It details every HTML page, the layout, and exactly how the user interacts with each of the training modules.

🌌 Global Aesthetic: "Cyber-Corporate Simulator"

Theme: Dark mode by default. Deep slate backgrounds (bg-slate-900).

Styling: Tailwind CSS via CDN. Lots of "glassmorphism" (semi-transparent dark panels with blur, backdrop-blur-md).

Feedback Colors: Neon Green (Success/Correct), Neon Red (Failure/Masking Drop), Cyan (Primary Action/Hold-to-Speak).

Navigation: A persistent top navbar or left sidebar on all pages (except Login) containing the logo, user XP score, and a "Back to Lounge" button.

🏠 Core Platform Pages

1. The Onboarding Screen (index.html)

The Vibe: A secure, terminal-style entry point.

Layout: Centered login card on a dark, subtly animated grid background.

Functionality:

Inputs for Username and Social Persona (Dropdown: e.g., "Job Seeker", "Awkward Texter", "Conflict Avoider").

On submit, hits Flask to create/fetch the user from MongoDB and redirects to lounge.html.

2. The Dashboard & Hub (lounge.html)

The Vibe: The mission control center.

Layout:

Top Bar: Displays the user's total "Humanity Score" (XP).

Left Column (Leaderboard): A scrolling list fetching real-time top scores from MongoDB. Proves the app is live.

Main Grid (The Gyms): A visually appealing grid of cards. Each card represents a training module. Clicking a card takes the user to that specific module's HTML page.

📱 Gym 1: The Digital Comm Suite (chat-module.html)

This is a single HTML page that uses Vue.js (via CDN) to manage the chat state. It reads the URL parameter (e.g., ?type=icebreaker) to tell Flask which AI prompt to use.

Layout: Split screen.

Left Side (The Phone): A mock iMessage interface with scrollable text bubbles. An input bar at the bottom.

Right Side (The Debugger): A sleek side-panel that displays the AI's real-time psychological breakdown and accuracy scores.

🧩 Sub-Modules (Determined by URL parameter):

Sarcasm Sweeper (?type=sarcasm):

How it works: A 5-message group chat is pre-loaded on the screen. The user's input bar is disabled. Instead, checkboxes appear next to every incoming text.

The Goal: The user must check the box next to the text that contains hidden passive-aggression or sarcasm. Clicking "Analyze" sends their choice to Flask for grading.

The Icebreaker (?type=icebreaker):

How it works: An empty chat. The user types the first message to a stranger at a networking event.

The Goal: Successfully introduce themselves and find a common interest within 5 total messages. The AI grades the conversation's flow and warmth.

Hint Hunter (?type=hint):

How it works: The user enters an ongoing chat. The user has to start with meaningful good conversation (which will also be evaluated). The AI starts dropping subtle hints ("Wow, look at the time", "I have an early morning").

The Goal: The user must pick up on the cue and type a polite closing message ("I'll let you go, have a good night!"). Failing to close the chat loses XP.

The Ping-Pong Protocol (?type=pingpong):

How it works: A standard chat interface.

The Goal: Keep the conversation going for 6 turns. If the user asks a "closed-ended" question (one that can be answered with just "yes" or "no") or replies with answers that aren’t conductive of a conversation, the AI Debugger flashes red and deducts points, also explaining how the user can explain and why.

🎙️ Gym 2: The Vocal Sandbox (module-audio.html)

This page relies on Vanilla JS, the native Web Speech API, Hark.js (for stutter detection), and ElevenLabs for playback.

Layout: A highly focused, minimalist screen.

Top: A scenario card (e.g., "Your boss is asking you to work Saturday. Say no politely."). These will be hardcoded in.

Center: A massive, glowing "Hold to Speak" button.

Bottom: An invisible audio player that appears when the AI responds, alongside a "Confidence Score" meter.

🧩 Sub-Modules:

Tone Check (?type=conflict):

How it works: The user presses and holds the main button to verbally respond to a stressful prompt (e.g., an unreasonable request from a boss). The browser's native Web Speech API transcribes their spoken words into text. This transcript is sent to the Flask backend, where LLaMA assumes the persona of the aggressor and generates a logical response. Flask then routes this response through ElevenLabs to generate an emotionally realistic, high-quality audio clip (e.g., an angry or disappointed voice), which is seamlessly played back to the user.

The Goal: Successfully de-escalate the hostile interaction while firmly maintaining personal boundaries. The AI evaluates the user's transcript to determine if they successfully resolved the conflict without caving under pressure or lashing out inappropriately.

The Pitch (?type=pitch):

How it works: User is asked to introduce themselves for a job interview. They hold the button and speak.

The Goal: Hark.js monitors the audio stream. If the user stops speaking for more than 1.5 seconds multiple times (stuttering/hesitation), or if the Web Speech API picks up "um" and "uh", the "Confidence Score" drops. The AI replies with constructive feedback on their vocal delivery.

🎭 Gym 3: The Facial Gym (module-face.html)

This page uses Vanilla JS and the face-api.js library running entirely in the browser to analyze webcam feeds.

Layout: Split screen.

Left Side (The Prompt): Displays either a static image or a scenario text.

Right Side (The Mirror): The user's live webcam feed (encased in a sleek UI frame). A live emotional readout overlays the corner (e.g., Happy: 80%, Neutral: 20%).

🧩 Sub-Modules:

Expression Reader (?type=static):

How it works: The webcam is OFF. The left side shows a complex human facial expression (e.g., "Skeptical"). Multiple choice buttons appear below it.

The Goal: A fast-paced flashcard game to correctly identify the emotion.

Face Emotions Helper (?type=live):

How it works: The webcam is ON. face-api.js is actively drawing bounding boxes on the user's face. The prompt gives a scenario: "Your friend just told you they are adopting a puppy." Prompts will be pre-built in

The Goal: The user must physically hold the socially appropriate expression (in this case, "Happy" or "Excited" > 0.70 threshold) for 3 continuous seconds. If their face drops to "Neutral" or "Sad", the timer resets and the border flashes red. 