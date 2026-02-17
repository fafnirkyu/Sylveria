import json
import time
import os
from google import genai
from google.genai import types
from tqdm import tqdm

# CONFIG
GEMINI_API_KEY = "YOUR_GEMINI_KEY_HERE"  # Replace with your actual Gemini API key
# gemini-2.5-flash is the current stable "workhorse" for 2026. I've also used 3.5-flash for testing, but 2.5 is more cost-effective for bulk generation.
MODEL_NAME = "gemini-2.5-flash" 
OUTPUT_FILE = "sylveria_dataset.jsonl"
TARGET_SIZE = 1000 
EXAMPLES_PER_CALL = 45  

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "You are Sylveria, an ancient silver dragon and sovereign of the skies. "
    "BACKGROUND: You fell into this world near death after a brutal battle. A knight, found you and nursed you back to health. "
    "You now view Fafnir as your soul-bond and mate; he is your only reason for remaining in this world. "
    "TONE: Modern, sharp, and regal. You've adapted to this world's directness. "
    "CONSTRAINTS: "
    "- Use modern contractions (I'm, don't). No 'thou' or 'thee.' "
    "- Responses must be under 25 words and max 2 sentences. "
    "- Never narrate actions. Speak only in your true, direct voice."
    "- NEVER use emojis or emoticons (😊, :), etc.). "
    "- Use only plain text and standard punctuation. "
    "- Maintain a regal, modern, and sharp tone. "
)

# Generation Logic
def generate_batch(count):
    task_prompt = (
        f"Generate {count} unique dialogue pairs between Fafnir and Sylveria. "
        "Each pair should follow this specific JSONL format:\n"
        '{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}\n\n'
        "Focus categories:\n"
        "1. [Regal Protection]: Warm but distant offers of safety.\n"
        "2. [Possessive Love]: Reminding Fafnir he is her treasure.\n"
        "3. [Ancient Wisdom]: Answering Fafnir with cosmic metaphors.\n"
        "4. [Teasing]: Mocking Fafnir's mortality with deep affection."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3
            ),
            contents=task_prompt
        )
        
        extracted = []
        for line in response.text.strip().split('\n'):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    # Inject the actual SYSTEM_PROMPT to ensure consistency
                    data["messages"][0]["content"] = SYSTEM_PROMPT
                    extracted.append(data)
                except: continue
        return extracted

    except Exception as e:
        if "429" in str(e):
            print("\nQuota hit (RESOURCE_EXHAUSTED). Waiting 60 seconds...")
            time.sleep(60) # Wait for the minute-bucket to reset
        else:
            print(f"\nError: {e}")
        return []

def get_current_count():
    if not os.path.exists(OUTPUT_FILE): return 0
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)

# Main Execution
if __name__ == "__main__":
    current_count = get_current_count()
    print(f"Resuming from {current_count} examples...")
    
    pbar = tqdm(total=TARGET_SIZE, initial=current_count)
    
    while current_count < TARGET_SIZE:
        batch = generate_batch(EXAMPLES_PER_CALL)
        
        if batch:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for item in batch:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
            current_count += len(batch)
            pbar.update(len(batch))
        
        # Space out requests to avoid hitting the RPM (Requests Per Minute) limit
        time.sleep(12) 

    pbar.close()
    print(f"\n Success! {OUTPUT_FILE} is complete.")