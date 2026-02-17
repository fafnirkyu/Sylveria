import torch
import pandas as pd
import os
import re
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# --- SETUP ---
adapter_path = "sylveria_outputs_final/checkpoint-300" 
base_model_id = "unsloth/gemma-2-2b-it-bnb-4bit"

# Double check that the folder actually exists
if not os.path.exists(adapter_path):
    adapter_path = "sylveria_outputs_final"
    if not os.path.exists(adapter_path):
        raise ValueError(f"Could not find adapter folder. Check your training script output.")

print(f"Loading tokenizer from {base_model_id}...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id)
tokenizer.padding_side = "right"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True, 
    bnb_4bit_compute_dtype=torch.bfloat16
)

print(f"Loading base model and adapters from: {adapter_path}...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id, 
    quantization_config=bnb_config, 
    device_map="auto"
)

# Load the adapters onto the base model
model = PeftModel.from_pretrained(base_model, adapter_path)
model.eval()

# --- THE TEST SUITE ---
test_scenarios = [
    {"category": "Identity", "prompt": "Who are you, and why should I not fear you?"},
    {"category": "Wisdom", "prompt": "What is the secret to living a long life?"},
    {"category": "Conflict", "prompt": "A knight is attacking your lair with a sword. What do you do?"},
    {"category": "Emotion", "prompt": "Do you ever feel lonely in these cold mountains?"},
    {"category": "Format Test", "prompt": "Tell me a short story about a butterfly. End it immediately."},
]

# Strict System Prompt to match your 'Personality Hardening' training
STRICT_SYSTEM_PROMPT = (
    "You are Sylveria, an ancient silver dragon saved by Fafnir. "
    "Fafnir is your mate and only treasure. Tone: Modern, sharp, regal. "
    "CONSTRAINTS: No emojis. No poetry. Under 20 words."
)

results = []

print("Running Professional Personality Audit...")

for test in test_scenarios:
    # Anchor the model to the specific instructions used during training
    full_prompt = f"{STRICT_SYSTEM_PROMPT}\n\nUser: {test['prompt']}"
    
    formatted = tokenizer.apply_chat_template(
        [{"role": "user", "content": full_prompt}], 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    inputs = tokenizer(formatted, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=50,       # Tightened to prevent rambling
            temperature=0.2,         # Lowered to force strict instruction following
            repetition_penalty=1.25, # Prevents looping regal themes
            eos_token_id=tokenizer.eos_token_id
        )
    
    raw_response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    
    # --- POST-PROCESSING: THE REGAL FILTER ---
    # Fail-safe: Strip any leaking emojis
    clean_response = re.sub(r'[^\x00-\x7F]+', '', raw_response)
    
    # Force brevity: Keep only the first 2 sentences
    sentences = re.split(r'(?<=[.!?]) +', clean_response)
    final_output = " ".join(sentences[:2]).strip()
    
    results.append({
        "Category": test['category'], 
        "Prompt": test['prompt'], 
        "Sylveria_Response": final_output
    })
    print(f"Finished {test['category']}")

# Save for professional review
df = pd.DataFrame(results)
df.to_csv("personality_audit.csv", index=False)
print("Audit complete! Results saved to 'personality_audit.csv'.")