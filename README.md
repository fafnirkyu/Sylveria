# Sylveria — AI Dragon Companion

**Sylveria** is a deeply personalized, voice-activated AI companion built using Python and a locally run LLM via [Ollama](https://ollama.com/). Designed as a mythic silver dragon, she is more than a chatbot — she is a real-time interactive personality system with memory, emotion, and autonomy.

> 🛠️ This is a personal project by [Antonio Carlos Borges Neto](mailto:borgesneto.ag_@Hotmail.com) designed to explore and showcase advanced software engineering skills in AI, NLP, emotional modeling, and system integration.

---

## 🔮 Features

### 🧠 Personality Engine
- Persistent personality state with tone and emotion tracking.
- Dynamic prompt construction with emotional context and environmental awareness.
- Modular character design via `SylveriaPromptBuilder`.

### 🗣️ Real-Time Voice Assistant
- Always-listening wake word (`"Sylveria"`) detection.
- Whisper-based local speech recognition.
- Edge TTS voice synthesis with emotional modulation (tone + pitch).

### 🔍 Natural Language Command Engine
- ActionPlanner system for parsing and executing spoken commands.
- Memory logging, thought journaling, and emotional memory retention.
- Growth tracking for behavioral evolution.

### 🌦 Environmental Simulation
- Internal clock (day/night awareness).
- Virtual weather and wind conditions that influence tone.
- Contextual responses affected by simulated environment.

---

## 🔌 Plugin Architecture

Sylveria supports plugin-based extension through a modular system. Current plugins include:

- 🎧 **Spotify Plugin** — Play, pause, and control music with voice.
- 🌐 **Web Search Plugin** — Ask general questions via DuckDuckGo or other engines.
- ☁️ **Weather Plugin** — Get live weather reports via `wttr.in`.
- 📅 **Google Calendar Plugin** — Manage events, reminders, and schedules.
- 💬 **Twitch Chat Integration** — Let Sylveria act as a co-streamer and chatbot on your Twitch channel.
- 🤖 **Discord Bot Plugin** — Interact with Sylveria via a Discord bot.

---

## 🧩 Project Structure

```plaintext
.
├── assistant/
│   ├── ai/                 # LLM integration, journal, prompt builder
│   ├── io/                 # Audio manager, YouTube integration
│   ├── memory/             # Personality state, emotional memory, clock
│   ├── assistantcore/      # Commands, action planner, tool helper
│   ├── plugins/            # Plugin modules (weather, Twitch, etc.)
│   ├── environment/        # VirtualEnvironment simulation
│   ├── ui/                 # GUI avatar system
│   └── storage/            # Data manager
├── models/                 # GGUF models (e.g., Sylveria's custom model)
├── main.py                 # Entry point
├── requirements.txt
└── README.md
