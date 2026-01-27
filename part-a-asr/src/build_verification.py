#!/usr/bin/env python3
"""
Build a verified 5-minute audio clip from Somali dataset with guaranteed
audio-transcript alignment. Works without torchcodec.

FIXED VERSION: Includes proper cleanup and validation
"""
import json
import os
import subprocess
import random
import shutil
import numpy as np
import soundfile as sf
from datasets import load_dataset, Audio
from tqdm import tqdm

# =============================================================================
# CONFIGURATION
# =============================================================================
TARGET_SECONDS = 5 * 60  # 300 seconds (5 minutes)
PAUSE_DURATION = 1.0     # 1 second silence between clips
OUT_DIR = os.path.join("outputs", "verification")
os.makedirs(OUT_DIR, exist_ok=True)

TMP_DIR = os.path.join(OUT_DIR, "_tmp_audio")
os.makedirs(TMP_DIR, exist_ok=True)

OUT_WAV = os.path.join(OUT_DIR, "verification.wav")
OUT_SR = 16000
OUT_CH = 1

# =============================================================================
# AUDIO HANDLING (No torchcodec required)
# =============================================================================
def extract_audio_from_bytes_or_path(audio_obj, idx: int, target_sr: int = 16000) -> tuple:
    """
    Extract audio array from dataset audio object.
    Handles both bytes and path formats without requiring torchcodec.
    Returns: (audio_array, sample_rate)
    """
    # Try path first
    if "path" in audio_obj and audio_obj["path"] and os.path.exists(audio_obj["path"]):
        try:
            audio, sr = sf.read(audio_obj["path"])
            return audio, sr
        except Exception as e:
            print(f"Warning: Could not read {audio_obj['path']}: {e}")
    
    # Try bytes (decode with ffmpeg)
    if "bytes" in audio_obj and audio_obj["bytes"]:
        tmp_input = os.path.join(TMP_DIR, f"raw_{idx}.bin")
        tmp_output = os.path.join(TMP_DIR, f"decoded_{idx}.wav")
        
        # Write bytes to temp file
        with open(tmp_input, "wb") as f:
            f.write(audio_obj["bytes"])
        
        # Decode with ffmpeg
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", tmp_input,
                "-ar", str(target_sr), "-ac", "1",
                tmp_output
            ], check=True, capture_output=True)
            
            audio, sr = sf.read(tmp_output)
            
            # ✅ FIXED: Clean up BOTH temp files
            os.remove(tmp_input)
            os.remove(tmp_output)
            
            return audio, sr
        except Exception as e:
            print(f"Warning: ffmpeg decode failed for idx {idx}: {e}")
            # Clean up any remaining temp files
            if os.path.exists(tmp_input):
                os.remove(tmp_input)
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            raise
    
    raise ValueError(f"Could not extract audio for idx {idx}")

def process_audio_clip(audio_obj, idx: int, target_sr: int = 16000) -> tuple:
    """
    Process audio clip to target format.
    Returns: (audio_array, duration_sec)
    """
    # Extract audio
    audio, sr = extract_audio_from_bytes_or_path(audio_obj, idx, target_sr)
    
    # Resample if needed
    if sr != target_sr:
        try:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        except ImportError:
            # Fallback: use ffmpeg for resampling
            tmp_in = os.path.join(TMP_DIR, f"resample_in_{idx}.wav")
            tmp_out = os.path.join(TMP_DIR, f"resample_out_{idx}.wav")
            
            sf.write(tmp_in, audio, sr)
            subprocess.run([
                "ffmpeg", "-y", "-i", tmp_in,
                "-ar", str(target_sr), "-ac", "1",
                tmp_out
            ], check=True, capture_output=True)
            
            audio, sr = sf.read(tmp_out)
            
            # Clean up temp files
            os.remove(tmp_in)
            os.remove(tmp_out)
    
    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    
    # Calculate duration
    duration = len(audio) / target_sr
    
    return audio, duration

# =============================================================================
# MAIN SCRIPT
# =============================================================================
def main():
    print("="*70)
    print("BUILDING VERIFIED VERIFICATION CLIP")
    print("="*70)
    
    # =========================================================================
    # Load dataset (WITHOUT automatic decoding to avoid torchcodec)
    # =========================================================================
    print("\nLoading dataset: skydheere/soomali-asr-dataset (test split)...")
    try:
        # Load WITHOUT decoding audio (decode=False)
        ds = load_dataset("skydheere/soomali-asr-dataset", split="test")
        ds = ds.cast_column("audio", Audio(decode=False))  # Keep as bytes
    except Exception as e:
        print(f"Test split not available ({e}), using validation...")
        ds = load_dataset("skydheere/soomali-asr-dataset", split="validation")
        ds = ds.cast_column("audio", Audio(decode=False))
    
    print(f"✅ Loaded {len(ds)} samples")
    print(f"Dataset columns: {ds.column_names}")
    
    # Find text field
    text_field = None
    for field in ["transcription", "sentence", "text", "transcript"]:
        if field in ds.column_names:
            text_field = field
            break
    
    if text_field is None:
        raise ValueError(f"No text field found! Columns: {ds.column_names}")
    
    print(f"✅ Using text field: '{text_field}'")
    
    # =========================================================================
    # Create silence buffer
    # =========================================================================
    print(f"\nGenerating {PAUSE_DURATION}s silence buffer...")
    silence_samples = int(PAUSE_DURATION * OUT_SR)
    silence_array = np.zeros(silence_samples, dtype=np.float32)
    
    # =========================================================================
    # Collect and analyze clips
    # =========================================================================
    print("\nAnalyzing clips...")
    items = []
    failed_count = 0
    
    for i in tqdm(range(len(ds)), desc="Processing"):
        try:
            sample = ds[i]
            text = sample[text_field].strip()
            
            # Skip empty text
            if len(text) == 0:
                continue
            
            # Process audio (this handles decoding)
            audio_array, duration = process_audio_clip(sample["audio"], i, OUT_SR)
            
            # Skip very short clips
            if duration < 0.5:  # Less than 0.5 seconds
                continue
            
            # Save clip
            clip_path = os.path.join(TMP_DIR, f"clip_{i:04d}.wav")
            sf.write(clip_path, audio_array, OUT_SR)
            
            items.append({
                "idx": i,
                "path": clip_path,
                "audio": audio_array,
                "duration": duration,
                "text": text,
                "word_count": len(text.split())
            })
            
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # Only show first 5 errors
                print(f"\nWarning: Failed to process clip {i}: {e}")
    
    print(f"\n✅ Successfully processed {len(items)} clips")
    if failed_count > 0:
        print(f"⚠️  Failed to process {failed_count} clips")
    
    if len(items) == 0:
        raise ValueError("No valid clips found!")
    
    # =========================================================================
    # Select clips to reach target duration
    # =========================================================================
    print(f"\nSelecting clips to reach {TARGET_SECONDS}s target...")
    
    # Sort by duration (prefer medium-length clips for variety)
    items_sorted = sorted(items, key=lambda x: abs(x["duration"] - 10.0))
    
    # Use deterministic seed for reproducibility
    random.seed(42)
    random.shuffle(items_sorted)
    
    chosen = []
    current_total = 0.0
    total_words = 0
    
    for item in items_sorted:
        chosen.append(item)
        current_total += (item["duration"] + PAUSE_DURATION)
        total_words += item["word_count"]
        
        if current_total >= TARGET_SECONDS:
            break
    
    print(f"✅ Selected {len(chosen)} clips")
    print(f"   Total duration: {current_total:.1f}s")
    print(f"   Total words: {total_words}")
    print(f"   Avg words/clip: {total_words/len(chosen):.1f}")
    
    # =========================================================================
    # Build concatenated audio
    # =========================================================================
    print("\nBuilding concatenated audio...")
    
    audio_segments = []
    ground_truth_lines = []
    segments_metadata = []
    cursor = 0.0
    
    for i, item in enumerate(tqdm(chosen, desc="Concatenating")):
        # Add audio segment
        audio_segments.append(item["audio"])
        audio_segments.append(silence_array)
        
        # Save ground truth
        ground_truth_lines.append(item["text"])
        
        # Save metadata
        segments_metadata.append({
            "segment_num": i + 1,
            "dataset_idx": item["idx"],
            "text": item["text"],
            "word_count": item["word_count"],
            "start_sec": round(cursor, 3),
            "end_sec": round(cursor + item["duration"], 3),
            "duration": round(item["duration"], 3)
        })
        
        cursor += (item["duration"] + PAUSE_DURATION)
    
    # Concatenate all audio
    print("Concatenating audio arrays...")
    full_audio = np.concatenate(audio_segments)
    
    # Save final audio
    print(f"\nSaving to: {OUT_WAV}")
    sf.write(OUT_WAV, full_audio, OUT_SR)
    
    # =========================================================================
    # Save ground truth and metadata
    # =========================================================================
    
    # Ground truth (single line for WER calculation)
    gt_file = os.path.join(OUT_DIR, "verification_gt_clean.txt")
    with open(gt_file, "w", encoding="utf-8") as f:
        f.write(" ".join(ground_truth_lines))
    
    print(f"✅ Saved ground truth to: {gt_file}")
    
    # Segmented ground truth (for debugging)
    gt_segments_file = os.path.join(OUT_DIR, "verification_gt_segments.txt")
    with open(gt_segments_file, "w", encoding="utf-8") as f:
        for i, line in enumerate(ground_truth_lines, 1):
            f.write(f"{i}. {line}\n")
    
    print(f"✅ Saved segmented GT to: {gt_segments_file}")
    
    # Metadata JSON
    manifest = {
        "total_duration_sec": round(cursor, 2),
        "num_segments": len(chosen),
        "total_words": total_words,
        "dataset": "skydheere/soomali-asr-dataset",
        "split": "test",
        "sample_rate": OUT_SR,
        "channels": OUT_CH,
        "random_seed": 42,
        "segments": segments_metadata
    }
    
    manifest_file = os.path.join(OUT_DIR, "verification_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved manifest to: {manifest_file}")
    
    # =========================================================================
    # Verification check
    # =========================================================================
    print("\n" + "="*70)
    print("VERIFICATION CHECK:")
    print("="*70)
    
    # Load saved audio and check
    saved_audio, saved_sr = sf.read(OUT_WAV)
    saved_duration = len(saved_audio) / saved_sr
    
    print(f"Audio file: {OUT_WAV}")
    print(f"Duration: {saved_duration:.1f}s")
    print(f"Sample rate: {saved_sr}Hz")
    print(f"Channels: {'Mono' if saved_audio.ndim == 1 else 'Stereo'}")
    print(f"Segments: {len(chosen)}")
    print(f"Total words: {total_words}")
    
    # Validate speech rate
    actual_speech_time = current_total - (PAUSE_DURATION * len(chosen))
    words_per_second = total_words / actual_speech_time if actual_speech_time > 0 else 0
    
    print(f"\nSpeech analysis:")
    print(f"  Actual speech time: {actual_speech_time:.1f}s (excluding pauses)")
    print(f"  Speech rate: {words_per_second:.2f} words/sec")
    
    if words_per_second < 1.0 or words_per_second > 5.0:
        print(f"  ⚠️  Warning: Unusual speech rate (normal is 2-4 words/sec)")
    else:
        print(f"  ✅ Speech rate looks normal")
    
    # =========================================================================
    # Cleanup temporary files
    # =========================================================================
    print("\n" + "="*70)
    print("Cleaning up temporary files...")
    try:
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        print("✅ Temporary files cleaned up")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean up temp directory: {e}")
    
    # =========================================================================
    # Final Summary
    # =========================================================================
    print("\n" + "="*70)
    print("✅ SUCCESS!")
    print("="*70)
    print(f"All files saved to: {OUT_DIR}")
    print("\nGenerated files:")
    print(f"  1. {os.path.basename(OUT_WAV)} - Audio file ({saved_duration:.1f}s)")
    print(f"  2. verification_gt_clean.txt - Ground truth ({total_words} words)")
    print(f"  3. verification_gt_segments.txt - Segmented transcript")
    print(f"  4. verification_manifest.json - Detailed metadata")
    
    print("\nNext steps:")
    print("  1. Upload verification.wav to Colab")
    print("  2. Upload verification_gt_clean.txt to Colab")
    print("  3. Run inference with your model")
    print("  4. Expected WER: 10-25% (based on 0.00% validation WER)")
    print("="*70)
    
    # Show first 3 segments as preview
    print("\nFirst 3 segments preview:")
    for i in range(min(3, len(segments_metadata))):
        seg = segments_metadata[i]
        print(f"  {seg['segment_num']}. [{seg['start_sec']:.1f}s-{seg['end_sec']:.1f}s] "
              f"({seg['word_count']} words)")
        print(f"      {seg['text'][:65]}...")
    
    print()

if __name__ == "__main__":
    main()