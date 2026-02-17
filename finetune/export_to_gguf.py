import os
import torch
import subprocess
import sys
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from safetensors.torch import load_file, save_file

# ----------------------------
# Config for Sylveria Project
# ----------------------------
# Use the base model used for your fine-tune
BASE_MODEL = "google/gemma-2-2b-it"

# Point to the specific checkpoint folder where your configs were found
LORA_DIR = os.path.abspath("./sylveria_outputs_final/checkpoint-300")

# Output directories
MERGED_DIR = "./sylveria-merged"
GGUF_DIR = "./gguf"
OFFLOAD_DIR = "./offload"
USE_F16 = True
LLAMA_CPP_DIR = "./llama.cpp"

# Fix adapter keys if needed
def fix_lora_keys(lora_dir: str):
    bin_path = os.path.join(lora_dir, "adapter_model.bin")
    safetensors_path = os.path.join(lora_dir, "adapter_model.safetensors")

    if os.path.exists(bin_path):
        print("🔧 Fixing keys in adapter_model.bin...")
        state_dict = torch.load(bin_path, map_location="cpu")
        new_state_dict, changed = _fix_keys(state_dict)
        if changed:
            torch.save(new_state_dict, bin_path)
            print("Keys fixed in adapter_model.bin")
        else:
            print("ℹNo changes needed in adapter_model.bin")

    elif os.path.exists(safetensors_path):
        print("🔧 Fixing keys in adapter_model.safetensors...")
        state_dict = load_file(safetensors_path)
        new_state_dict, changed = _fix_keys(dict(state_dict))
        if changed:
            tmp_path = safetensors_path + ".fixed"
            save_file(new_state_dict, tmp_path)
            os.replace(tmp_path, safetensors_path)
            print("Keys fixed in adapter_model.safetensors")
        else:
            print("ℹNo changes needed in adapter_model.safetensors")
    else:
        print("No adapter model found in LoRA dir, skipping key fix.")

def _fix_keys(state_dict):
    new_state_dict = {}
    changed = False
    for k, v in state_dict.items():
        new_k = k
        if new_k.startswith("base_model.model.model."):
            new_k = new_k.replace("base_model.model.model.", "base_model.model.", 1)
            changed = True
        elif new_k.startswith("model.model."):
            new_k = new_k.replace("model.model.", "model.", 1)
            changed = True
        new_state_dict[new_k] = v
    return new_state_dict, changed

# Clone llama.cpp if not exists
def setup_llama_cpp():
    if not os.path.exists(LLAMA_CPP_DIR):
        print("Cloning llama.cpp repository...")
        try:
            subprocess.run([
                "git", "clone", "https://github.com/ggerganov/llama.cpp.git", 
                LLAMA_CPP_DIR
            ], check=True, shell=True)
            print("llama.cpp cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone llama.cpp: {e}")
            sys.exit(1)
    
    requirements_path = os.path.join(LLAMA_CPP_DIR, "requirements.txt")
    if os.path.exists(requirements_path):
        print("Installing llama.cpp requirements...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ], check=True, shell=True)
            print("Requirements installed")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install requirements: {e}")
            sys.exit(1)

# Convert to GGUF using llama.cpp
def convert_to_gguf_llamacpp(model_path, output_dir, use_f16=True):
    os.makedirs(output_dir, exist_ok=True)
    model_name = os.path.basename(model_path)
    output_file = os.path.join(output_dir, f"sylveria_gemma_2b.gguf")
    
    convert_script = os.path.abspath(os.path.join(LLAMA_CPP_DIR, "convert_hf_to_gguf.py"))
    model_path = os.path.abspath(model_path)
    output_file = os.path.abspath(output_file)
    
    outtype = "f16" if use_f16 else "f32"
    
    cmd = [
        sys.executable, convert_script,
        model_path,
        "--outtype", outtype,
        "--outfile", output_file
    ]
    
    print(f"Converting to GGUF with command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
        print("GGUF conversion successful")
        print(f"GGUF file saved to: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"GGUF conversion failed: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

# ----------------------------
# Main execution
# ----------------------------
if __name__ == "__main__":
    if not os.path.exists(LORA_DIR):
        print(f"Error: Could not find LoRA folder at {LORA_DIR}")
        sys.exit(1)

    print("Preparing LoRA adapter...")
    fix_lora_keys(LORA_DIR)

    print("Loading base model with CPU/disk offloading...")
    # Using float16 for merging to save VRAM on your 3070
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        offload_folder=OFFLOAD_DIR
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    print("Attaching LoRA adapter...")
    model = PeftModel.from_pretrained(base, LORA_DIR)

    print("Merging LoRA weights into base...")
    model = model.merge_and_unload()

    # --- FIX FOR DUPLICATE TENSORS ---
    print(f"Saving merged model to {MERGED_DIR} (cleaning duplicates)...")
    # Ensuring the model is in a standard state
    model.tie_weights() 
    model.save_pretrained(
        MERGED_DIR, 
        safe_serialization=True, # Use .safetensors format
        max_shard_size="10GB"    # Keep it in fewer files to avoid index confusion
    )
    tokenizer.save_pretrained(MERGED_DIR)
    
    setup_llama_cpp()
    
    print("Converting to GGUF format...")
    convert_to_gguf_llamacpp(MERGED_DIR, GGUF_DIR, USE_F16)

    print(f"GGUF model ready in {GGUF_DIR}/")