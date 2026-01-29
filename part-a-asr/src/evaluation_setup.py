#!/usr/bin/env python3
"""
COMPREHENSIVE EVALUATION - Works with any jiwer version
Shows all segments + word-level TP/FP/FN statistics
"""

import json
import os
import torch
import librosa
import numpy as np
import pandas as pd
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from transformers.models.whisper.english_normalizer import BasicTextNormalizer
from jiwer import wer
from tqdm import tqdm
import difflib

print("="*80)
print("COMPREHENSIVE EVALUATION - ALL SEGMENTS + STATISTICS")
print("="*80)

# Load model
print("\n📦 Loading model...")
MODEL_PATH = "outputs/final_model"
processor = WhisperProcessor.from_pretrained(MODEL_PATH)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH)

forced_decoder_ids = processor.get_decoder_prompt_ids(language="somali", task="transcribe")
model.config.forced_decoder_ids = forced_decoder_ids

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
model.eval()
print(f"✓ Model on: {device}")

# Load audio
print("📥 Loading verification clip...")
full_audio, sr = librosa.load("outputs/verification/verification.wav", sr=16000)

with open("outputs/verification/verification_manifest.json", "r") as f:
    manifest_data = json.load(f)
segments = manifest_data.get("segments", manifest_data)
print(f"✓ Loaded {len(segments)} segments")

normalizer = BasicTextNormalizer()

def compute_word_stats(reference, hypothesis):
    """Compute word-level statistics using difflib"""
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)

    hits = 0
    substitutions = 0
    deletions = 0
    insertions = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            hits += (i2 - i1)
        elif tag == 'replace':
            substitutions += max(i2 - i1, j2 - j1)
        elif tag == 'delete':
            deletions += (i2 - i1)
        elif tag == 'insert':
            insertions += (j2 - j1)

    return {'hits': hits, 'substitutions': substitutions, 'deletions': deletions, 'insertions': insertions}

# Evaluate ALL segments
print(f"\n🚀 Evaluating ALL {len(segments)} segments...\n")

all_results = []
predictions = []
references = []
skipped = 0

for i, seg in enumerate(tqdm(segments, desc="Processing")):
    start_idx = int(seg.get("start_sec", seg.get("start", 0)) * sr)
    end_idx = int(seg.get("end_sec", seg.get("end", 0)) * sr)
    chunk = full_audio[start_idx:end_idx]

    duration = len(chunk) / sr
    energy = np.sqrt(np.mean(chunk**2))

    if duration < 0.3 or energy < 0.01:
        pred_norm = ""
        skipped += 1
    else:
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
        pred_norm = normalizer(transcription)

    ref_text = seg.get("text_normalized") or seg.get("text", "")
    ref_norm = normalizer(ref_text) if not seg.get("text_normalized") else ref_text

    predictions.append(pred_norm)
    references.append(ref_norm)

    if ref_norm:
        seg_wer = wer(ref_norm, pred_norm) if pred_norm else 1.0
        word_stats = compute_word_stats(ref_norm, pred_norm)

        all_results.append({
            "segment_id": i + 1,
            "duration_sec": float(duration),
            "reference": ref_norm,
            "hypothesis": pred_norm,
            "ref_words": len(ref_norm.split()),
            "hyp_words": len(pred_norm.split()),
            "wer": float(seg_wer),
            "hits": word_stats["hits"],
            "substitutions": word_stats["substitutions"],
            "deletions": word_stats["deletions"],
            "insertions": word_stats["insertions"],
        })

# Aggregate statistics
print("\n" + "="*80)
print("AGGREGATE STATISTICS")
print("="*80)

valid_pairs = [(p, r) for p, r in zip(predictions, references) if r]
full_pred = " ".join([p for p, r in valid_pairs])
full_ref = " ".join([r for p, r in valid_pairs])

overall_wer = wer(full_ref, full_pred)
overall_stats = compute_word_stats(full_ref, full_pred)

total_ref_words = sum(r["ref_words"] for r in all_results)
total_hyp_words = sum(r["hyp_words"] for r in all_results)

print(f"\n📊 WORD-LEVEL STATISTICS:")
print(f"   Total reference words:  {total_ref_words}")
print(f"   Total hypothesis words: {total_hyp_words}")
print(f"\n   ✅ Hits (TP - Correct):        {overall_stats['hits']:4d} ({overall_stats['hits']/total_ref_words*100:5.1f}%)")
print(f"   🔄 Substitutions (Confused):   {overall_stats['substitutions']:4d} ({overall_stats['substitutions']/total_ref_words*100:5.1f}%)")
print(f"   ❌ Deletions (FN - Missed):    {overall_stats['deletions']:4d} ({overall_stats['deletions']/total_ref_words*100:5.1f}%)")
print(f"   ➕ Insertions (FP - Extra):    {overall_stats['insertions']:4d} ({overall_stats['insertions']/total_ref_words*100:5.1f}%)")

print(f"\n📈 ACCURACY METRICS:")
print(f"   Word Accuracy: {overall_stats['hits']/total_ref_words*100:.2f}%")
print(f"   Word Error Rate: {overall_wer*100:.2f}%")
print(f"   Precision: {overall_stats['hits']/total_hyp_words*100:.2f}%")
print(f"   Recall: {overall_stats['hits']/total_ref_words*100:.2f}%")

print(f"\n📊 SEGMENT-LEVEL STATISTICS:")
print(f"   Total segments: {len(all_results)}")
print(f"   Skipped: {skipped}")
print(f"   Perfect (WER=0): {sum(1 for r in all_results if r['wer'] == 0)}")
print(f"   Good (WER<0.2): {sum(1 for r in all_results if r['wer'] < 0.2)}")
print(f"   Avg segment WER: {np.mean([r['wer'] for r in all_results])*100:.2f}%")

# Detailed table
print("\n" + "="*80)
print("ALL SEGMENTS - SORTED BY WER (WORST FIRST)")
print("="*80)
print(f"\n{'ID':<4} {'WER':<8} {'H':<4} {'S':<4} {'D':<4} {'I':<4} {'Reference':<40} {'Hypothesis':<40}")
print("-" * 120)

df = pd.DataFrame(all_results)
df_sorted = df.sort_values('wer', ascending=False)

for _, row in df_sorted.iterrows():
    print(f"{int(row['segment_id']):<4} {row['wer']*100:6.1f}% "
          f"{int(row['hits']):<4} {int(row['substitutions']):<4} {int(row['deletions']):<4} {int(row['insertions']):<4} "
          f"{row['reference'][:38]:<40} {row['hypothesis'][:38]:<40}")

# Full comparison
print("\n" + "="*80)
print("FULL COMPARISON - ALL 129 SEGMENTS")
print("="*80)

for row in all_results:
    print(f"\n{'─'*80}")
    print(f"Segment {int(row['segment_id'])} | WER: {row['wer']*100:.1f}% | "
          f"H:{int(row['hits'])} S:{int(row['substitutions'])} D:{int(row['deletions'])} I:{int(row['insertions'])}")
    print(f"REF ({int(row['ref_words'])} words): {row['reference']}")
    print(f"HYP ({int(row['hyp_words'])} words): {row['hypothesis']}")

# Save files
print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

output_json = "outputs/verification/detailed_evaluation_all_segments.json"
os.makedirs(os.path.dirname(output_json), exist_ok=True)

with open(output_json, "w", encoding="utf-8") as f:
    json.dump({
        "overall_wer": float(overall_wer),
        "word_level_stats": {
            "total_reference_words": total_ref_words,
            "total_hypothesis_words": total_hyp_words,
            "hits_TP": overall_stats['hits'],
            "substitutions": overall_stats['substitutions'],
            "deletions_FN": overall_stats['deletions'],
            "insertions_FP": overall_stats['insertions'],
        },
        "all_segments": all_results,
    }, f, indent=2, ensure_ascii=False)

df.to_csv("outputs/verification/detailed_evaluation_all_segments.csv", index=False, encoding="utf-8")

with open("outputs/verification/full_comparison_all_129_segments.txt", "w", encoding="utf-8") as f:
    for row in all_results:
        f.write(f"Segment {int(row['segment_id'])} | WER: {row['wer']*100:.1f}% | "
                f"H:{int(row['hits'])} S:{int(row['substitutions'])} D:{int(row['deletions'])} I:{int(row['insertions'])}\n")
        f.write(f"REF: {row['reference']}\n")
        f.write(f"HYP: {row['hypothesis']}\n\n")

print(f"✓ Saved JSON, CSV, and TXT files")
print(f"\n🎯 Overall WER: {overall_wer*100:.2f}%")
print(f"✅ Word Accuracy: {overall_stats['hits']/total_ref_words*100:.2f}%")
print("="*80)