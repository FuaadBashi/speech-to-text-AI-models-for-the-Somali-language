#!/usr/bin/env python3
"""
Evaluate a fine-tuned Whisper checkpoint on one or more local WAV files with beam search.

Example:
  python src/eval_verification.py \
    --model_dir outputs/checkpoints/whisper_medium_two_stage_t4/stage_a \
    --pairs verification_pairs.tsv \
    --num_beams 8

TSV format (tab-separated):
  /path/to/audio.wav<TAB>reference transcription
"""

import argparse
import csv
import json
import os
import re
from dataclasses import asdict, dataclass
from typing import List, Tuple

import numpy as np
import torch
import soundfile as sf
import evaluate
from transformers import WhisperForConditionalGeneration, WhisperProcessor

try:
    from transformers.models.whisper.english_normalizer import BasicTextNormalizer
except Exception:
    BasicTextNormalizer = None


def normalize_somali_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[“”\"'`´’]", "", s)
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_pairs_tsv(path: str) -> List[Tuple[str, str]]:
    pairs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            wav, ref = line.split("\t", 1)
            pairs.append((wav, ref))
    return pairs


def read_wav_16k_mono(path: str) -> np.ndarray:
    audio, sr = sf.read(path)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    if sr != 16000:
        # simple resample (good enough for eval); for best quality use librosa.resample
        import librosa
        audio = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=16000)
    return audio.astype(np.float32)


@dataclass
class Row:
    file: str
    ref: str
    hyp: str
    ref_norm: str
    hyp_norm: str
    wer: float


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True)
    ap.add_argument("--pairs", required=True, help="TSV: wav_path<TAB>reference")
    ap.add_argument("--num_beams", type=int, default=5)
    ap.add_argument("--max_new_tokens", type=int, default=225)
    ap.add_argument("--out_dir", default="outputs/verification_eval")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    processor = WhisperProcessor.from_pretrained(args.model_dir)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_dir).to(device)
    model.eval()

    wer_metric = evaluate.load("wer")
    basic_norm = BasicTextNormalizer() if BasicTextNormalizer is not None else None

    pairs = load_pairs_tsv(args.pairs)

    rows: List[Row] = []

    print("IDX  FILE                            BEAMS  WER")
    print("---  ------------------------------  -----  -----")

    for i, (wav_path, ref) in enumerate(pairs, start=1):
        audio = read_wav_16k_mono(wav_path)
        inputs = processor.feature_extractor(audio, sampling_rate=16000, return_tensors="pt")
        input_features = inputs["input_features"].to(device)

        with torch.no_grad():
            pred_ids = model.generate(
                input_features,
                num_beams=args.num_beams,
                max_new_tokens=args.max_new_tokens,
            )

        hyp = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)[0]

        if basic_norm is not None:
            ref_n = basic_norm(ref)
            hyp_n = basic_norm(hyp)
        else:
            ref_n = normalize_somali_text(ref)
            hyp_n = normalize_somali_text(hyp)

        wer_val = wer_metric.compute(predictions=[hyp_n], references=[ref_n])

        print(f"{i:3d}  {os.path.basename(wav_path)[:30]:30s}  {args.num_beams:5d}  {wer_val:0.3f}")

        rows.append(Row(
            file=wav_path,
            ref=ref,
            hyp=hyp,
            ref_norm=ref_n,
            hyp_norm=hyp_n,
            wer=float(wer_val),
        ))

    avg_wer = float(np.mean([r.wer for r in rows])) if rows else 1.0
    print(f"\nDONE. Mean WER (normalized) = {avg_wer:.4f}")

    # Save artifacts
    with open(os.path.join(args.out_dir, "rows.json"), "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in rows], f, ensure_ascii=False, indent=2)

    with open(os.path.join(args.out_dir, "rows.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()) if rows else ["file","ref","hyp","ref_norm","hyp_norm","wer"])
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


if __name__ == "__main__":
    main()
