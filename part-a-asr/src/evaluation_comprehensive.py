#!/usr/bin/env python3
"""
SIMPLE EVALUATION - Uses outputs/final_model directly
"""

import json
import os
import torch
import librosa
import numpy as np
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from transformers.models.whisper.english_normalizer import BasicTextNormalizer
from jiwer import wer
from tqdm import tqdm

print("="*80)
print("VERIFICATION EVALUATION - USING FINAL MODEL")
print("="*80)

# Configuration
MODEL_PATH = "outputs/final_model"  # Use final model directly
WAV_PATH = "outputs/verification/verification.wav"
MANIFEST_PATH = "outputs/verification/verification_manifest.json"

# Text normalization
normalizer = BasicTextNormalizer()
def normalize(text):
    return normalizer(text)

# =============================================================================
# LOAD MODEL
# =============================================================================
print(f"\n📦 Loading model from: {MODEL_PATH}")

if not os.path.exists(MODEL_PATH):
    raise ValueError(f"Model not found at: {MODEL_PATH}")

processor = WhisperProcessor.from_pretrained(MODEL_PATH)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH)
print("✓ Model loaded")

# Set forced decoder IDs
forced_decoder_ids = processor.get_decoder_prompt_ids(language="somali", task="transcribe")
print(f"✓ Forced decoder IDs: {forced_decoder_ids}")
model.config.forced_decoder_ids = forced_decoder_ids

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
model.eval()
print(f"✓ Model on: {device}")

# =============================================================================
# LOAD AUDIO
# =============================================================================
print(f"\n📥 Loading audio...")
full_audio, sr = librosa.load(WAV_PATH, sr=16000)
print(f"✓ Loaded {len(full_audio)/sr:.1f}s")

with open(MANIFEST_PATH, "r") as f:
    manifest_data = json.load(f)
segments = manifest_data.get("segments", manifest_data)
print(f"✓ Loaded {len(segments)} segments")

# =============================================================================
# EVALUATE
# =============================================================================
print(f"\n🚀 Evaluating {len(segments)} segments...")
print("   Settings: no_repeat_ngram_size=3, skip silent, max_new_tokens=225\n")

predictions = []
references = []
skipped = 0

for seg in tqdm(segments, desc="Processing"):
    # Extract audio
    start_idx = int(seg.get("start_sec", seg.get("start", 0)) * sr)
    end_idx = int(seg.get("end_sec", seg.get("end", 0)) * sr)
    chunk = full_audio[start_idx:end_idx]

    # Skip silent
    duration = len(chunk) / sr
    energy = np.sqrt(np.mean(chunk**2))

    if duration < 0.3 or energy < 0.01:
        pred_norm = ""
        skipped += 1
    else:
        # Transcribe
        inputs = processor(chunk, return_tensors="pt", sampling_rate=sr).input_features.to(device)

        with torch.no_grad():
            ids = model.generate(
                inputs,
                forced_decoder_ids=forced_decoder_ids,
                max_new_tokens=225,
                min_new_tokens=1,
                num_beams=5,
                length_penalty=1.0,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )

        transcription = processor.batch_decode(ids, skip_special_tokens=True)[0]
        pred_norm = normalize(transcription)

    # Get reference
    ref_text = seg.get("text_normalized") or seg.get("text", "")
    ref_norm = normalize(ref_text) if not seg.get("text_normalized") else ref_text

    predictions.append(pred_norm)
    references.append(ref_norm)

print(f"\n⚠️  Skipped {skipped} silent segments")

# =============================================================================
# COMPUTE WER
# =============================================================================
print(f"\n📊 Computing WER...")

valid_pairs = [(p, r) for p, r in zip(predictions, references) if r]
predictions_valid = [p for p, r in valid_pairs]
references_valid = [r for p, r in valid_pairs]

full_pred = " ".join(predictions_valid)
full_ref = " ".join(references_valid)

wer_full = wer(full_ref, full_pred) if full_ref else float('inf')

segment_wers = []
for pred, ref in zip(predictions_valid, references_valid):
    if ref and pred:
        try:
            segment_wers.append(wer(ref, pred))
        except:
            pass

wer_avg = np.mean(segment_wers) if segment_wers else float('inf')

# =============================================================================
# RESULTS
# =============================================================================
print(f"\n{'='*80}")
print("RESULTS")
print("="*80)
print(f"Model: {MODEL_PATH}")
print(f"\nSegments: {len(valid_pairs)}/{len(segments)} (skipped {skipped})")
print(f"Words: {len(full_pred.split())}/{len(full_ref.split())} ({len(full_pred.split())/len(full_ref.split())*100:.1f}% coverage)")
print(f"\nWER (full): {wer_full*100:.2f}%")
print(f"WER (avg):  {wer_avg*100:.2f}%")
print("="*80)

if wer_full <= 0.20:
    print(f"\n🎉 ✅ TARGET ACHIEVED!")
    print(f"   WER {wer_full*100:.1f}% ≤ 20%")
    print(f"   Your model is ready!")
elif wer_full <= 0.30:
    print(f"\n✓ Good: {wer_full*100:.1f}%")
else:
    print(f"\n⚠️  WER: {wer_full*100:.1f}%")

# Samples
print(f"\n📝 Samples:")
for i in range(min(5, len(valid_pairs))):
    pred, ref = valid_pairs[i]
    seg_wer = wer(ref, pred) if ref and pred else 0
    print(f"\n{i+1}. WER: {seg_wer*100:.1f}%")
    print(f"   REF: {ref[:70]}...")
    print(f"   HYP: {pred[:70]}...")

# Save
results = {
    "model": MODEL_PATH,
    "wer_full": float(wer_full),
    "wer_avg": float(wer_avg),
    "segments": len(valid_pairs),
    "skipped": skipped,
    "coverage": len(full_pred.split()) / len(full_ref.split()) if len(full_ref.split()) > 0 else 0,
    "target_achieved": wer_full <= 0.20,
}

output_path = "outputs/verification/evaluation_results.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Saved: {output_path}")
print("="*80)
print("✅ DONE!")
print("="*80)