# Sylveria — Local Voice-Controlled AI Agent

Sylveria is a fully local, voice-interactive AI agent built in Python, running entirely offline via [Ollama](https://ollama.com/) and `llama.cpp`. It combines real-time speech recognition, a fine-tuned local LLM, and a modular plugin system into a single voice-driven assistant — with zero cloud dependency and zero external API calls.

> Personal project by [Antonio Carlos Borges Neto](mailto:borgesneto.ag_@Hotmail.com), built to explore local LLM fine-tuning, real-time voice pipelines, and modular agent architecture.

---

## Features

### Dialogue & State Engine
- Persistent conversational state with tone tracking across a session.
- Dynamic prompt construction with contextual and environmental awareness.
- Modular prompt design via `SylveriaPromptBuilder`.

### LoRA Fine-Tuning Pipeline
Sylveria's response style is fine-tuned, not just prompted.

A base model (Mythomist-7B) was fine-tuned with LoRA adapters on a custom ~5k-example dataset, built from:
- ~50 hand-crafted seed samples defining a consistent response style and tone.
- Synthetic data augmentation, using a smaller LLM (Qwen 0.6B) to generate thousands of diverse example conversations from the seed set.

This produces a consistent, stylistically coherent voice rather than relying on prompt engineering alone.

---

## LoRA Training Guide

This repo contains everything needed to reproduce the fine-tuning pipeline on top of Mythomist-7B.

### 1. Prepare Environment
```bash
git clone https://github.com/YOUR_USERNAME/Sylveria.git
cd Sylveria
pip install -r requirements.txt
```

### 2. Build Dataset
- Add your API key to `dataset_builder.py`
- Run the dataset builder:
```bash
python finetune/dataset_builder.py
```
This produces the training file (`sylveria_dataset.jsonl`) from the seed samples and synthetic augmentation.

### 3. Run LoRA Training
Optimized for an 8GB VRAM GPU (e.g. RTX 3070) using 4-bit quantization and paged optimizers:
```bash
python train_lora.py
```
- **Base model:** `unsloth/gemma-2-2b-it-bnb-4bit`
- **Output:** adapters saved to `./sylveria_final_lora`
- **Config:** rank 64 / alpha 64

### 4. Export for Local Inference
```bash
python export_to_gguf.py
```
Merges LoRA weights into the FP16 `google/gemma-2-2b-it` base, resolves shared tensor key conflicts, and exports to `gguf/sylveria_gemma_2b.gguf`.

Load locally via Ollama or `llama.cpp`:
```bash
ollama create sylveria -f ./Modelfile
ollama run sylveria
```

---

## Real-Time Voice Pipeline
- Wake-word detection (always-listening, local).
- Whisper-based local speech-to-text.
- Edge TTS voice synthesis with tone/pitch modulation.

## Command Engine
- `ActionPlanner` system for parsing and executing spoken commands.
- Session memory logging and state tracking across interactions.

## Environmental Context Simulation
- Internal day/night clock.
- Simulated weather/context state that influences response tone.

---

## Plugin Architecture

Modular plugin system, current plugins include:

- **Spotify** — voice-controlled playback.
- **Web Search** — general Q&A via DuckDuckGo.
- **Weather** — live reports via `wttr.in`, with IP-based geolocation for defaults.
- **Google Calendar** — event and reminder management.
- **Twitch Chat** — co-streamer/chatbot integration.
- **Discord Bot** — conversational interface via Discord.
- **Script Runner** — executes custom Python scripts from the `scripts/` folder via natural language commands.

---

## Project Structure

```plaintext
.
├── assistant/
│   ├── ai/                 # LLM integration, journal, prompt builder
│   ├── io/                 # Audio manager, YouTube integration
│   ├── memory/             # State tracking, session memory, clock
│   ├── assistantcore/      # Commands, action planner, tool helper
│   ├── plugins/            # Plugin modules (weather, Twitch, etc.)
│   ├── environment/        # Environmental context simulation
│   ├── ui/                 # GUI system
│   └── storage/            # Data manager
├── finetune/
│   ├── dataset_builder.py  # Builds fine-tuning dataset from seed + synthetic data
│   ├── train_lora.py       # LoRA fine-tuning pipeline
│   ├── export_to_gguf.py   # Convert LoRA + base into GGUF
│   └── sylveria_dataset.jsonl
├── models/                 # GGUF models
├── main.py                 # Entry point
├── requirements.txt
└── README.md
```

---

## Stack

Python, Whisper, Edge TTS, Ollama, PyTorch, Hugging Face, LoRA/PEFT, GGUF, llama.cpp
