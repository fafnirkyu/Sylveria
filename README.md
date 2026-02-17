# Sylveria — AI Dragon Companion

**Sylveria** is a deeply personalized, voice-activated AI companion built using Python and a locally run LLM via [Ollama](https://ollama.com/).  
Designed as a mythic silver dragon, she is more than a chatbot — she is a real-time interactive personality system with memory, emotion, autonomy, and a **custom-trained voice**.

> 🛠️ This is a personal project by [Antonio Carlos Borges Neto](mailto:borgesneto.ag_@Hotmail.com), designed to explore and showcase advanced software engineering skills in AI, NLP, emotional modeling, dataset curation, and system integration.

---

## 🔮 Features

### 🧠 Personality Engine
- Persistent personality state with tone and emotion tracking.
- Dynamic prompt construction with emotional context and environmental awareness.
- Modular character design via `SylveriaPromptBuilder`.

### 🎓 Fine-Tuning with LoRA
Sylveria’s personality isn’t just scripted — it’s **trained**.

I fine-tuned a base model (**Mythomist-7B**) with **LoRA adapters**, creating a custom dataset of ~5k examples that capture her bonded, mythic voice:

- 📖 **Dialogue extraction**: Quotes from  
  - *Saphira* (Eragon)  
  - *Ruth* (Dragonriders of Pern)  
  - *Cortana* (Halo)  
- ✍️ **50 handcrafted “seed” samples**: Defining Sylveria’s unique mythic, loving tone.  
- 🤖 **Synthetic augmentation**: A smaller LLM (Qwen 0.6B) was used to generate thousands of diverse companion-style conversations.  

✅ The result: Sylveria speaks with a consistent, affectionate, and mythic personality — not just templated prompts.

---

## 🧪 LoRA Training Guide

This repo contains everything needed to **reproduce Sylveria’s fine-tuning** on top of Mythomist-7B.  

### 1. Prepare Environment
```bash
git clone https://github.com/YOUR_USERNAME/Sylveria.git
cd Sylveria
pip install -r requirements.txt
```

### 2. Build Dataset
- Add your API key to dataset_builder.py
- Run dataset builder:
```bash
python finetune/dataset_builder.py
```
This produces the training file with 1,000 high-quality dialogue pairs. (`sylveria_dataset.jsonl`).

### 3. Run LoRA Training
- Training is optimized for an 8GB VRAM GPU (like an RTX 3070) using 4-bit quantization and paged optimizers:
```bash
python train_lora.py
```
Base Model: unsloth/gemma-2-2b-it-bnb-4bit.
Output: Saves adapters to ./sylveria_final_lora.
Config: Uses Rank 64/Alpha 64 to deeply bake the personality into the model.


### 5. Export for Local Inference
After training:
```bash
python export_to_gguf.py
```
Merging LoRA weights into the official FP16 google/gemma-2-2b-it base.
Fixing shared tensor keys to prevent conversion errors.
Exporting the final model to gguf/sylveria_gemma_2b.gguf.

Now you can load Sylveria locally in **Ollama** or `llama.cpp`:
```bash
ollama create sylveria -f ./Modelfile
ollama run sylveria
```

---

## 🗣️ Real-Time Voice Assistant
- Always-listening wake word (`"Sylveria"`) detection.
- Whisper-based local speech recognition.
- Edge TTS voice synthesis with emotional modulation (tone + pitch).

## 🔍 Natural Language Command Engine
- ActionPlanner system for parsing and executing spoken commands.
- Memory logging, thought journaling, and emotional memory retention.
- Growth tracking for behavioral evolution.

## 🌦 Environmental Simulation
- Internal clock (day/night awareness).
- Virtual weather and wind conditions that influence tone.
- Contextual responses affected by simulated environment.

---

## 🔌 Plugin Architecture

Sylveria supports plugin-based extension through a modular system. Current plugins include:

- 🎧 **Spotify Plugin** — Play, pause, and control music with voice.
- 🌐 **Web Search Plugin** — Ask general questions via DuckDuckGo or other engines.
- ☁️ **Weather Plugin** — Get live weather reports via `wttr.in`.  
  Automatically detects the user's city via IP-based geolocation for default responses.
- 📅 **Google Calendar Plugin** — Manage events, reminders, and schedules.
- 💬 **Twitch Chat Integration** — Let Sylveria act as a co-streamer and chatbot on your Twitch channel.
- 🤖 **Discord Bot Plugin** — Interact with Sylveria via a Discord bot.
- 🐍 **Script Runner Plugin** — Sylveria can execute custom Python scripts placed in the `scripts/` folder using natural language instructions.

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
├── finetune/
│   ├── dataset_builder.py  # Extracts + rewrites datasets from PDFs
│   ├── train_lora.py       # LoRA fine-tuning pipeline
│   ├── export_to_gguf.py   # Convert LoRA + base into GGUF
│   └── sylveria_dataset.jsonl
├── models/                 # GGUF models (e.g., Sylveria’s LoRA fine-tuned model)
├── main.py                 # Entry point
├── requirements.txt
└── README.md
```

