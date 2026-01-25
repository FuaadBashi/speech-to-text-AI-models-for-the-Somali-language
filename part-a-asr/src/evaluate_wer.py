"""Compute WER for verification clip.

Here it computes:
  - WER-clean: hypothesis vs verification_gt_clean.txt
  - WER-raw:   hypothesis vs verification_gt_raw.txt
This is done, because FLEURS provides both raw_transcription and a normalised transcription, 
which helps you show robustness and transparency.

Writes to:
  outputs/metrics/wer_report.json
"""

import json
import os
from jiwer import wer
from text_normalize import normalize_lines

VER_DIR = os.path.join("outputs", "verification")
TR_DIR = os.path.join("outputs", "transcripts")
OUT_DIR = os.path.join("outputs", "metrics")
os.makedirs(OUT_DIR, exist_ok=True)

def read_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def main():
    gt_raw = read_lines(os.path.join(VER_DIR, "verification_gt_raw.txt"))
    gt_clean = read_lines(os.path.join(VER_DIR, "verification_gt_clean.txt"))

    hyp_raw = read_lines(os.path.join(TR_DIR, "raw.txt"))

    gt_raw_norm = normalize_lines(gt_raw)
    gt_clean_norm = normalize_lines(gt_clean)
    hyp_norm = normalize_lines(hyp_raw)

    wer_raw = wer(gt_raw_norm, hyp_norm)
    wer_clean = wer(gt_clean_norm, hyp_norm)

    report = {
        "verification": {
            "audio": os.path.join(VER_DIR, "verification.wav"),
            "gt_raw": os.path.join(VER_DIR, "verification_gt_raw.txt"),
            "gt_clean": os.path.join(VER_DIR, "verification_gt_clean.txt"),
            "manifest": os.path.join(VER_DIR, "verification_manifest.json"),
        },
        "hypothesis": {
            "raw_transcript": os.path.join(TR_DIR, "raw.txt"),
            "clean_transcript": os.path.join(TR_DIR, "clean.txt"),
        },
        "metrics": {
            "wer_raw": wer_raw,
            "wer_clean": wer_clean,
        },
        "notes": "WER computed after conservative normalisation (see src/text_normalize.py and docs/wer_methodology.md)."
    }

    out_path = os.path.join(OUT_DIR, "wer_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"WER-clean: {wer_clean:.4f}")
    print(f"WER-raw  : {wer_raw:.4f}")
    print(f"Wrote -> {out_path}")

if __name__ == "__main__":
    main()
