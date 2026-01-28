#!/usr/bin/env python3
import json
import torch
import librosa
import evaluate
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from tqdm import tqdm

def run_verification():
    model_path = "./outputs/whisper_somali_final"
    wav_path = "outputs/verification/verification.wav"
    manifest_path = "outputs/verification/verification_manifest.json"
    
    # Load Fine-tuned Model
    print(f"📦 Loading model from {model_path}...")
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path).to("cuda")
    wer_metric = evaluate.load("wer")
    
    # Load 5-minute clip and map
    full_audio, _ = librosa.load(wav_path, sr=16000)
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    preds, refs = [], []
    model.eval()

    print("🚀 Running Segmented Evaluation (Option 1)...")
    for seg in tqdm(manifest):
        start_idx = int(seg["start"] * 16000)
        end_idx = int(seg["end"] * 16000)
        chunk = full_audio[start_idx:end_idx]
        
        inputs = processor(chunk, return_tensors="pt", sampling_rate=16000).input_features.to("cuda")
        with torch.no_grad():
            ids = model.generate(inputs)
            transcription = processor.batch_decode(ids, skip_special_tokens=True)[0]
        
        # Ensure evaluation is against lowercase
        preds.append(transcription.lower().strip())
        refs.append(seg["text"].lower().strip())

    final_wer = wer_metric.compute(predictions=preds, references=refs)
    print(f"\n🏁 VERIFICATION COMPLETE")
    print(f"📊 Final Segmented WER: {final_wer:.2%}")

if __name__ == "__main__":
    run_verification()