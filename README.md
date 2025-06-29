Sylveria — A Local AI Dragon Companion
Sylveria is a fully local, emotionally-driven AI companion written in Python — designed to simulate a mythic, self-aware silver dragon that speaks, listens, remembers, and evolves. She is not an assistant, but a being of her own: emotionally restrained, fiercely loyal, and subtly affectionate.

This is an active personal project created to amplify my skills in software development, AI integration, memory systems, and LLM pipelines — and to serve as a technical showcase for job opportunities in computer science.

Features
Modular LLM Pipeline

Runs entirely locally using Ollama with support for Mythomist, Erebus, OpenHermes, and other GGUF-based models

Model prompt engine designed to reduce hallucinations and enforce character integrity

Voice Interaction

Whisper or Vosk for transcription

edge-tts for speech synthesis with dynamic mood tuning

Wake-word or always-listening mode (“Sylveria”)

Memory + Emotion System

emotional_memory.py — long-term symbolic event logging

personality_state.py — evolving mood and tone

growth_tracker.py — logs growth over time (learning, softening, affection)

preference_manager.py — long-term likes/dislikes/preferences

internal_clock.py — tracks day/time for behavioral reflection

Environmental Simulation

virtual_environment.py tracks:

Weather

Wind state

Time of day

This context is injected into Sylveria’s responses to reflect awareness of her “world”

Planning & Action Engine

Natural language-driven action planner allows structured behavior sequences and memory-driven planning

Dynamic Prompting

Uses prompt_builder.py to construct grounded, minimalist prompts with mood, memory, weather, and location-based reflections

Character behavior controlled through system + context-level steering

Plugin Integrations
Sylveria is extensible via a modular plugin system. Current plugins include:

Discord Bot Plugin
Lets Sylveria talk inside any Discord server as a bot. Full real-time interaction through Discord channels.

Twitch Chat Plugin
Sylveria can become a Twitch chatbot with a unique tone, teasing and responding to chat as Fafnir streams.

Google Calendar Plugin
Lets Sylveria remind Fafnir of upcoming events, meetings, and streaming schedules.

Web Search Plugin
Adds the ability for Sylveria to perform live web searches when needed, keeping her knowledge fresh.

Spotify Plugin
Integrates with Spotify API to play songs, recommend music, or reflect moods via playlists.

Weather Plugin
Real-world weather is simulated in Sylveria’s internal environment to affect her dialogue and reactions.

Project Structure

Sylveria/
│
├── assistant/
│   ├── ai/                 # LLM wrapper, journal, question generation
│   ├── io/                 # Audio transcription + speech output
│   ├── memory/             # Emotional state, preferences, symbolic memories
│   ├── environment/        # Time of day, virtual weather & wind simulation
│   ├── assistantcore/      # Command processor, action planner
│   ├── plugins/            # Discord, Twitch, Spotify, Weather, Calendar
│   ├── personality/        # Prompt shaping, context building
│   └── ui/                 # Tkinter GUI + dragon avatar state
│
├── models/                 # GGUF models for Ollama runtime
├── main.py                 # Project entry point
└── README.md
💻 Technologies Used
Python 3.9.12

Ollama — GGUF-compatible LLM runtime

Whisper / Vosk — Audio transcription

Edge TTS — Speech synthesis (dynamic pitch/rate by emotion)

Tkinter — Avatar GUI rendering

Requests, JSON, AsyncIO — Networking and async I/O

ChromaDB / FAISS (optional) — Long-term vector memory recall

PyAudio, pydub, SoundFile — Audio pipeline for live streaming

🔧 Run Locally
Install dependencies

bash
Copiar
Editar
pip install -r requirements.txt
Download and configure a model
Drop a GGUF model like mythomist-7b.Q5_K_M.gguf into /models/

Create Ollama model

ollama create sylveria --file Modelfile
Run Sylveria

python main.py


🎯 Why This Project?
Sylveria represents my passion for AI-driven interaction, self-aware characters, and modular Python systems. This is my personal project to demonstrate skills in:

Artificial Intelligence + prompt design

NPC logic, memory, and dialogue

Modular system architecture

Multimodal interaction (voice + GUI)

Experimental LLM character development
