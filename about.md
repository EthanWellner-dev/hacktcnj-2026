🏆 The Social Sandbox: Judges' Brief

🎯 The Core Concept

Social Sandbox is a "flight simulator for human interaction." It is an integrated training suite that helps users master the nuances of communication—from decoding passive-aggressive texts to maintaining facial composure under pressure—all within a private, AI-powered environment.

🛠️ The Technical "Flex" (What to highlight)

1. Privacy-First "Dumb Engine" Architecture (Vultr + Ollama)

Unlike most hackathon projects that simply wrap an OpenAI API, we built our own Local-First AI Backbone.

The Tech: We provisioned a Vultr Cloud GPU instance to host LLaMA 3 via Ollama.

The Why: Social training is deeply personal. By using a self-hosted LLM, we ensure that the user’s vocal transcripts and social anxieties never leave our private infrastructure, providing a level of data sovereignty that standard "wrapper" apps lack.

2. Multi-Modal Analysis Suite

We aren't just analyzing text; we are analyzing the Human Spectrum:

Visual: Using face-api.js for real-time, client-side emotional detection and "masking" verification.

Vocal: Integrating ElevenLabs for emotionally-weighted audio feedback and using Hark.js with the Web Speech API to calculate a "Confidence Score" based on vocal hesitations and filler words.

Contextual: A reusable Vue.js engine that powers four distinct texting modules (Sarcasm, Hint Detection, Icebreaking, and Active Listening).

3. Data-Driven Gamification (MongoDB Atlas)

We’ve implemented a persistent Humanity Score (XP) system. Every micro-interaction across our 3 "Gyms" is logged to a MongoDB Atlas cluster, fueling a live global leaderboard that drives user retention and competitive learning.

🌍 Real-World Impact

For many, especially neurodivergent individuals or those with social anxiety, the "first time" having a difficult conversation shouldn't be in a high-stakes real-world scenario. Social Sandbox provides a safe space to "debug" social cues, allowing users to build muscle memory and confidence before they ever step into a real-world interview or networking event.

💡 Pitch "Power Phrases" for Judging

"We’ve built a multi-modal gym for the most important muscle in the human body: the social muscle."

"Our infrastructure uses Vultr as a secure 'Dumb Engine,' keeping the brain on our server and the privacy in the user’s hands."

"We move beyond chatbots; we've built a social debugger that analyzes the hidden subtext of human interaction."