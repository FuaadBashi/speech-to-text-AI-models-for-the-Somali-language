#!/usr/bin/env python3
import os
import io
import re
import json
import argparse
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Tuple

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
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", errors="ignore"))
    return p.stdout


def _ffmpeg_decode_16k_mono_wav_bytes_from_bytes(b: bytes) -> bytes:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"]
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


def _edit_distance_words(h: List[str], r: List[str]) -> int:
    dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        dp[i][0] = i
    for j in range(len(h) + 1):
        dp[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
    return dp[len(r)][len(h)]


def wer_word_level(preds: List[str], refs: List[str], do_normalize: bool = True) -> float:
    total_edits, total_words = 0, 0
    for p, r in zip(preds, refs):
        if do_normalize:
            p = normalize_text(p)
            r = normalize_text(r)
        pw, rw = p.split(), r.split()
        total_edits += _edit_distance_words(pw, rw)
        total_words += len(rw)
    if total_words == 0:
        return 0.0 if total_edits == 0 else 1.0
    return total_edits / total_words


def per_sample_stats(hyp: str, ref: str, do_normalize: bool = True) -> Tuple[int, int, float]:
    if do_normalize:
        hyp = normalize_text(hyp)
        ref = normalize_text(ref)
    hw, rw = hyp.split(), ref.split()
    edits = _edit_distance_words(hw, rw)
    words = len(rw)
    swer = (edits / words) if words > 0 else (0.0 if edits == 0 else 1.0)
    return edits, words, swer


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
    ap.add_argument("--max_new_tokens", type=int, default=128)

    # NEW:
    ap.add_argument("--language", default="somali", help="Whisper language prompt")
    ap.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    ap.add_argument("--output_dir", default="outputs/metrics", help="Where to write reports")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = WhisperProcessor.from_pretrained(args.model_dir)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_dir).to(device)
    model.eval()

    # Force Somali + transcribe during decoding (IMPORTANT for WER)
    forced_decoder_ids = processor.get_decoder_prompt_ids(language=args.language, task=args.task)

    # Load dataset
    if args.data_dir:
        ds = load_dataset(args.dataset, data_dir=args.data_dir, split=args.split, revision="refs/convert/parquet")
    else:
        ds_all = load_dataset(args.dataset)
        ds = ds_all[args.split] if isinstance(ds_all, dict) else ds_all

    ds = ds.cast_column("audio", Audio(decode=False))
    if args.max_samples and args.max_samples > 0:
        ds = ds.select(range(min(args.max_samples, len(ds))))

    refs_raw, hyps_raw = [], []
    refs_norm, hyps_norm = [], []
    rows = []

    bs = max(1, args.batch_size)

    for i in range(0, len(ds), bs):
        batch = ds[i:i+bs]

        audios = []
        ex_dicts = []
        for j in range(len(batch["audio"])):
            ex = {k: batch[k][j] for k in batch.keys()}
            ex_dicts.append(ex)
            audios.append(load_audio_16k_mono(ex["audio"]))

        # refs
        batch_refs_raw = [pick_text(ex) for ex in ex_dicts]
        batch_refs_norm = [normalize_text(t) for t in batch_refs_raw]

        feats = processor.feature_extractor(audios, sampling_rate=16000, return_tensors="pt").input_features.to(device)

        gen = model.generate(
            feats,
            num_beams=args.num_beams,
            max_new_tokens=args.max_new_tokens,
            forced_decoder_ids=forced_decoder_ids,
        )

        batch_hyps_raw = processor.tokenizer.batch_decode(gen, skip_special_tokens=True)
        batch_hyps_norm = [normalize_text(t) for t in batch_hyps_raw]

        for k in range(len(batch_hyps_raw)):
            idx = i + k
            e_raw, w_raw, swer_raw = per_sample_stats(batch_hyps_raw[k], batch_refs_raw[k], do_normalize=False)
            e_n, w_n, swer_n = per_sample_stats(batch_hyps_raw[k], batch_refs_raw[k], do_normalize=True)

            rows.append({
                "idx": idx,
                "ref_raw": batch_refs_raw[k],
                "hyp_raw": batch_hyps_raw[k],
                "ref_norm": batch_refs_norm[k],
                "hyp_norm": batch_hyps_norm[k],
                "edits_raw": e_raw,
                "ref_words_raw": w_raw,
                "wer_raw": swer_raw,
                "edits_norm": e_n,
                "ref_words_norm": w_n,
                "wer_norm": swer_n,
            })

        refs_raw.extend(batch_refs_raw)
        hyps_raw.extend(batch_hyps_raw)
        refs_norm.extend(batch_refs_norm)
        hyps_norm.extend(batch_hyps_norm)

    wer_raw = wer_word_level(hyps_raw, refs_raw, do_normalize=False)
    wer_norm = wer_word_level(hyps_raw, refs_raw, do_normalize=True)

    # Write reports
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"wer_{args.dataset.replace('/', '_')}_{args.split}_{stamp}"

    # JSON summary
    summary = {
        "model_dir": args.model_dir,
        "dataset": args.dataset,
        "split": args.split,
        "data_dir": args.data_dir,
        "num_beams": args.num_beams,
        "batch_size": args.batch_size,
        "max_new_tokens": args.max_new_tokens,
        "language": args.language,
        "task": args.task,
        "n_samples": len(ds),
        "wer_raw": float(wer_raw),
        "wer_norm": float(wer_norm),
    }
    json_path = os.path.join(args.output_dir, f"{base}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # CSV
    csv_path = os.path.join(args.output_dir, f"{base}.csv")
    import csv
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Markdown
    md_path = os.path.join(args.output_dir, f"{base}.md")
    worst = sorted(rows, key=lambda r: r["wer_norm"], reverse=True)[:10]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# WER Report\n\n")
        f.write(f"- Model: `{args.model_dir}`\n")
        f.write(f"- Data : `{args.dataset}` split=`{args.split}` data_dir=`{args.data_dir}`\n")
        f.write(f"- Beams: `{args.num_beams}` | batch_size=`{args.batch_size}` | max_new_tokens=`{args.max_new_tokens}`\n")
        f.write(f"- Language/task: `{args.language}` / `{args.task}`\n")
        f.write(f"- Samples: `{len(ds)}`\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **WER raw** : `{wer_raw:.4f}`\n")
        f.write(f"- **WER norm**: `{wer_norm:.4f}`\n\n")
        f.write("## Worst 10 (by normalized WER)\n\n")
        for r in worst:
            f.write(f"### idx={r['idx']} | WER_norm={r['wer_norm']:.3f}\n\n")
            f.write(f"**REF:** {r['ref_raw']}\n\n")
            f.write(f"**HYP:** {r['hyp_raw']}\n\n")

    print(f"\nMODEL: {args.model_dir}")
    print(f"DATA : {args.dataset} split={args.split} data_dir={args.data_dir}")
    print(f"BEAMS: {args.num_beams}")
    print(f"WER  : raw={wer_raw:.4f}  norm={wer_norm:.4f}")
    print(f"Wrote JSON: {json_path}")
    print(f"Wrote CSV : {csv_path}")
    print(f"Wrote MD  : {md_path}\n")


if __name__ == "__main__":
    main()
