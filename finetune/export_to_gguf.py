# export_to_gguf.py
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL = "TheBloke/Mythomist-7B-GGUF"
LORA_DIR = "./lora-sylveria"
MERGED_DIR = "./sylveria-merged"

# Load base + LoRA
print("🔄 Loading base + LoRA...")
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, device_map="auto")
model = PeftModel.from_pretrained(model, LORA_DIR)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

# Merge LoRA weights into base
print("🧩 Merging LoRA weights...")
model = model.merge_and_unload()

# Save merged HF format
model.save_pretrained(MERGED_DIR)
tokenizer.save_pretrained(MERGED_DIR)

print(f"✅ Merged model saved to {MERGED_DIR}")

# ----------------------------
# Convert to GGUF
# ----------------------------
print("📦 Converting to GGUF...")
os.system(
    f"python3 -m transformers.models.llama.convert_llama_weights_to_gguf "
    f"--input_dir {MERGED_DIR} "
    f"--output_dir ./gguf "
    f"--model_size 7B "
    f"--use-f32"  # or use --use-f16 for smaller export
)

print("✅ GGUF model ready in ./gguf/")
