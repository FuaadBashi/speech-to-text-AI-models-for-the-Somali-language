import json
import os
import numpy as np
import soundfile as sf
import librosa
from datasets import load_dataset, Audio
from tqdm import tqdm
from transformers.models.whisper.english_normalizer import BasicTextNormalizer

# =============================================================================
# CONFIGURATION
# =============================================================================
TARGET_SECONDS = 5 * 60  # 5 minutes total
PAUSE_DURATION = 1.0     # 1 second silence between clips
OUT_DIR = os.path.join("outputs", "verification")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_WAV = os.path.join(OUT_DIR, "verification.wav")
OUT_MANIFEST = os.path.join(OUT_DIR, "verification_manifest.json")
OUT_SR = 16000

# Text normalization (match training)
try:
    normalizer = BasicTextNormalizer()
    def normalize_text(text):
        return normalizer(text)
    print("✓ Using BasicTextNormalizer")
except:
    import re
    def normalize_text(text):
        text = text.lower().strip()
        text = re.sub(r"[""\"'`´']", "", text)
        text = re.sub(r"[^a-z0-9\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    print("✓ Using fallback normalizer")

# =============================================================================
# BUILD VERIFICATION CLIP
# =============================================================================
def build_verification_clip():
    """
    Build 5-minute WAV by concatenating dataset clips with silence pauses.
    Save manifest with per-segment boundaries.
    """
    print("="*80)
    print("BUILDING 5-MINUTE VERIFICATION CLIP")
    print("="*80)

    # Load dataset WITHOUT auto-decoding (avoids torchcodec issues)
    print("\n📥 Loading dataset...")
    ds = load_dataset("skydheere/soomali-asr-dataset", split="validation")
    ds = ds.cast_column("audio", Audio(decode=False))
    print(f"✓ Loaded {len(ds)} samples from validation split")

    audio_segments = []
    manifest = []
    current_time = 0.0
    failed_count = 0
    total_words_raw = 0
    total_words_norm = 0

    print("\n🔊 Processing audio segments...")
    for i in tqdm(range(len(ds)), desc="Building clip"):
        if current_time >= TARGET_SECONDS:
            break

        try:
            sample = ds[i]
            text_raw = sample["transcription"].strip()
            if not text_raw:
                continue

            # Normalize text (for evaluation)
            text_norm = normalize_text(text_raw)

            # Decode audio manually (robust method)
            audio_data = sample["audio"]

            # Try path first
            if "path" in audio_data and audio_data["path"] and os.path.exists(audio_data["path"]):
                audio, sr = sf.read(audio_data["path"])
            # Try bytes
            elif "bytes" in audio_data and audio_data["bytes"]:
                import io
                audio, sr = sf.read(io.BytesIO(audio_data["bytes"]))
            # Try array
            elif "array" in audio_data:
                audio = np.array(audio_data["array"], dtype=np.float32)
                sr = audio_data.get("sampling_rate", OUT_SR)
            else:
                failed_count += 1
                continue

            # Ensure numpy array
            audio = np.array(audio, dtype=np.float32)

            # Convert stereo to mono
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)

            # Resample if needed
            if sr != OUT_SR:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=OUT_SR)

            duration = len(audio) / OUT_SR

            # Skip very short clips
            if duration < 0.5:
                continue

            # Add to manifest
            segment_info = {
                "segment_id": len(manifest),
                "dataset_idx": i,
                "start_sec": round(current_time, 4),
                "end_sec": round(current_time + duration, 4),
                "duration_sec": round(duration, 4),
                "text_raw": text_raw,
                "text_normalized": text_norm,
                "word_count_raw": len(text_raw.split()),
                "word_count_normalized": len(text_norm.split()),
            }
            manifest.append(segment_info)

            # Add audio
            audio_segments.append(audio)

            # Add silence pause
            silence = np.zeros(int(PAUSE_DURATION * OUT_SR), dtype=np.float32)
            audio_segments.append(silence)

            current_time += (duration + PAUSE_DURATION)
            total_words_raw += len(text_raw.split())
            total_words_norm += len(text_norm.split())

        except Exception as e:
            failed_count += 1
            if failed_count <= 3:
                print(f"\n⚠️  Error on sample {i}: {e}")
            continue

    if not audio_segments:
        raise ValueError("No audio segments were successfully processed!")

    print(f"\n✓ Processed {len(manifest)} segments")
    if failed_count > 0:
        print(f"⚠️  Failed to process {failed_count} samples")

    # Concatenate all audio
    print("\n🔗 Concatenating audio...")
    full_audio = np.concatenate(audio_segments)

    # Save WAV
    print(f"💾 Saving WAV file...")
    sf.write(OUT_WAV, full_audio, OUT_SR)
    actual_duration = len(full_audio) / OUT_SR

    # Save manifest
    print(f"💾 Saving manifest...")
    manifest_data = {
        "total_duration_sec": round(actual_duration, 2),
        "num_segments": len(manifest),
        "sample_rate": OUT_SR,
        "pause_duration_sec": PAUSE_DURATION,
        "total_words_raw": total_words_raw,
        "total_words_normalized": total_words_norm,
        "dataset": "skydheere/soomali-asr-dataset",
        "split": "validation",
        "text_field": "transcription",
        "normalization": "BasicTextNormalizer",
        "segments": manifest
    }

    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "="*80)
    print("✅ VERIFICATION CLIP CREATED")
    print("="*80)
    print(f"Audio file: {OUT_WAV}")
    print(f"  Duration: {actual_duration:.1f}s ({actual_duration/60:.1f} minutes)")
    print(f"  Sample rate: {OUT_SR} Hz")
    print(f"  Size: {os.path.getsize(OUT_WAV) / 1024**2:.1f} MB")
    print(f"\nManifest: {OUT_MANIFEST}")
    print(f"  Segments: {len(manifest)}")
    print(f"  Words (raw): {total_words_raw}")
    print(f"  Words (normalized): {total_words_norm}")
    print(f"\n📊 Average per segment:")
    print(f"  Duration: {actual_duration/len(manifest):.1f}s")
    print(f"  Words: {total_words_norm/len(manifest):.1f}")
    print("="*80)

    # Verify alignment (spot check)
    verify_alignment()

def verify_alignment():
    """Spot check: verify manifest timestamps match audio."""
    print("\n🔍 SPOT CHECK: Verifying alignment...")

    if not os.path.exists(OUT_WAV) or not os.path.exists(OUT_MANIFEST):
        print("❌ Files not found")
        return

    # Load
    audio_full, sr = sf.read(OUT_WAV)
    with open(OUT_MANIFEST, "r") as f:
        manifest_data = json.load(f)

    # Check first segment
    seg = manifest_data["segments"][0]
    start_idx = int(seg["start_sec"] * sr)
    end_idx = int(seg["end_sec"] * sr)
    segment_audio = audio_full[start_idx:end_idx]

    actual_dur = len(segment_audio) / sr
    expected_dur = seg["duration_sec"]

    print(f"Segment 0: '{seg['text_normalized'][:50]}...'")
    print(f"  Expected: {expected_dur:.3f}s | Actual: {actual_dur:.3f}s")

    if abs(actual_dur - expected_dur) < 0.01:
        print("✅ ALIGNMENT VERIFIED")
    else:
        print("⚠️  ALIGNMENT MISMATCH")

# Run the builder
build_verification_clip()