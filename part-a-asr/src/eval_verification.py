#!/usr/bin/env python3
import os
import argparse
import torch
import json
from transformers import pipeline, WhisperProcessor

try:
    from text_normalize import normalize_text
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from text_normalize import normalize_text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True)
    ap.add_argument("--ver_wav", required=True)
    ap.add_argument("--language", default="somali")
    ap.add_argument("--task", default="transcribe")
    ap.add_argument("--output_dir", default="outputs/metrics/verification")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    device = 0 if torch.cuda.is_available() else -1
    
    processor = WhisperProcessor.from_pretrained(args.model_dir)
    
    # --- ARABIC BLOCKER LOGIC ---
    # we identify arabic unicode range and find corresponding whisper tokens
    arabic_tokens = []
    for i in range(0x0600, 0x06FF):
        tids = processor.tokenizer.encode(chr(i), add_special_tokens=False)
        arabic_tokens.extend(tids)
    arabic_tokens = list(set(arabic_tokens)) # remove duplicates

    pipe = pipeline(
        "automatic-speech-recognition",
        model=args.model_dir,
        device=device,
        chunk_length_s=30, 
    )

    generate_kwargs = {
        "language": args.language,
        "task": args.task,
        "num_beams": 5,
        "no_repeat_ngram_size": 3,
        "bad_words_ids": [[t] for t in arabic_tokens], # block arabic tokens
        "suppress_tokens": [1, 2, 7, 8, 9, 10, 14, 25, 26, 27, 28, 29, 31, 50257] # suppresses common hallucinations
    }

    print(f"\nProcessing noisy audio: {args.ver_wav}")
    result = pipe(args.ver_wav, generate_kwargs=generate_kwargs)
    
    pred_text = result["text"]
    print(f"\nTRANSCRIPTION:\n{'-'*30}\n{pred_text}\n{'-'*30}")

    # save output
    with open(os.path.join(args.output_dir, "verification_pred.txt"), "w") as f:
        f.write(pred_text)

if __name__ == "__main__":
    main()