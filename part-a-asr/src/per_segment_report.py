#!/usr/bin/env python3
import csv
import json
import os
from pathlib import Path

from jiwer import wer


def read_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f.readlines()]


def normalize_text(text: str) -> str:
    """
    Use your project normaliser if present; fall back to conservative normalisation.
    This ensures per-segment WER is computed consistently with evaluate_wer.py.
    """
    try:
        from text_normalize import normalize_text as _norm  # type: ignore
        return _norm(text)
    except Exception:
        import re
        t = text.lower()
        t = re.sub(r"[^\w\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t


def main():
    ver_dir = Path("outputs") / "verification"
    tr_dir = Path("outputs") / "transcripts"
    out_dir = Path("outputs") / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = ver_dir / "verification_manifest.json"
    gt_path = ver_dir / "verification_gt_clean.txt"
    hyp_path = tr_dir / "clean.txt"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing GT: {gt_path}")
    if not hyp_path.exists():
        raise FileNotFoundError(f"Missing hypothesis: {hyp_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    segments = manifest.get("segments", [])
    if not segments:
        raise RuntimeError("Manifest has no segments.")

    gt_lines = read_lines(str(gt_path))
    hyp_lines = read_lines(str(hyp_path))

    if len(gt_lines) != len(hyp_lines):
        raise RuntimeError(
            f"Line mismatch: GT={len(gt_lines)} vs HYP={len(hyp_lines)}. "
            "Run inference with --manifest so you get one line per segment."
        )

    if len(segments) != len(gt_lines):
        raise RuntimeError(
            f"Segment mismatch: segments={len(segments)} vs GT lines={len(gt_lines)}. "
            "Manifest and GT should correspond one-to-one."
        )

    csv_path = out_dir / "per_segment_report.csv"
    md_path = out_dir / "per_segment_report.md"

    rows = []
    wers = []

    for i, seg in enumerate(segments):
        seg_path = seg.get("path", "")
        seg_name = os.path.basename(seg_path) if seg_path else f"seg_{i+1}"

        gt = gt_lines[i]
        hyp = hyp_lines[i]

        gt_n = normalize_text(gt)
        hyp_n = normalize_text(hyp)

        seg_wer = wer(gt_n, hyp_n)
        wers.append(seg_wer)

        rows.append({
            "segment_num": i + 1,
            "segment_file": seg_name,
            "duration_sec": seg.get("duration_sec", ""),
            "start_sec": seg.get("start_sec", ""),
            "end_sec": seg.get("end_sec", ""),
            "wer_clean": seg_wer,
            "gt_clean": gt,
            "hyp_clean": hyp,
        })

    # Write CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "segment_num", "segment_file", "duration_sec", "start_sec", "end_sec",
                "wer_clean", "gt_clean", "hyp_clean"
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Write Markdown summary
    avg_wer = sum(wers) / max(len(wers), 1)
    best = min(wers) if wers else None
    worst = max(wers) if wers else None

    lines = []
    lines.append("# Per-segment WER report (clean)\n")
    lines.append(f"- Segments: {len(rows)}\n")
    lines.append(f"- Mean WER: {avg_wer:.4f}\n")
    if best is not None and worst is not None:
        lines.append(f"- Best/Worst WER: {best:.4f} / {worst:.4f}\n")
    lines.append("\n## Segments\n")
    lines.append("| # | File | Duration (s) | WER |\n")
    lines.append("|---:|---|---:|---:|\n")
    for r in rows:
        dur = r["duration_sec"]
        lines.append(f"| {r['segment_num']} | {r['segment_file']} | {dur} | {r['wer_clean']:.4f} |\n")
    md_path.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote -> {csv_path}")
    print(f"Wrote -> {md_path}")


if __name__ == "__main__":
    main()
