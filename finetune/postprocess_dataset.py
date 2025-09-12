import json, re, random, time, ast
import ollama
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# CONFIG
# ----------------------------
INPUT_FILE = "sylveria_dataset.jsonl"
OUTPUT_FILE = "sylveria_dataset_cleaned.jsonl"
PROMPT_FILE = "user_prompts.json"
MODEL_NAME = "mythomist-7b:Q5_K_M"  
GEN_MODEL = "mythomist-7b:Q5_K_M"           
REWRITE_TEMP = 0.6
PROMPT_TEMP = 0.7
RETRIES = 2
MAX_WORKERS = 6 
INJECT_PROMPTS = True 

# ----------------------------
# Fallbacks
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
BAD_WORDS = ["kylara", "t'bor", "orth", "wirenth", "canth", "weyr", "pern"]

MYTHIC_WORDS = [
    "wings", "scales", "silver", "eternal", "stars", "treasure", "soul",
    "flame", "bond", "heart", "sky", "flight", "fire", "ancient", "dragon"
]

FAFNIR_PROB = 0.35

# ----------------------------
# Helpers
# ----------------------------
def call_model(prompt: str, model=MODEL_NAME, temp=REWRITE_TEMP, retries=RETRIES) -> str:
    """Wrapper for Ollama chat with retries"""
    for _ in range(retries + 1):
        try:
            resp = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temp}
            )
            msg = resp.get("message", {}).get("content", "").strip()
            if msg:
                return msg
        except Exception:
            time.sleep(0.2)
    return ""

def clean_reply(text: str) -> str:
    """Filters replies based on length and content rules"""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", text.strip())
    words = t.split()
    if len(words) < 5 or len(words) > 30:
        return ""
    if any(bad in t.lower() for bad in BAD_WORDS):
        return ""
    if not t[0].isupper():
        return ""
    return t

# ----------------------------
# Style Enhancement
# ----------------------------
def adjust_sentence_length(text: str, target_range) -> str:
    words = text.split()
    if len(words) < target_range[0]:
        words += random.sample(MYTHIC_WORDS, k=min(2, len(MYTHIC_WORDS)))
    elif len(words) > target_range[1]:
        words = words[:target_range[1]]
    return " ".join(words).strip()

def enhance_reply(reply: str) -> str:
    if random.random() < FAFNIR_PROB and "Fafnir" not in reply:
        reply = reply.rstrip(".") + ", Fafnir."

    if not any(word in reply.lower() for word in MYTHIC_WORDS):
        reply += " " + random.choice(MYTHIC_WORDS)

    roll = random.random()
    if roll < 0.5:
        target = (6, 12)
    elif roll < 0.9:
        target = (13, 20)
    else:
        target = (21, 30)
    return adjust_sentence_length(reply, target)

# ----------------------------
# Rewrite Bad Replies
# ----------------------------
def rewrite_as_sylveria(line: str) -> str:
    prompt = (
        "Rewrite the following line in the voice of Sylveria, "
        "a mythic silver dragon bonded to Fafnir.\n\n"
        "- Speak directly to Fafnir\n"
        "- Loving, wise, mythic tone\n"
        "- 1–2 sentences, 5–30 words\n"
        "- No narration, no outside names, only dialogue\n\n"
        f"Line: {line}"
    )
    out = call_model(prompt)
    return clean_reply(out) or random.choice(FALLBACK_REPLIES)

# ----------------------------
# Prompt Generator
# ----------------------------
def generate_prompts(n=500):
    prompt = (
        f"Generate {n} short user prompts for a bonded, loving dragon companion.\n"
        "- Each 3–12 words\n"
        "- Intimate, mythic, poetic tone\n"
        "- Address the dragon directly\n"
        "- Return only a JSON array of strings"
    )
    try:
        resp = ollama.chat(
            model=GEN_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": PROMPT_TEMP}
        )
        raw = resp.get("message", {}).get("content", "").strip()

        # Remove possible ```json fences
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"```$", "", raw).strip()

        # Try parsing
        try:
            arr = json.loads(raw)
        except:
            try:
                arr = ast.literal_eval(raw)
            except:
                arr = re.findall(r'"([^"]{3,50})"', raw)

        if isinstance(arr, list) and arr:
            prompts = [p.strip() for p in arr if 3 <= len(p.split()) <= 12]
            return list(set(prompts))
    except Exception as e:
        print("Prompt generation failed:", e)
    return []

def save_prompts(prompts):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(prompts)} prompts to {PROMPT_FILE}")

# ----------------------------
# Dataset Processing
# ----------------------------
def process_dataset():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    to_rewrite, cleaned, seen = [], [], set()

    for ex in data:
        reply = ex["messages"][-1]["content"]
        fixed = clean_reply(reply)

        if fixed and fixed.lower() not in seen:
            enhanced = enhance_reply(fixed)
            ex["messages"][-1]["content"] = enhanced
            cleaned.append(ex)
            seen.add(enhanced.lower())
        else:
            to_rewrite.append((ex, reply))

    print(f"Found {len(to_rewrite)} bad replies to rewrite out of {len(data)}")

    rewritten = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(rewrite_as_sylveria, reply): ex for ex, reply in to_rewrite}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Rewriting"):
            ex = futures[fut]
            try:
                new_reply = fut.result()
            except Exception:
                new_reply = random.choice(FALLBACK_REPLIES)
            if new_reply.lower() not in seen:
                ex["messages"][-1]["content"] = enhance_reply(new_reply)
                rewritten.append(ex)
                seen.add(new_reply.lower())

    all_cleaned = cleaned + rewritten

    # Optional: Inject generated prompts
    if INJECT_PROMPTS:
        prompts = generate_prompts(300)
        if prompts:
            for p in prompts:
                all_cleaned.append({
                    "messages": [
                        {"role": "system", "content": "You are Sylveria — a mythic, silver dragon bonded to Fafnir. Only speak as her."},
                        {"role": "user", "content": p},
                        {"role": "assistant", "content": random.choice(FALLBACK_REPLIES)}
                    ]
                })
            print(f"Injected {len(prompts)} generated user prompts into dataset")
            save_prompts(prompts)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in all_cleaned:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\nCleaned dataset saved to {OUTPUT_FILE}")
    print(f"   Total: {len(all_cleaned)} examples")
    print(f"   Fixed: {len(rewritten)} | Already good: {len(cleaned)}")

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    process_dataset()

