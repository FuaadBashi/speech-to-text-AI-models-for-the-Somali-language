#!/usr/bin/env python3
import json
import os
import subprocess
import random
import shutil
import numpy as np
import soundfile as sf
from datasets import load_dataset, Audio
from tqdm import tqdm

# CONFIGURATION
TARGET_SECONDS = 5 * 60  
PAUSE_DURATION = 1.0     
OUT_DIR = os.path.join("outputs", "verification")
os.makedirs(OUT_DIR, exist_ok=True)
TMP_DIR = os.path.join(OUT_DIR, "_tmp_audio")
os.makedirs(TMP_DIR, exist_ok=True)
OUT_WAV = os.path.join(OUT_DIR, "verification.wav")
OUT_SR = 16000

def process_audio_clip(audio_obj, idx, target_sr=16000):
    audio = audio_obj["array"]
    sr = audio_obj["sampling_rate"]
    if sr != target_sr:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio, len(audio) / target_sr

def main():
    print("BUILDING VERIFIED 5-MINUTE SOMALI CLIP (LOWERCASE)")
    ds = load_dataset("skydheere/soomali-asr-dataset", split="validation", trust_remote_code=True)
    
    items = []
    for i in tqdm(range(len(ds)), desc="Analyzing"):
        sample = ds[i]
        text = sample["transcription"].lower().strip() # Force lowercase
        if not text: continue
        
        audio_array, duration = process_audio_clip(sample["audio"], i, OUT_SR)
        items.append({"audio": audio_array, "duration": duration, "text": text})
        if sum(x["duration"] + PAUSE_DURATION for x in items) >= TARGET_SECONDS:
            break

    silence = np.zeros(int(PAUSE_DURATION * OUT_SR), dtype=np.float32)
    full_audio, full_text = [], []
    for item in items:
        full_audio.extend([item["audio"], silence])
        full_text.append(item["text"])

    sf.write(OUT_WAV, np.concatenate(full_audio), OUT_SR)
    with open(os.path.join(OUT_DIR, "verification_gt_clean.txt"), "w") as f:
        f.write(" ".join(full_text))
    
    print(f"✅ Success! Saved to {OUT_DIR}")

if __name__ == "__main__":
    main()