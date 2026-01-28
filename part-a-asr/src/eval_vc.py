#!/usr/bin/env python3
"""
BEST-OF-BOTH: Per-segment verification evaluation.

Combines:
- Your code's simplicity and clarity
- My code's robustness (forced_decoder_ids, normalization, checkpoint selection)

This is the OPTIMAL solution.
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
import glob

# =============================================================================
# CONFIGURATION
# =============================================================================
WAV_PATH = "outputs/verification/verification.wav"
MANIFEST_PATH = "outputs/verification/verification_manifest.json"
CHECKPOINT_DIR = "outputs/checkpoints/whisper_small_somali_final/stage_a"
OUTPUT_PATH = "outputs/verification/evaluation_results.json"

# =============================================================================
# TEXT NORMALIZATION (Match training)
# =============================================================================
try:
    normalizer = BasicTextNormalizer()
    def normalize(text):
        return normalizer(text)
    print("✓ Using BasicTextNormalizer")
except:
    import re
    def normalize(text):
        text = text.lower().strip()
        text = re.sub(r"[""\"'`´']", "", text)
        text = re.sub(r"[^a-z0-9\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    print("✓ Using fallback normalizer")

# =============================================================================
# FIND BEST CHECKPOINT
# =============================================================================
def find_best_checkpoint(checkpoint_dir):
    """Find checkpoint with lowest eval_wer_norm."""
    print(f"\n📥 Finding best checkpoint in: {checkpoint_dir}")
    
    checkpoints = glob.glob(f"{checkpoint_dir}/checkpoint-*")
    if not checkpoints:
        raise ValueError(f"No checkpoints found in {checkpoint_dir}")
    
    checkpoints.sort(key=lambda x: int(x.split('-')[-1]))
    print(f"✓ Found {len(checkpoints)} checkpoints")
    
    best_checkpoint = None
    best_wer = float('inf')
    best_step = 0
    
    for cp in checkpoints:
        step = int(cp.split('-')[-1])
        trainer_state = os.path.join(cp, "trainer_state.json")
        
        if os.path.exists(trainer_state):
            with open(trainer_state, 'r') as f:
                state = json.load(f)
            
            # Find eval_wer_norm for this checkpoint
            for entry in reversed(state.get('log_history', [])):
                if 'eval_wer_norm' in entry and entry.get('step') == step:
                    wer_val = entry['eval_wer_norm']
                    if wer_val < best_wer:
                        best_wer = wer_val
                        best_checkpoint = cp
                        best_step = step
                    break
    
    if not best_checkpoint:
        best_checkpoint = checkpoints[-1]
        best_step = int(best_checkpoint.split('-')[-1])
        print(f"⚠️  Could not find eval_wer_norm, using latest checkpoint")
    
    print(f"✓ Best checkpoint: checkpoint-{best_step}")
    if best_wer < float('inf'):
        print(f"  Training WER: {best_wer*100:.1f}%")
    
    return best_checkpoint, best_wer

# =============================================================================
# MAIN EVALUATION
# =============================================================================
def run_verification():
    """
    Evaluate 5-minute verification clip per-segment.
    This is the CORRECT way to evaluate concatenated audio.
    """
    print("="*80)
    print("VERIFICATION EVALUATION (PER-SEGMENT)")
    print("="*80)
    
    # Find best checkpoint
    model_path, training_wer = find_best_checkpoint(CHECKPOINT_DIR)
    
    # Load model
    print(f"\n📦 Loading model from: {model_path}")
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path)
    
    # CRITICAL: Configure forced decoder IDs for Somali
    forced_decoder_ids = processor.get_decoder_prompt_ids(
        language="somali",
        task="transcribe"
    )
    print(f"✓ Forced decoder IDs: {forced_decoder_ids}")
    
    # Move to GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    print(f"✓ Model on: {device}")
    
    # Load verification audio
    print(f"\n📥 Loading audio: {WAV_PATH}")
    full_audio, sr = librosa.load(WAV_PATH, sr=16000)
    duration = len(full_audio) / sr
    print(f"✓ Loaded {duration:.1f}s of audio")
    
    # Load manifest
    print(f"📥 Loading manifest: {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r") as f:
        manifest_data = json.load(f)
    
    segments = manifest_data.get("segments", manifest_data)  # Handle both formats
    print(f"✓ Loaded {len(segments)} segments")
    
    # Evaluate each segment
    print(f"\n🚀 Evaluating {len(segments)} segments...")
    predictions = []
    references = []
    
    for seg in tqdm(segments, desc="Processing segments"):
        # Extract segment audio
        start_idx = int(seg["start_sec" if "start_sec" in seg else "start"] * sr)
        end_idx = int(seg["end_sec" if "end_sec" in seg else "end"] * sr)
        chunk = full_audio[start_idx:end_idx]
        
        # Process with model
        inputs = processor(
            chunk,
            return_tensors="pt",
            sampling_rate=sr
        ).input_features.to(device)
        
        # Generate with proper parameters
        with torch.no_grad():
            ids = model.generate(
                inputs,
                forced_decoder_ids=forced_decoder_ids,  # ← CRITICAL
                max_length=448,
                num_beams=5,  # ← Better quality
                length_penalty=1.0,
            )
        
        # Decode
        transcription = processor.batch_decode(ids, skip_special_tokens=True)[0]
        
        # Normalize (match training)
        pred_norm = normalize(transcription)
        
        # Get reference (handle both field names)
        ref_text = seg.get("text_normalized") or seg.get("text", "")
        ref_norm = normalize(ref_text) if not seg.get("text_normalized") else ref_text
        
        predictions.append(pred_norm)
        references.append(ref_norm)
    
    # Compute WER
    print(f"\n📊 Computing WER...")
    
    # Full concatenation WER
    full_pred = " ".join(predictions)
    full_ref = " ".join(references)
    wer_full = wer(full_ref, full_pred)
    
    # Per-segment WER
    segment_wers = []
    for pred, ref in zip(predictions, references):
        if ref:  # Skip empty
            seg_wer = wer(ref, pred)
            segment_wers.append(seg_wer)
    
    wer_avg_segment = np.mean(segment_wers) if segment_wers else 0.0
    
    # Results
    print(f"\n{'='*80}")
    print("RESULTS")
    print("="*80)
    print(f"Checkpoint: {os.path.basename(model_path)}")
    if training_wer < float('inf'):
        print(f"Training WER: {training_wer*100:.1f}%")
    print(f"\nSegments evaluated: {len(segments)}")
    print(f"Words predicted: {len(full_pred.split())}")
    print(f"Words reference: {len(full_ref.split())}")
    print(f"Coverage: {len(full_pred.split())/len(full_ref.split())*100:.1f}%")
    print(f"\nWER (full concatenation): {wer_full*100:.2f}%")
    print(f"WER (avg per-segment):    {wer_avg_segment*100:.2f}%")
    print("="*80)
    
    # Success criteria
    if wer_full <= 0.20:
        print(f"\n🎉 ✅ TARGET ACHIEVED!")
        print(f"   WER {wer_full*100:.1f}% ≤ 20%")
        print(f"   Excellent performance!")
    elif wer_full <= 0.30:
        print(f"\n✓ Good performance!")
        print(f"   WER {wer_full*100:.1f}% is within acceptable range")
    else:
        print(f"\n⚠️  WER {wer_full*100:.1f}% is higher than target")
    
    # Sample predictions
    print(f"\n📝 Sample predictions (first 3 segments):")
    for i in range(min(3, len(segments))):
        seg_wer = wer(references[i], predictions[i]) if references[i] else 0
        print(f"\nSegment {i+1} (WER: {seg_wer*100:.1f}%):")
        print(f"  Ref: {references[i][:70]}...")
        print(f"  Hyp: {predictions[i][:70]}...")
    
    # Save results
    results = {
        "checkpoint": model_path,
        "training_wer": float(training_wer) if training_wer < float('inf') else None,
        "evaluation_method": "per_segment",
        "num_segments": len(segments),
        "wer_full": float(wer_full),
        "wer_avg_segment": float(wer_avg_segment),
        "prediction_word_count": len(full_pred.split()),
        "reference_word_count": len(full_ref.split()),
        "target_achieved": wer_full <= 0.20,
        "predictions": predictions,
        "references": references,
        "forced_decoder_ids": forced_decoder_ids,
        "generation_config": {
            "max_length": 448,
            "num_beams": 5,
            "length_penalty": 1.0
        }
    }
    
    print(f"\n💾 Saving results to: {OUTPUT_PATH}")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("="*80)
    print("✅ EVALUATION COMPLETE")
    print("="*80)
    
    return wer_full

if __name__ == "__main__":
    run_verification()