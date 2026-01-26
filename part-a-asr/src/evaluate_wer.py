#!/usr/bin/env python3
import os
import io
import argparse
import subprocess
from typing import Any, Dict, List

import numpy as np
import soundfile as sf
import torch
from datasets import load_dataset, Audio
from transformers import WhisperProcessor, WhisperForConditionalGeneration

try:
    from text_normalize import normalize_text
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from text_normalize import normalize_text


def _ffmpeg_decode_16k_mono_wav_bytes_from_path(path: str) -> bytes:
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-i",path,"-ac","1","-ar","16000","-f","wav","pipe:1"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", errors="ignore"))
    return p.stdout


def _ffmpeg_decode_16k_mono_wav_bytes_from_bytes(b: bytes) -> bytes:
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-i","pipe:0","-ac","1","-ar","16000","-f","wav","pipe:1"]
    p = subprocess.run(cmd, input=b, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", errors="ignore"))
    return p.stdout


def load_audio_16k_mono(audio_obj: Dict[str, Any]) -> np.ndarray:
    if audio_obj.get("bytes") is not None:
        wav_bytes = _ffmpeg_decode_16k_mono_wav_bytes_from_bytes(audio_obj["bytes"])
    else:
        wav_bytes = _ffmpeg_decode_16k_mono_wav_bytes_from_path(audio_obj["path"])
    audio, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
    if sr != 16000:
        raise RuntimeError(f"Expected 16kHz, got {sr}")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio


def pick_text(ex: Dict[str, Any]) -> str:
    for k in ["sentence", "text", "transcription", "transcript", "raw_transcription"]:
        if k in ex and ex[k] is not None and str(ex[k]).strip() != "":
            return str(ex[k])
    return ""


def wer_word_level(preds: List[str], refs: List[str]) -> float:
    def edit_distance_words(h: List[str], r: List[str]) -> int:
        dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
        for i in range(len(r) + 1):
            dp[i][0] = i
        for j in range(len(h) + 1):
            dp[0][j] = j
        for i in range(1, len(r) + 1):
            for j in range(1, len(h) + 1):
                cost = 0 if r[i - 1] == h[j - 1] else 1
                dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
        return dp[len(r)][len(h)]

    total_edits, total_words = 0, 0
    for p, r in zip(preds, refs):
        p = normalize_text(p)
        r = normalize_text(r)
        pw, rw = p.split(), r.split()
        total_edits += edit_distance_words(pw, rw)
        total_words += len(rw)

    if total_words == 0:
        return 0.0 if total_edits == 0 else 1.0
    return total_edits / total_words


@torch.inference_mode()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--split", default="validation")
    ap.add_argument("--data_dir", default=None, help="For datasets like google/fleurs (e.g., so_so)")
    ap.add_argument("--max_samples", type=int, default=0)
    ap.add_argument("--num_beams", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=2)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = WhisperProcessor.from_pretrained(args.model_dir)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_dir).to(device)
    model.eval()

    # Load dataset
    if args.data_dir:
        ds = load_dataset(args.dataset, data_dir=args.data_dir, split=args.split, revision="refs/convert/parquet")
    else:
        ds_all = load_dataset(args.dataset)
        ds = ds_all[args.split] if isinstance(ds_all, dict) else ds_all

    ds = ds.cast_column("audio", Audio(decode=False))
    if args.max_samples and args.max_samples > 0:
        ds = ds.select(range(min(args.max_samples, len(ds))))

    refs, hyps = [], []
    bs = max(1, args.batch_size)

    for i in range(0, len(ds), bs):
        batch = ds[i:i+bs]
        audios = [load_audio_16k_mono(a) for a in batch["audio"]]
        texts = [normalize_text(pick_text({k: batch[k][j] for k in batch.keys()})) for j in range(len(audios))]

        feats = processor.feature_extractor(audios, sampling_rate=16000, return_tensors="pt").input_features.to(device)

        gen = model.generate(
            feats,
            num_beams=args.num_beams,
            max_new_tokens=128,
        )
        preds = processor.tokenizer.batch_decode(gen, skip_special_tokens=True)

        refs.extend(texts)
        hyps.extend(preds)

    wer = wer_word_level(hyps, refs)
    print(f"\nMODEL: {args.model_dir}")
    print(f"DATA : {args.dataset} split={args.split} data_dir={args.data_dir}")
    print(f"BEAMS: {args.num_beams}")
    print(f"WER  : {wer:.4f}\n")


if __name__ == "__main__":
    main()
