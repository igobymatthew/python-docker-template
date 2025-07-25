# %%
import pandas as pd
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.metrics import accuracy_score, f1_score
import torch

# %%
# Load data from CSV files placed in the working directory
# Expected files: train.csv with columns ['text', 'label']
dataset = load_dataset("csv", data_files={"train": "train.csv", "validation": "validation.csv"})

# %%
# Initialize tokenizer and model
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=dataset['train'].features['label'].num_classes)

# %%
# Tokenization function
def tokenize(batch):
    return tokenizer(batch["text"], padding=True, truncation=True)

# %%
# Tokenize datasets
tokenized = dataset.map(tokenize, batched=True)

# %%
# Compute metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="macro"),
    }

# %%
# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    num_train_epochs=1,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    save_total_limit=1,
)

# %%
# Trainer setup
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    compute_metrics=compute_metrics,
)

# %%
# Train the model
trainer.train()

# %%
# Save the model
trainer.save_model("./model")

