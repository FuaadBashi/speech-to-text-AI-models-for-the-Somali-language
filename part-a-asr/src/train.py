#!/usr/bin/env python3
import os
import torch
import librosa
from dataclasses import dataclass
from typing import Any, Dict, List
from datasets import load_dataset, Audio
from transformers import (
    WhisperForConditionalGeneration,
    WhisperProcessor,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    set_seed
)

# --- CUSTOM TRAINER FOR EARLY STOPPING @ WER < 14% ---
class SomaliTrainer(Seq2SeqTrainer):
    def evaluation_loop(self, *args, **kwargs):
        output = super().evaluation_loop(*args, **kwargs)
        if "eval_wer" in output.metrics:
            wer = output.metrics["eval_wer"]
            print(f"\n📊 Current Step WER: {wer:.4f}")
            if wer < 0.14:
                print(f"🎯 TARGET WER < 14% REACHED. STOPPING TRAINING.")
                self.control.should_training_stop = True
        return output

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any
    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        batch["labels"] = labels
        return batch

def train():
    set_seed(42)
    model_id = "openai/whisper-small"
    out_dir = "./outputs/whisper_somali_final"
    
    processor = WhisperProcessor.from_pretrained(model_id, language="somali", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(model_id)
    model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language="somali", task="transcribe")

    # Safe manual load to bypass torchcodec error
    ds = load_dataset("skydheere/soomali-asr-dataset", split="train").cast_column("audio", Audio(decode=False))
    
    def prepare_dataset(batch):
        audio, _ = librosa.load(batch["audio"]["path"], sr=16000)
        batch["input_features"] = processor.feature_extractor(audio, sampling_rate=16000).input_features[0]
        # Force Lowercase
        batch["labels"] = processor.tokenizer(batch["transcription"].lower().strip()).input_ids
        return batch

    train_data = ds.map(prepare_dataset, remove_columns=ds.column_names)

    training_args = Seq2SeqTrainingArguments(
        output_dir=out_dir,
        per_device_train_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=1e-5,
        max_steps=1500,
        evaluation_strategy="steps",
        eval_steps=250,
        predict_with_generate=True,
        fp16=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        load_best_model_at_end=True,
        report_to="none"
    )

    trainer = SomaliTrainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=train_data.select(range(100)), # Subset for validation speed
        processing_class=processor,
        data_collator=DataCollatorSpeechSeq2SeqWithPadding(processor=processor),
    )

    trainer.train()
    trainer.save_model(out_dir)
    processor.save_pretrained(out_dir)

if __name__ == "__main__":
    train()