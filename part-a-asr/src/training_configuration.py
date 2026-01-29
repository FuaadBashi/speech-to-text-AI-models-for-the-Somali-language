print("="*80)
print("🚀 STARTING FAST TRAINING (<1 HOUR)")
print("="*80)

# Optimized training arguments for speed
training_args = Seq2SeqTrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=24,  # ↑ Increased from 16
    gradient_accumulation_steps=2,   # ↑ Effective batch size = 48
    learning_rate=2e-5,               # ↑ Slightly higher for faster convergence
    warmup_steps=100,                 # ↓ Reduced from 200
    max_steps=800,                    # ↓ Reduced from 2000 (still effective)
    gradient_checkpointing=True,
    bf16=True,                        # ⚡ Better than fp16 on modern GPUs
    eval_strategy="steps",
    eval_steps=200,                   # ↓ Less frequent evals (faster)
    save_steps=200,                   # ↓ Less frequent saves
    logging_steps=25,                 # ↓ Less frequent logging
    predict_with_generate=True,
    generation_max_length=225,
    save_total_limit=2,               # ↓ Keep only 2 checkpoints
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    greater_is_better=False,
    push_to_hub=False,
    report_to=["tensorboard"],
    dataloader_num_workers=2,         # ⚡ Parallel data loading
    dataloader_pin_memory=True,       # ⚡ Faster GPU transfer
)

# Data collator
data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

# Trainer
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    data_collator=data_collator,
    compute_metrics=lambda pred: compute_metrics(pred, processor),
    tokenizer=processor.feature_extractor,
)

print("\n📊 Training configuration:")
print(f"  Batch size per device: {training_args.per_device_train_batch_size}")
print(f"  Gradient accumulation: {training_args.gradient_accumulation_steps}")
print(f"  Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
print(f"  Learning rate: {training_args.learning_rate}")
print(f"  Max steps: {training_args.max_steps}")
print(f"  BF16: {training_args.bf16}")
print(f"  Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
print(f"  Estimated time: 45-55 minutes ⏱️")
print("\n🏃 Training starting...\n")

# Train
trainer.train()

# Save final model
print("\n💾 Saving final model...")
final_model_path = "outputs/final_model"
trainer.save_model(final_model_path)
processor.save_pretrained(final_model_path)

print(f"✓ Model saved to: {final_model_path}")
print("\n✅ Training complete!")
print("="*80)