#!/usr/bin/env python3
import json
import os
import subprocess
import random
from datasets import load_dataset, Audio
from tqdm import tqdm

# --- CONFIGURATION ---
TARGET_SECONDS = 5 * 60  # 300 seconds (5 minutes)
PAUSE_DURATION = 1.0     # 1 second of silence between clips
OUT_DIR = os.path.join("outputs", "verification")
os.makedirs(OUT_DIR, exist_ok=True)

TMP_DIR = os.path.join(OUT_DIR, "_tmp_audio")
os.makedirs(TMP_DIR, exist_ok=True)

OUT_WAV = os.path.join(OUT_DIR, "verification.wav")
OUT_SR = 16000
OUT_CH = 1

def resolve_audio_file(audio_obj, idx: int) -> str:
    """Extracts local path or writes bytes to temp file for ffmpeg."""
    p = audio_obj.get("path")
    if p and os.path.exists(p):
        return os.path.abspath(p)
    b = audio_obj.get("bytes")
    if b:
        out = os.path.join(TMP_DIR, f"fleurs_{idx}.wav")
        if not os.path.exists(out):
            with open(out, "wb") as f:
                f.write(b)
        return os.path.abspath(out)
    raise RuntimeError(f"Could not resolve audio for idx {idx}")

def ffprobe_duration(path: str) -> float:
    """Gets duration in seconds via ffprobe."""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return float(p.stdout.strip())

def main():
    print("Loading FLEURS Somali test split...")
    ds = load_dataset("google/fleurs", data_dir="so_so", split="test", revision="refs/convert/parquet")
    ds = ds.cast_column("audio", Audio(decode=False))

    # 1. Create a 1-second silence file
    silence_wav = os.path.join(TMP_DIR, "silence_pause.wav")
    print(f"Generating {PAUSE_DURATION}s silence buffer...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={OUT_SR}:cl=mono", 
        "-t", str(PAUSE_DURATION), silence_wav
    ], check=True, capture_output=True)

    # 2. Collect durations
    items = []
    for i in tqdm(range(len(ds)), desc="Analyzing clips"):
        path = resolve_audio_file(ds[i]["audio"], i)
        dur = ffprobe_duration(path)
        items.append((i, path, dur))

    # 3. Shuffle and pick clips until we hit TARGET_SECONDS
    random.seed(42) # Consistent shuffle for reproducibility
    random.shuffle(items)
    
    chosen = []
    current_total = 0.0
    for idx, path, dur in items:
        chosen.append((idx, path, dur))
        current_total += (dur + PAUSE_DURATION)
        if current_total >= TARGET_SECONDS:
            break

    # 4. Write Ground Truth and Concat List
    gt_clean = []
    concat_list_path = os.path.join(OUT_DIR, "concat_list.txt")
    segments = []
    cursor = 0.0

    with open(concat_list_path, "w") as f_concat:
        for idx, path, dur in chosen:
            # Write to concat list: Clip + Silence
            f_concat.write(f"file '{path}'\n")
            f_concat.write(f"file '{os.path.abspath(silence_wav)}'\n")
            
            # Save metadata
            text = ds[idx]["transcription"]
            gt_clean.append(text.strip())
            
            segments.append({
                "index": idx,
                "text": text,
                "start_sec": round(cursor, 3),
                "end_sec": round(cursor + dur, 3)
            })
            cursor += (dur + PAUSE_DURATION)

    # 5. Export Files
    with open(os.path.join(OUT_DIR, "verification_gt_clean.txt"), "w") as f:
        f.write("\n".join(gt_clean))

    print(f"Stitching {len(chosen)} segments into {OUT_WAV}...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-ac", str(OUT_CH), "-ar", str(OUT_SR), OUT_WAV
    ], check=True, capture_output=True)

    # 6. Save Manifest
    manifest = {
        "total_duration": round(cursor, 2),
        "num_clips": len(chosen),
        "segments": segments
    }
    with open(os.path.join(OUT_DIR, "verification_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSUCCESS: Built {cursor:.2f}s verification audio.")
    print(f"Files saved in: {OUT_DIR}")

if __name__ == "__main__":
    main()