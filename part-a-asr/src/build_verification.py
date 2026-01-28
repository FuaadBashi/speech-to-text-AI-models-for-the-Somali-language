#!/usr/bin/env python3
import json
import os
import numpy as np
import soundfile as sf
import librosa
from datasets import load_dataset, Audio
from tqdm import tqdm

# CONFIGURATION
TARGET_SECONDS = 300  # 5 minutes
PAUSE_DURATION = 1.0     
OUT_DIR = os.path.join("outputs", "verification")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_WAV = os.path.join(OUT_DIR, "verification.wav")
OUT_MANIFEST = os.path.join(OUT_DIR, "verification_manifest.json")
OUT_SR = 16000

def build_and_verify():
    print("🛠️ BUILDING 5-MINUTE WAV + JSON MANIFEST (LOWERCASE)")
    # cast_column(decode=False) stops the torchcodec ImportError
    ds = load_dataset("skydheere/soomali-asr-dataset", split="test").cast_column("audio", Audio(decode=False))
    
    audio_list = []
    manifest = []
    current_time = 0.0
    
    for i in tqdm(range(len(ds)), desc="Processing Segments"):
        if current_time >= TARGET_SECONDS:
            break
            
        sample = ds[i]
        text = sample["transcription"].lower().strip() # Force lowercase
        if not text: continue
        
        try:
            # Manual librosa load bypasses broken HF environment audio loading
            audio, _ = librosa.load(sample["audio"]["path"], sr=OUT_SR)
            duration = len(audio) / OUT_SR
            
            # Record timestamps for segmented evaluation
            manifest.append({
                "start": current_time,
                "end": current_time + duration,
                "text": text
            })
            
            audio_list.append(audio)
            # Add pause
            audio_list.append(np.zeros(int(PAUSE_DURATION * OUT_SR)))
            
            current_time += (duration + PAUSE_DURATION)
        except Exception as e:
            continue

    # Save artifact
    sf.write(OUT_WAV, np.concatenate(audio_list), OUT_SR)
    with open(OUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=4)
    
    print(f"✅ Created {current_time/60:.2f}m WAV and Manifest in {OUT_DIR}")

if __name__ == "__main__":
    build_and_verify()