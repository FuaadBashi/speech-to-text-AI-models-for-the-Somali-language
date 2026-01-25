"""
Build a single >=5 minute verification clip from FLEURS Somali test split.

So here what im trying to doo is build a single >=5 minute verification clip from FLEURS Somali test split. Thats because the 
other dataset "skydheere" doesnt have anything close to real long form conversations, it mostly short pharse, sentences and words. in 
the real world somali isnt spoken like that. "FLEURS" allows me to get close to conversational Somali while also haveing a clean transcirpt 
to validate on.

Requirements:
- ffmpeg + ffprobe installed and available on PATH
  (brew install ffmpeg)

Outputs:
- outputs/verification/verification.wav
- outputs/verification/verification_gt_raw.txt
- outputs/verification/verification_gt_clean.txt
- outputs/verification/verification_manifest.json
"""

import json
import os
import subprocess
from datasets import load_dataset, Audio
from tqdm import tqdm

TARGET_SECONDS = 5 * 60  # 300 seconds
OUT_DIR = os.path.join("outputs", "verification")
os.makedirs(OUT_DIR, exist_ok=True)

TMP_DIR = os.path.join(OUT_DIR, "_tmp_audio")
os.makedirs(TMP_DIR, exist_ok=True)

# Final WAV settings
OUT_WAV = os.path.join(OUT_DIR, "verification.wav")
OUT_SR = 16000
OUT_CH = 1


def resolve_audio_file(audio_obj, idx: int) -> str:
    """
    Return a real local file path suitable for ffprobe/ffmpeg.
    """
    p = audio_obj.get("path")
    if p and os.path.exists(p):
        return os.path.abspath(p)

    # Fallback: write embedded bytes to a temp file
    b = audio_obj.get("bytes")
    if b:
        out = os.path.join(TMP_DIR, f"fleurs_{idx}.wav")
        if not os.path.exists(out):
            with open(out, "wb") as f:
                f.write(b)
        return os.path.abspath(out)

    raise RuntimeError(
        f"Couldn't resolve audio to a local file for idx={idx}. Keys={list(audio_obj.keys())}"
    )

def write_concat_list(concat_list_path: str, chosen_paths):
    base = os.path.dirname(concat_list_path)
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for path in chosen_paths:
            abs_path = path if os.path.isabs(path) else os.path.abspath(os.path.join(base, path))
            f.write(f"file '{abs_path}'\n")


def ffprobe_duration_seconds(path: str) -> float:
    """Return duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}:\n{p.stderr}")
    return float(p.stdout.strip())


def main():
    # Parquet-converted revision exposes a 'default' config; use data_dir for language.
    ds = load_dataset(
        "google/fleurs",
        data_dir="so_so",
        split="test",
        revision="refs/convert/parquet",
    )

    # IMPORTANT: do not decode audio in Python (avoids torchcodec)
    ds = ds.cast_column("audio", Audio(decode=False))

    # Collect (idx, resolved_abs_path, duration)
    items = []
    for i in tqdm(range(len(ds)), desc="Collecting durations (ffprobe)"):
        audio_obj = ds[i]["audio"]
        audio_path = resolve_audio_file(audio_obj, i)  # ABSOLUTE + exists
        dur = ffprobe_duration_seconds(audio_path)
        items.append((i, audio_path, dur))

    # Longest-first (tie-break by index)
    items.sort(key=lambda x: (-x[2], x[0]))

    chosen = []
    total = 0.0
    for idx, path, dur in items:
        chosen.append((idx, path, dur))
        total += dur
        if total >= TARGET_SECONDS:
            break

    # Write ground truth files in the SAME order as chosen audio
    gt_raw_lines = []
    gt_clean_lines = []
    segments = []
    cursor = 0.0

    for idx, path, dur in chosen:
        ex = ds[idx]
        raw_t = ex.get("raw_transcription", ex.get("transcription", ""))
        clean_t = ex.get("transcription", raw_t)

        segments.append(
            {
                "index": idx,
                "path": path,  # absolute path used for stitching
                "start_sec": round(cursor, 3),
                "end_sec": round(cursor + dur, 3),
                "duration_sec": round(dur, 3),
            }
        )
        cursor += dur

        gt_raw_lines.append(str(raw_t).strip())
        gt_clean_lines.append(str(clean_t).strip())

    with open(os.path.join(OUT_DIR, "verification_gt_raw.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(gt_raw_lines) + "\n")

    with open(
        os.path.join(OUT_DIR, "verification_gt_clean.txt"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(gt_clean_lines) + "\n")

    # Build an ffmpeg concat list file (ABSOLUTE paths to avoid double-prefixing)
    concat_list_path = os.path.join(OUT_DIR, "concat_list.txt")
    write_concat_list(concat_list_path, [p for _, p, _ in chosen])

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for _, path, _ in chosen:
            f.write(f"file '{os.path.abspath(path)}'\n")

    # Stitch into a single WAV (16kHz mono)
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_path,
        "-ac",
        str(OUT_CH),
        "-ar",
        str(OUT_SR),
        OUT_WAV,
    ]
    p = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed:\n{p.stderr}")

    manifest = {
        "dataset": "google/fleurs",
        "revision": "refs/convert/parquet",
        "data_dir": "so_so",
        "split": "test",
        "target_seconds": TARGET_SECONDS,
        "total_duration_sec": round(cursor, 3),
        "num_segments": len(chosen),
        "selection_strategy": "longest-first (duration desc; tie-break by index)",
        "audio_output": OUT_WAV,
        "wav_format": {"sampling_rate": OUT_SR, "channels": OUT_CH},
        "segments": segments,
    }
    with open(os.path.join(OUT_DIR, "verification_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Built {OUT_WAV} duration={cursor:.2f}s segments={len(chosen)}")


if __name__ == "__main__":
    main()
