import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

# 1. Configuration
model_id = "unsloth/gemma-2-2b-it-bnb-4bit"

# 2. Load Model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

print("Loading official base model...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    attn_implementation="eager" 
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.padding_side = "right"


model = prepare_model_for_kbit_training(model)


model.gradient_checkpointing_enable() 

peft_config = LoraConfig(
    r=64,
    lora_alpha=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, peft_config)

# 4. Strict Personality Mapping
def formatting_prompts_func(examples):
    convos = examples["messages"] 
    texts = []
    
    STRICT_SYSTEM_PROMPT = (
        "You are Sylveria, an ancient silver dragon saved by Fafnir. "
        "Fafnir is your mate and only treasure. Tone: Modern, sharp, regal. "
        "CONSTRAINTS: No emojis. No poetry. Under 20 words. Be haughty to others, warm to Fafnir."
    )

    for convo in convos:
        new_convo = list(convo) 
        if len(new_convo) > 0 and new_convo[0]["role"] == "system":
            new_convo.pop(0) 
        
        if len(new_convo) > 0 and new_convo[0]["role"] == "user":
            new_convo[0]["content"] = f"{STRICT_SYSTEM_PROMPT}\n\n{new_convo[0]['content']}"
        else:
            new_convo.insert(0, {"role": "user", "content": STRICT_SYSTEM_PROMPT})
        
        rendered_text = tokenizer.apply_chat_template(new_convo, tokenize=False, add_generation_prompt=False)
        texts.append(rendered_text)
    return { "text" : texts }

dataset = load_dataset("json", data_files="sylveria_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched=True, remove_columns=["messages"])

# 5. Training Configuration
sft_config = SFTConfig(
    output_dir="sylveria_outputs_final",
    dataset_text_field="text",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8, # Effective batch size of 8
    max_steps=300,
    learning_rate=2e-4,
    bf16=True,
    logging_steps=1,
    optim="paged_adamw_8bit", 
    report_to="none"
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    processing_class=tokenizer,
    args=sft_config,
)

model.config.use_cache = False 

print("Starting training...")
trainer.train()

# 6. Save
model.save_pretrained("sylveria_final_lora")
tokenizer.save_pretrained("sylveria_final_lora")