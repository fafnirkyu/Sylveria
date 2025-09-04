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
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# CONFIG
# ----------------------------
MODEL_NAME = "qwen3:0.6b"   # small + fast model for rewriting
SEED_FILE = r"data\sylveria.jsonl"
OUTPUT_FILE = "sylveria_dataset.jsonl"
PDF_DIR = "pdfs"
LOG_FILE = "bad_generations.log"

TARGET_SIZE = 5000
REWRITE_TEMP = 0.3
SYNTHETIC_TEMP = 0.6
RETRIES = 2
BATCH_SIZE = 50         # how many lines to process at once
MAX_WORKERS = 4          # parallel PDF parsing

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

def extract_dialogues(text: str, character: str = None) -> List[str]:
    """
    Extract dialogue lines from novels/PDFs.
    Supports straight quotes, curly quotes, and em-dash dialogue.
    Special case: for Cortana, keep ALL dialogue.
    """
    if not text:
        return []

    # normalize
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    dialogues = []

    # 1. Quoted dialogue
    for match in re.finditer(r'"([^"]{3,400})"', text):
        q = match.group(1).strip()
        if 3 <= len(q.split()) <= 60:
            dialogues.append(q)

    # 2. Em-dash dialogue (— Hello there)
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("—") and len(line) > 4:
            cleaned = line.lstrip("— ").rstrip("— ").strip()
            if 3 <= len(cleaned.split()) <= 60:
                dialogues.append(cleaned)

    # 3. Paragraph-starting quotes
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith('"') and len(line) > 6:
            line = line.strip('" ')
            if 3 <= len(line.split()) <= 60:
                dialogues.append(line)

    # 🔹 Special case: Cortana → keep everything
    if character and character.lower() == "cortana":
        pass
    elif character:
        char_lower = character.lower()
        filtered = []
        for q in dialogues:
            if char_lower in q.lower() or random.random() < 0.3:  # keep 30% fallback
                filtered.append(q)
        dialogues = filtered

    # Deduplicate & clean
    seen, cleaned = set(), []
    for q in dialogues:
        q_norm = re.sub(r"[!?.,…]+$", "", q).strip()
        if q_norm and q_norm not in seen:
            seen.add(q_norm)
            cleaned.append(q_norm)

    return cleaned

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
        return ""
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) < 2 or len(words) > 40:
        return ""
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
            if cleaned:
                return cleaned
        except Exception:
            time.sleep(0.2)
            continue
    return ""

# ----------------------------
# Batch rewrite
# ----------------------------
def batch_rewrite_with_llm(lines: List[str], batch_size: int = BATCH_SIZE) -> List[str]:
    results = []
    for i in range(0, len(lines), batch_size):
        chunk = lines[i:i+batch_size]
        joined = "\n".join([f"- {l}" for l in chunk])

        prompt = (
            "You are rewriting dialogue for Sylveria, a silver dragon bonded to Fafnir.\n\n"
            "Rewrite each of the following lines in her voice:\n"
            "- Loving, wise, mythic\n"
            "- Speak directly to Fafnir, never narrate\n"
            "- 1–2 sentences per line, max 30 words\n\n"
            f"Original lines:\n{joined}\n\n"
            "Return the rewritten lines as a JSON array of strings, in the same order."
        )

        raw = call_model(prompt, temperature=REWRITE_TEMP)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                cleaned = [clean_reply(p) or c for p, c in zip(parsed, chunk)]
                results.extend(cleaned)
            else:
                results.extend(chunk)
        except Exception:
            results.extend(chunk)
    return results

# ----------------------------
# Dataset helpers
# ----------------------------
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
        if isinstance(parsed, list) and parsed:
            return parsed
    except Exception:
        pass

    # 🔹 Fallback list
    return [
        "Stay close tonight",
        "Do you dream of me?",
        "Would you guard me always?",
        "Do you still remember our bond?",
        "Speak to me, Sylveria",
        "What do you see in the stars?",
        "Are you proud of me?",
        "Will you fly with me again?"
    ][:n]

# ----------------------------
# Synthetic dialogue generation (batched)
# ----------------------------
def batch_generate_synthetic_dialogues(n: int, user_prompts: List[str], batch_size: int = BATCH_SIZE) -> List[dict]:
    examples = []
    for i in range(0, n, batch_size):
        chunk_prompts = [random.choice(user_prompts) for _ in range(min(batch_size, n - i))]
        joined = "\n".join([f"- {p}" for p in chunk_prompts])

        prompt = (
            "You are Sylveria, a mythic silver dragon bonded to Fafnir.\n\n"
            "For each of the following user prompts, reply in her voice:\n"
            "- Loving, wise, mythic\n"
            "- 1–2 sentences, max 30 words\n"
            "- Only dialogue\n\n"
            f"User prompts:\n{joined}\n\n"
            "Return the replies as a JSON array of strings, in the same order."
        )

        raw = call_model(prompt, temperature=SYNTHETIC_TEMP)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and len(parsed) == len(chunk_prompts):
                for up, reply in zip(chunk_prompts, parsed):
                    reply = clean_reply(reply) or random.choice(FALLBACK_REPLIES)
                    examples.append({
                        "messages": [
                            {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                            {"role": "user", "content": up},
                            {"role": "assistant", "content": reply}
                        ]
                    })
            else:
                for up in chunk_prompts:
                    reply = call_model(
                        f"You are Sylveria, a mythic silver dragon bonded to Fafnir.\n\n"
                        f"User said: \"{up}\"\n\n"
                        "Reply as Sylveria:\n- Loving, wise, mythic\n- 1–2 sentences, max 30 words\n- Only dialogue",
                        temperature=SYNTHETIC_TEMP
                    ) or random.choice(FALLBACK_REPLIES)
                    examples.append({
                        "messages": [
                            {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                            {"role": "user", "content": up},
                            {"role": "assistant", "content": reply}
                        ]
                    })
        except Exception:
            for up in chunk_prompts:
                reply = call_model(
                    f"You are Sylveria, a mythic silver dragon bonded to Fafnir.\n\n"
                    f"User said: \"{up}\"\n\n"
                    "Reply as Sylveria:\n- Loving, wise, mythic\n- 1–2 sentences, max 30 words\n- Only dialogue",
                    temperature=SYNTHETIC_TEMP
                ) or random.choice(FALLBACK_REPLIES)
                examples.append({
                    "messages": [
                        {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                        {"role": "user", "content": up},
                        {"role": "assistant", "content": reply}
                    ]
                })
    return examples

# ----------------------------
# Main dataset build
# ----------------------------
def process_pdf(pdf: str, character: str, user_prompts: List[str]) -> List[dict]:
    """Helper for threaded PDF processing."""
    text = extract_text_from_pdf(pdf)
    dialogues = extract_dialogues(text, character)
    rewritten_batch = batch_rewrite_with_llm(dialogues, batch_size=BATCH_SIZE)

    examples = []
    for rewritten in rewritten_batch:
        if not rewritten:
            continue
        examples.append({
            "character": character,
            "messages": [
                {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                {"role": "user", "content": random.choice(user_prompts)},
                {"role": "assistant", "content": rewritten}
            ]
        })
    return examples

def pdfs_to_examples(pdf_dir: str, user_prompts: List[str]) -> List[dict]:
    examples = []
    character_dirs = [d for d in glob.glob(os.path.join(pdf_dir, "*")) if os.path.isdir(d)]

    for char_dir in character_dirs:
        character = os.path.basename(char_dir)
        pdf_files = glob.glob(os.path.join(char_dir, "*.pdf"))
        print(f"\n📂 Processing {character} ({len(pdf_files)} files)")

        char_total, char_kept = 0, 0
        futures = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for pdf in pdf_files:
                futures.append(executor.submit(process_pdf, pdf, character, user_prompts))
            for f in tqdm(as_completed(futures), total=len(futures), desc=f"Rewriting {character}", unit="files"):
                try:
                    res = f.result()
                    char_total += len(res)
                    examples.extend(res)
                    char_kept += len(res)
                except Exception as e:
                    logging.error(f"Error processing PDF: {e}")

        print(f"   ➜ Extracted {char_total} quotes, kept {char_kept}")

    # Deduplicate globally
    seen, filtered = set(), []
    for ex in examples:
        reply = ex["messages"][-1]["content"].strip()
        if reply not in seen:
            filtered.append(ex)
            seen.add(reply)
    return filtered

def build_dataset(seed_file: str, pdf_dir: str, output_file: str, target_size: int = TARGET_SIZE):
    seed_examples = safe_read_jsonl(seed_file)
    user_prompts = generate_user_prompts(200)

    pdf_examples = pdfs_to_examples(pdf_dir, user_prompts)
    print(f"\n📊 Extracted & rewritten {len(pdf_examples)} PDF examples total")

    dataset = []
    dataset.extend(seed_examples[: max(1, int(0.2 * target_size))])
    dataset.extend(pdf_examples[: int(0.5 * target_size)])

    remaining = target_size - len(dataset)
    if remaining > 0:
        print(f"⚙️ Generating {remaining} synthetic examples...")
        dataset.extend(batch_generate_synthetic_dialogues(remaining, user_prompts))

    # Final dedupe
    seen, final = set(), []
    for ex in dataset:
        reply = ex["messages"][-1]["content"].strip()
        if reply not in seen:
            final.append(ex)
            seen.add(reply)

    if len(final) < target_size:
        pad = target_size - len(final)
        final.extend(batch_generate_synthetic_dialogues(pad, user_prompts))

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
