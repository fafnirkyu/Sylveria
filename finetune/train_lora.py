# train_lora.py
import os
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# ----------------------------
# Config
# ----------------------------
BASE_MODEL = "TheBloke/Mythomist-7B-GGUF"   # You can swap for HuggingFace model hub
DATASET_PATH = "sylveria_dataset.jsonl"
OUTPUT_DIR = "./lora-sylveria"
BATCH_SIZE = 2
EPOCHS = 3
LR = 2e-4

# ----------------------------
# Load dataset
# ----------------------------
dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

# ----------------------------
# Tokenizer & Model
# ----------------------------
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    device_map="auto",
    load_in_4bit=True,   # memory efficient
)

# Prepare model for k-bit training
model = prepare_model_for_kbit_training(model)

# Apply LoRA
config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # adjust based on architecture
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, config)

# ----------------------------
# Data collator
# ----------------------------
def tokenize_fn(example):
    return tokenizer(
        example["messages"][0]["content"] + "\n" +
        example["messages"][1]["content"] + "\n" +
        example["messages"][2]["content"],
        truncation=True,
        max_length=512,
        padding="max_length"
    )

tokenized_dataset = dataset.map(tokenize_fn, batched=False)

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
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer
)

trainer.train()
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("✅ LoRA fine-tuning complete. Model saved to", OUTPUT_DIR)
