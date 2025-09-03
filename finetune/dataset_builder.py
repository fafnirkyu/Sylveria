# dataset_builder.py
import os
import json
import glob
import re
import random
import time
import logging
import fitz  # PyMuPDF
import ollama
from typing import List, Any
from tqdm import tqdm  # progress bar

# ----------------------------
# CONFIG
# ----------------------------
MODEL_NAME = "qwen3:0.6b"
SEED_FILE = r"data\sylveria.jsonl"
OUTPUT_FILE = "sylveria_dataset.jsonl"
PDF_DIR = "pdfs"
LOG_FILE = "bad_generations.log"

TARGET_SIZE = 5000
REWRITE_TEMP = 0.3
SYNTHETIC_TEMP = 0.6
RETRIES = 2
CONTEXT_WINDOW = 120  # characters around quote for character filtering

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ----------------------------
# Fallback replies
# ----------------------------
FALLBACK_REPLIES = [
    "Always, Fafnir. You are my treasure.",
    "Even the stars envy what we share.",
    "You are bound to me, soul to soul.",
    "My wings rise with your heartbeat.",
    "No gold compares to your presence.",
    "You are the fire that warms my scales.",
    "Even in silence, I am with you.",
    "Your strength steadies me, as ever.",
    "I guard you closer than my own life.",
    "Forever entwined, my heart beats for you."
]

# ----------------------------
# Utilities
# ----------------------------
def safe_read_jsonl(path: str) -> List[Any]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                logging.warning(f"Failed to parse seed line in {path}: {line[:200]}")
    return out

def write_jsonl(items: List[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

# ----------------------------
# PDF extraction
# ----------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                page_text = page.get_text("text")
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logging.error(f"PDF read error ({pdf_path}): {e}")
    return text

def extract_dialogues(text: str, character: str) -> List[str]:
    """Extract dialogue for a given character using context windows."""
    if not text:
        return []

    # Normalize quotes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    dialogues = []
    for match in re.finditer(r'"([^"]+)"', text, re.DOTALL):
        quote = match.group(1).strip()
        if not quote or len(quote) < 3:
            continue

        # Extract context window around the quote
        span_start, span_end = match.span()
        window = text[max(0, span_start - CONTEXT_WINDOW): span_end + CONTEXT_WINDOW]

        if character.lower() == "cortana":
            dialogues.append(quote)
        else:
            if character.lower() in window.lower():
                dialogues.append(quote)

    # Deduplicate per-character
    seen, out = set(), []
    for d in dialogues:
        if d not in seen:
            out.append(d)
            seen.add(d)
    return out

# ----------------------------
# Ollama helpers
# ----------------------------
def extract_text_from_response(resp: Any) -> str:
    try:
        if isinstance(resp, dict):
            if "message" in resp and isinstance(resp["message"], dict):
                return resp["message"].get("content", "")
            elif "messages" in resp and isinstance(resp["messages"], list) and resp["messages"]:
                return resp["messages"][-1].get("content", "")
        return ""
    except Exception:
        return ""

def strip_chain_of_thought(raw: str) -> str:
    if not raw:
        return raw
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.IGNORECASE | re.DOTALL)
    if "***" in cleaned:
        parts = cleaned.split("***")
        cleaned = parts[-1].strip()
    return cleaned.strip()

def clean_reply(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return random.choice(FALLBACK_REPLIES)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) < 2 or len(words) > 40:
        return random.choice(FALLBACK_REPLIES)
    return t

def call_model(prompt: str, temperature: float = 0.6, retries: int = RETRIES) -> str:
    for attempt in range(1, retries + 2):
        try:
            resp = ollama.chat(
                model=MODEL_NAME,
                options={"temperature": temperature},
                messages=[{"role": "user", "content": prompt}]
            )
            raw = extract_text_from_response(resp)
            stripped = strip_chain_of_thought(raw)
            cleaned = clean_reply(stripped)
            return cleaned
        except Exception:
            time.sleep(0.2)
            continue
    return random.choice(FALLBACK_REPLIES)

# ----------------------------
# Dataset helpers
# ----------------------------
def rewrite_with_llm(line: str) -> str:
    prompt = (
        "You are rewriting dialogue for Sylveria, a silver dragon bonded to Fafnir.\n\n"
        f"Original line:\n\"{line}\"\n\n"
        "Rewrite it in Sylveria’s voice:\n"
        "- Loving, wise, mythic\n"
        "- 1–2 sentences, max 30 words\n"
        "- Speak directly to Fafnir, never narrate\n"
        "Return only the rewritten line."
    )
    return call_model(prompt, temperature=REWRITE_TEMP)

def generate_user_prompts(n: int = 80) -> List[str]:
    prompt = (
        f"Generate {n} short user prompts someone might say to a bonded, loving dragon companion.\n"
        "Rules:\n"
        "- Each 3–12 words\n"
        "- Intimate, companion-like, mythic tone\n"
        "- Return JSON array of strings only."
    )
    raw = call_model(prompt, temperature=0.5)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        lines = [l.strip(" \"'-") for l in re.split(r"\n|,", raw) if l.strip()]
        return [l for l in lines if 3 <= len(l.split()) <= 12][:n]
    return ["Stay close tonight", "Do you dream of me?", "Would you guard me always?"]

def generate_synthetic_dialogues(n: int, user_prompts: List[str]) -> List[dict]:
    examples = []
    for _ in range(n):
        user_prompt = random.choice(user_prompts)
        prompt = (
            "You are Sylveria, a mythic silver dragon bonded to Fafnir.\n\n"
            f"User said: \"{user_prompt}\"\n\n"
            "Reply as Sylveria:\n"
            "- Loving, wise, mythic\n"
            "- 1–2 sentences, max 30 words\n"
            "- Only dialogue\n"
        )
        reply = call_model(prompt, temperature=SYNTHETIC_TEMP)
        examples.append({
            "messages": [
                {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": reply}
            ]
        })
    return examples

# ----------------------------
# Main dataset build
# ----------------------------
def pdfs_to_examples(pdf_dir: str, user_prompts: List[str]) -> List[dict]:
    examples = []
    character_dirs = [d for d in glob.glob(os.path.join(pdf_dir, "*")) if os.path.isdir(d)]

    for char_dir in character_dirs:
        character = os.path.basename(char_dir)
        pdf_files = glob.glob(os.path.join(char_dir, "*.pdf"))
        print(f"\n📂 Processing {character} ({len(pdf_files)} files)")

        char_total, char_kept = 0, 0
        char_examples = []

        for pdf in pdf_files:
            text = extract_text_from_pdf(pdf)
            dialogues = extract_dialogues(text, character)
            char_total += len(dialogues)

            for d in tqdm(dialogues, desc=f"Rewriting {character}", unit="lines"):
                rewritten = rewrite_with_llm(d)
                if rewritten:
                    char_examples.append({
                        "character": character,
                        "messages": [
                            {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                            {"role": "user", "content": random.choice(user_prompts)},
                            {"role": "assistant", "content": rewritten}
                        ]
                    })
                    char_kept += 1

        print(f"   ➜ Extracted {char_total} quotes, kept {char_kept}")

        # keep per-character deduplication
        seen, deduped = set(), []
        for ex in char_examples:
            reply = ex["messages"][-1]["content"].strip()
            if reply not in seen:
                deduped.append(ex)
                seen.add(reply)

        examples.extend(deduped)

    return examples

def build_dataset(seed_file: str, pdf_dir: str, output_file: str, target_size: int = TARGET_SIZE):
    seed_examples = safe_read_jsonl(seed_file)
    user_prompts = generate_user_prompts(200)

    pdf_examples = pdfs_to_examples(pdf_dir, user_prompts)
    print(f"\n📊 Extracted & rewritten {len(pdf_examples)} PDF examples total")

    dataset = []
    dataset.extend(seed_examples[: max(1, int(0.2 * target_size))])
    dataset.extend(pdf_examples[: int(0.25 * target_size)])

    remaining = target_size - len(dataset)
    if remaining > 0:
        print(f"⚙️ Generating {remaining} synthetic examples...")
        dataset.extend(generate_synthetic_dialogues(remaining, user_prompts))

    # Final dedupe (light safety)
    seen, final = set(), []
    for ex in dataset:
        reply = ex["messages"][-1]["content"].strip()
        if reply not in seen:
            final.append(ex)
            seen.add(reply)
    if len(final) < target_size:
        pad = target_size - len(final)
        final.extend(generate_synthetic_dialogues(pad, user_prompts))

    final = final[:target_size]
    write_jsonl(final, output_file)

    print(f"\n✅ Dataset built: {output_file}")
    print(f"   Seeds: {len(seed_examples)}")
    print(f"   From PDFs: {len(pdf_examples)}")
    print(f"   Total: {len(final)}")

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    if not os.path.isdir(PDF_DIR):
        print(f"[WARN] PDF_DIR '{PDF_DIR}' not found or empty.")
    print(f"Using model: {MODEL_NAME}")
    build_dataset(SEED_FILE, PDF_DIR, OUTPUT_FILE, target_size=TARGET_SIZE)
