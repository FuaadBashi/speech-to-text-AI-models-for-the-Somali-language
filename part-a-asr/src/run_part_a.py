#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="hamaada/whisper-finetuned-somali-stt")
    ap.add_argument("--language", default="somali")
    ap.add_argument("--quiet", action="store_true", help="Pass --quiet to infer.py")
    ap.add_argument("--rebuild_verification", action="store_true")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    ver_manifest = root / "outputs" / "verification" / "verification_manifest.json"
    ver_wav = root / "outputs" / "verification" / "verification.wav"
    wer_json = root / "outputs" / "metrics" / "wer_report.json"

    # 1) Build verification (only if missing, unless forced)
    if args.rebuild_verification or (not ver_manifest.exists()) or (not ver_wav.exists()):
        run(["python3", "src/build_verification_fleurs.py"], cwd=root)

    # 2) Inference (manifest-driven)
    infer_cmd = [
        "python3", "src/infer.py",
        "--manifest", str(ver_manifest),
        "--out", "outputs/transcripts/raw.txt",
        "--model", args.model,
        "--language", args.language,
    ]
    if args.quiet:
        infer_cmd.append("--quiet")
    run(infer_cmd, cwd=root)

    # 3) Evaluate WER
    run(["python3", "src/evaluate_wer.py"], cwd=root)

    # 4) Per-segment report
    run(["python3", "src/per_segment_report.py"], cwd=root)

    # 5) Print final WER
    if wer_json.exists():
        d = json.loads(wer_json.read_text(encoding="utf-8"))
        wer_clean = d.get("metrics", {}).get("wer_clean", None)
        wer_raw = d.get("metrics", {}).get("wer_raw", None)
        print(f"\nDONE. WER-clean={wer_clean:.4f} WER-raw={wer_raw:.4f}")
        print(f"Artifacts:\n- {wer_json}\n- outputs/metrics/per_segment_report.csv\n- outputs/metrics/per_segment_report.md\n")


if __name__ == "__main__":
    main()
