import torch
import evaluate
import re
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

# Configuration
MODEL_ID = "openai/whisper-small"
DATASET_NAME = "skydheere/soomali-asr-dataset"
OUTPUT_DIR = "outputs/checkpoints/whisper_small_somali_final"
LANGUAGE = "somali"

set_seed(42)

print("="*80)
print("🤖 TRAINING SETUP (FAST MODE)")
print("="*80)
print(f"Model: {MODEL_ID}")
print(f"Dataset: {DATASET_NAME}")
print(f"Language: {LANGUAGE}")
print(f"Target: <1 hour training")
print("="*80)

# Text normalization function
def normalize_text(text: str) -> str:
    """Strict normalization for WER calculation"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Metrics computation
wer_metric = evaluate.load("wer")

def compute_metrics(pred, processor):
    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token
    label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

    # Decode
    pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    # Normalize
    pred_str_norm = [normalize_text(p) for p in pred_str]
    label_str_norm = [normalize_text(l) for l in label_str]

    # Calculate WER
    wer = wer_metric.compute(predictions=pred_str_norm, references=label_str_norm)
    return {"wer": wer}

# Data collator
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any

    def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        # Extract input features
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # Extract labels
        label_features = [{"input_ids": feature["labels"]} for feature in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Mask padding tokens
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        # Remove BOS token if present
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch

# Load processor and model
print("\n📦 Loading processor and model...")
processor = WhisperProcessor.from_pretrained(MODEL_ID, language=LANGUAGE, task="transcribe")
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)

# Configure for Somali
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language=LANGUAGE, task="transcribe")
model.config.suppress_tokens = []
model.config.use_cache = False

print(f"✓ Model loaded: {MODEL_ID}")
print(f"✓ Forced decoder IDs: {model.config.forced_decoder_ids}")

# Load and prepare dataset
print("\n📥 Loading dataset...")
dataset = load_dataset(DATASET_NAME)
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

print(f"✓ Train samples: {len(dataset['train'])}")
print(f"✓ Validation samples: {len(dataset['validation'])}")

def prepare_dataset(batch):
    """Prepare audio features and labels"""
    audio = batch["audio"]

    # Extract audio features
    batch["input_features"] = processor.feature_extractor(
        audio["array"],
        sampling_rate=16000
    ).input_features[0]

    # Tokenize transcription
    batch["labels"] = processor.tokenizer(
        batch["transcription"].lower().strip()
    ).input_ids

    return batch

print("\n🔄 Preprocessing dataset...")
dataset = dataset.map(
    prepare_dataset,
    remove_columns=dataset["train"].column_names,
    num_proc=4
)

print("✓ Dataset preprocessed")
print("\n✅ Training setup complete!")