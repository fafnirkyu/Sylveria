import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# 1. Setup Paths
# Replace this with the actual folder name where your adapters are saved
adapter_path = "./sylveria_final_lora" 
base_model_id = "unsloth/gemma-2-2b-it-bnb-4bit"

# 2. Load Tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(adapter_path)

# 3. Load Base Model in 4-bit
print("Loading base model...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
)

base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# 4. Load LoRA Adapters
print("Attaching LoRA adapters...")
model = PeftModel.from_pretrained(base_model, adapter_path)
model.eval() # Set to evaluation mode

# 5. Test Function
def generate_response(user_input, system_prompt=""):
    # Replicate the prompt formatting used during training
    # Merge system prompt into user input for Gemma compatibility
    if system_prompt:
        combined_input = f"{system_prompt}\n\n{user_input}"
    else:
        combined_input = user_input

    messages = [{"role": "user", "content": combined_input}]
    
    # Apply the chat template
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode only the new tokens
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    return response

# 6. Start Chatting
print("\n--- Model Ready! Type 'exit' to stop. ---")
while True:
    user_text = input("User: ")
    if user_text.lower() == 'exit':
        break
    
    # You can include your specific character/system instructions here
    ans = generate_response(user_text, system_prompt="You are a helpful assistant.")
    print(f"\nModel: {ans}\n")