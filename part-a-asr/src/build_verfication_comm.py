import os
import subprocess
import json
import re
from datasets import load_dataset, Audio
from tqdm import tqdm

# --- CONFIGURATION ---
TARGET_SECONDS = 5 * 60  # 5 Minutes
PAUSE_DURATION = 1.0     # 1 second of silence between clips

# Labels the folder specifically as requested
OUT_DIR = os.path.join("outputs", "verification Common Voice")
os.makedirs(OUT_DIR, exist_ok=True)

TMP_DIR = os.path.join(OUT_DIR, "_tmp_audio")
os.makedirs(TMP_DIR, exist_ok=True)

OUT_WAV = os.path.join(OUT_DIR, "verification_cv.wav")
OUT_SR = 16000
OUT_CH = 1

def simple_normalize(text):
    """Ensures text is alphabet letters lower case as per user instructions."""
    # Remove punctuation and lowercase
    text = text.lower()
    # Keep only characters (including Somali specific x, c, ') and spaces
    text = re.sub(r"[^a-zxc' ]", "", text)
    return text.strip()

def main():
    print("Loading Common Voice Somali (Streaming Mode)...")
    ds = load_dataset("mozilla-foundation/common_voice_11_0", "so", 
                      split="test", streaming=True, trust_remote_code=True)
    ds = ds.cast_column("audio", Audio(sampling_rate=OUT_SR))

    # 1. Create a 1-second silence file
    silence_wav = os.path.join(TMP_DIR, "cv_pause.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={OUT_SR}:cl=mono", 
        "-t", str(PAUSE_DURATION), silence_wav
    ], check=True, capture_output=True)

    chosen_paths = []
    gt_texts = []
    current_total = 0.0
    
    # 2. Iterate through stream until we hit 5 minutes
    print("Collecting clips...")
    for i, example in enumerate(ds):
        temp_clip = os.path.join(TMP_DIR, f"cv_clip_{i}.wav")
        import soundfile as sf
        sf.write(temp_clip, example["audio"]["array"], OUT_SR)
        
        duration = len(example["audio"]["array"]) / OUT_SR
        chosen_paths.append(temp_clip)
        
        # Apply normalization to ground truth text
        clean_text = simple_normalize(example["sentence"])
        gt_texts.append(clean_text)
        
        current_total += (duration + PAUSE_DURATION)
        if current_total >= TARGET_SECONDS:
            break

    # 3. Write Concat List for FFMPEG
    concat_list_path = os.path.join(OUT_DIR, "cv_concat_list.txt")
    with open(concat_list_path, "w") as f:
        for path in chosen_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
            f.write(f"file '{os.path.abspath(silence_wav)}'\n")

    # 4. Stitch with FFMPEG
    print(f"Stitching into {OUT_WAV}...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-ac", str(OUT_CH), "-ar", str(OUT_SR), OUT_WAV
    ], check=True, capture_output=True)

    # 5. Save Ground Truth (lowercase alphabet only)
    with open(os.path.join(OUT_DIR, "verification_cv_gt.txt"), "w") as f:
        f.write("\n".join(gt_texts))

    print(f"\nSUCCESS: Created {current_total:.2f}s verification clip.")
    print(f"Folder: {OUT_DIR}")
    print(f"Audio File: {OUT_WAV}")

if __name__ == "__main__":
    main()