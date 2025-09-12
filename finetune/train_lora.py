import os
import json
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import random

# ----------------------------
# Config
# ----------------------------
BASE_MODEL = "Gryphe/Mythomist-7B"
DATASET_PATH = "sylveria_dataset_cleaned.jsonl"  
PROMPTS_PATH = "user_prompts.json"               
OUTPUT_DIR = "./lora-sylveria"
BATCH_SIZE = 2
EPOCHS = 3
LR = 2e-4
MAX_SEQ_LEN = 512

# ----------------------------
# Load dataset
# ----------------------------
dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

# Load generated prompts
if os.path.exists(PROMPTS_PATH):
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        DIVERSIFIED_PROMPTS = json.load(f)
else:
    DIVERSIFIED_PROMPTS = []
print(f" Loaded {len(DIVERSIFIED_PROMPTS)} extra prompts")

# ----------------------------
# Tokenizer & Model
# ----------------------------
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=False)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# BitsAndBytes 4-bit quantization (QLoRA setup)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16, 
)

print("🔄 Loading model in 4-bit...")
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    dtype=torch.bfloat16,
    device_map="auto",
)

# Prepare model for QLoRA
model = prepare_model_for_kbit_training(model)

# Apply LoRA
config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, config)

# ----------------------------
# Tokenization
# ----------------------------
def tokenize_fn(example):
    # Optionally replace user prompt with a diversified one
    user_prompt = example["messages"][1]["content"].strip()
    if DIVERSIFIED_PROMPTS and random.random() < 0.5:
        user_prompt = random.choice(DIVERSIFIED_PROMPTS)

    # Flatten conversation
    text = (
        example["messages"][0]["content"].strip()  # system
        + "\n" + user_prompt                       # user
        + "\n" + example["messages"][2]["content"].strip()  # assistant
    )

    tokenized = tokenizer(
        text,
        truncation=True,
        max_length=MAX_SEQ_LEN,
        padding="max_length",
        return_tensors="pt",
    )
    tokenized["labels"] = tokenized["input_ids"].clone()
    return {k: v.squeeze(0) for k, v in tokenized.items()}

tokenized_dataset = dataset.map(tokenize_fn, batched=False)

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
)

# ----------------------------
# Training
# ----------------------------
args = TrainingArguments(
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=8,
    num_train_epochs=EPOCHS,
    learning_rate=LR,
    output_dir=OUTPUT_DIR,
    save_strategy="epoch",
    logging_steps=10,
    bf16=True,
    optim="paged_adamw_8bit",
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

print("Starting training...")
trainer.train()

# Save LoRA weights
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("LoRA fine-tuning complete. Model saved to", OUTPUT_DIR)
