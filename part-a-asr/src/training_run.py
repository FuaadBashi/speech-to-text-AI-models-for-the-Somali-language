# ============================================================================
# FIXED EVALUATION - COPY THIS ENTIRE CELL
# ============================================================================
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
print("FIXED EVALUATION WITH ANTI-REPETITION")
print("="*80)

# Load model
print("\n📦 Loading model...")
MODEL_PATH = "outputs/final_model"
processor = WhisperProcessor.from_pretrained(MODEL_PATH)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH)

# Configure for Somali
forced_decoder_ids = processor.get_decoder_prompt_ids(language="somali", task="transcribe")
model.config.forced_decoder_ids = forced_decoder_ids
print(f"✓ Forced decoder IDs: {forced_decoder_ids}")

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
model.eval()
print(f"✓ Model on: {device}")

# Load audio
print("\n📥 Loading verification clip...")
full_audio, sr = librosa.load("outputs/verification/verification.wav", sr=16000)

with open("outputs/verification/verification_manifest.json", "r") as f:
    manifest_data = json.load(f)
segments = manifest_data.get("segments", manifest_data)
print(f"✓ Loaded {len(segments)} segments")

# Normalize function
normalizer = BasicTextNormalizer()

# Evaluate
print(f"\n🚀 Evaluating with FIXED generation...")
print("   ✓ no_repeat_ngram_size=3 (PREVENTS REPETITION)")
print("   ✓ Skip silent segments")
print()

predictions = []
references = []
skipped = 0

for seg in tqdm(segments, desc="Processing"):
    # Extract audio segment
    start_idx = int(seg.get("start_sec", seg.get("start", 0)) * sr)
    end_idx = int(seg.get("end_sec", seg.get("end", 0)) * sr)
    chunk = full_audio[start_idx:end_idx]

    # Skip silent/very short
    duration = len(chunk) / sr
    energy = np.sqrt(np.mean(chunk**2))

    if duration < 0.3 or energy < 0.01:
        pred_norm = ""
        skipped += 1
    else:
        # Process
        inputs = processor(chunk, return_tensors="pt", sampling_rate=sr).input_features.to(device)

        # Generate with ANTI-REPETITION
        with torch.no_grad():
            ids = model.generate(
                inputs,
                forced_decoder_ids=forced_decoder_ids,
                max_new_tokens=225,
                min_new_tokens=1,
                num_beams=5,
                length_penalty=1.0,
                no_repeat_ngram_size=3,    # ← CRITICAL: Stops "sug sug sug..."
                early_stopping=True,
            )

        transcription = processor.batch_decode(ids, skip_special_tokens=True)[0]
        pred_norm = normalizer(transcription)

    # Get reference
    ref_text = seg.get("text_normalized") or seg.get("text", "")
    ref_norm = normalizer(ref_text) if not seg.get("text_normalized") else ref_text

    predictions.append(pred_norm)
    references.append(ref_norm)

print(f"\n✓ Skipped {skipped} silent segments")

# Compute WER
print("\n📊 Computing WER...")
valid_pairs = [(p, r) for p, r in zip(predictions, references) if r]
predictions_valid = [p for p, r in valid_pairs]
references_valid = [r for p, r in valid_pairs]

full_pred = " ".join(predictions_valid)
full_ref = " ".join(references_valid)

wer_full = wer(full_ref, full_pred)

# Results
print(f"\n{'='*80}")
print("FINAL RESULTS")
print("="*80)
print(f"Segments: {len(valid_pairs)}/{len(segments)} (skipped {skipped})")
print(f"Words predicted: {len(full_pred.split())}")
print(f"Words reference: {len(full_ref.split())}")
print(f"Coverage: {len(full_pred.split())/len(full_ref.split())*100:.1f}%")
print(f"\n✨ WER: {wer_full*100:.2f}%")
print("="*80)

if wer_full <= 0.20:
    print(f"\n🎉 ✅ TARGET ACHIEVED! WER {wer_full*100:.1f}% ≤ 20%")
else:
    print(f"\n⚠️  WER {wer_full*100:.1f}% is above 20%")

# Show samples
print(f"\n📝 First 3 segments:")
for i in range(min(3, len(valid_pairs))):
    pred, ref = valid_pairs[i]
    seg_wer = wer(ref, pred) if ref and pred else 0
    print(f"\n{i+1}. WER: {seg_wer*100:.1f}%")
    print(f"   REF: {ref[:70]}...")
    print(f"   HYP: {pred[:70]}...")

print("\n" + "="*80)
