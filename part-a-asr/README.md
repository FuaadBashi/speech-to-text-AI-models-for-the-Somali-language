# Part A — Somali ASR (Verification Clip + Inference + WER)

This repository implements **Part A** of the assessment: creating a **5+ minute verification clip** with **ground-truth transcripts**, running **ASR inference**, and computing **WER** (Word Error Rate) on a fixed, reproducible evaluation set.

## What you get (deliverables)

After running the pipeline you will have:

### Verification artefacts (5+ minutes)
- `outputs/verification/verification.wav`  
- `outputs/verification/verification_manifest.json`  
- `outputs/verification/verification_gt_raw.txt`  
- `outputs/verification/verification_gt_clean.txt`

### Inference outputs
- `outputs/transcripts/raw.txt`
- `outputs/transcripts/clean.txt`

### Metrics
- `outputs/metrics/wer_report.json`

## Key design choices (high level)

- **Verification audio source:** `google/fleurs` Somali (`so_so`) **test split**
- **Why parquet revision:** newer `datasets` versions do not support dataset scripts; parquet conversion is supported.
- **Selection strategy:** **longest-first** until total duration ≥ 300 seconds (minimises stitching overhead).
- **Evaluation strategy:** **manifest-driven inference**: one segment → one transcript line (prevents line-count mismatch issues in WER).

See:
- `docs/data_sources.md`
- `docs/decisions.md`
- `docs/wer_methodology.md`

---

## Prerequisites

1) **Python 3.9+**
2) **FFmpeg installed** (must provide `ffmpeg` and `ffprobe` on PATH)

Verify:
```bash
ffmpeg -version
ffprobe -version
python3 --version
Setup
Create and activate a virtual environment:

bash
Copy code
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
(Optional, recommended for exact reproducibility)

bash
Copy code
python3 -m pip freeze > requirements.lock.txt
Step 1 — Build verification clip (5+ minutes)
This downloads the FLEURS Somali test split (parquet), selects the longest utterances until ≥ 5 minutes, and stitches them into a single WAV.

bash
Copy code
python3 src/build_verification_fleurs.py
Expected output:

outputs/verification/verification.wav

outputs/verification/verification_manifest.json

outputs/verification/verification_gt_raw.txt

outputs/verification/verification_gt_clean.txt

Quick sanity checks:

bash
Copy code
ls -lah outputs/verification/verification.wav
head outputs/verification/verification_manifest.json
wc -l outputs/verification/verification_gt_clean.txt
Step 2 — Run inference (manifest-driven)
Run ASR per segment (the manifest lists the exact segment WAV files used to build the verification clip).

Example model (your proven working run):

bash
Copy code
python3 src/infer.py \
  --manifest outputs/verification/verification_manifest.json \
  --out outputs/transcripts/raw.txt \
  --model hamaada/whisper-finetuned-somali-stt \
  --language somali \
  --quiet
Sanity check alignment:

bash
Copy code
wc -l outputs/verification/verification_gt_clean.txt outputs/transcripts/clean.txt
These must match (e.g., 8 vs 8).

Step 3 — Evaluate WER
bash
Copy code
python3 src/evaluate_wer.py
cat outputs/metrics/wer_report.json
Troubleshooting
1) “Dataset scripts are no longer supported”
If you see an error like:

RuntimeError: Dataset scripts are no longer supported, but found fleurs.py

That means you’re on a newer datasets version (expected). This repo uses:

revision="refs/convert/parquet"

data_dir="so_so"

2) TorchCodec / FFmpeg dylib errors during inference
If you previously saw torchcodec loading failures, this repo’s inference path should avoid depending on torchcodec by reading audio in Python and passing arrays to the model. If you reintroduce a pipeline path that tries to decode directly from file internally, you may hit torchcodec again.

3) macOS urllib3 “LibreSSL” warning
This warning does not block the pipeline; it is commonly seen on macOS Python builds compiled with LibreSSL. You can ignore it unless HTTPS requests start failing.

Reproducibility
Reproducibility is ensured by:

Recording the exact dataset + split + parquet revision in verification_manifest.json

Recording the exact chosen segments and their boundaries

Using deterministic selection strategy (longest-first; tie-break by index)

If you want to regenerate the exact same verification set, keep the manifest and segment wavs under:
outputs/verification/_tmp_audio/

Directory layout (Part A)
pgsql
Copy code
part-a-asr/
  README.md
  requirements.txt
  requirements.lock.txt
  src/
    build_verification_fleurs.py
    text_normalize.py
    infer.py
    evaluate_wer.py
    train.py
  outputs/
    verification/
      verification.wav
      verification_gt_raw.txt
      verification_gt_clean.txt
      verification_manifest.json
      _tmp_audio/            # segment wavs used for the stitched verification.wav
    transcripts/
      raw.txt
      clean.txt
    metrics/
      wer_report.json
  docs/
    wer_methodology.md
    data_sources.md
    decisions.md
yaml
Copy code

---

## `docs/data_sources.md`

```md
# Data Sources (Part A)

This project uses the following datasets for Part A.

## 1) FLEURS (Somali) — Verification + Evaluation

- Dataset: `google/fleurs`
- Language: Somali (`so_so`)
- Split used: `test`
- Loading approach:
  - `revision="refs/convert/parquet"`
  - `data_dir="so_so"`

### Why FLEURS for verification/eval?
- Provides **paired audio + transcript** in a consistent format.
- Test split provides a stable evaluation target.
- Works well for creating a “verification clip” requirement because we can:
  - select a deterministic subset of utterances
  - stitch them into a single WAV
  - keep the ground-truth transcripts aligned per segment via a manifest

### Important note on parquet revision
Recent versions of `datasets` no longer support “dataset scripts” (Python dataset loaders). The parquet conversion branch is used to load FLEURS without relying on scripts.

---

## 2) skydheere/soomali-asr-dataset — Training volume (optional for Part A)

- Dataset: `skydheere/soomali-asr-dataset`
- Intended use: training/finetuning volume (not required to complete the Part A verification pipeline)
- Note: training and evaluation should remain separated; Part A evaluation is performed on the FLEURS test-derived verification set.

---

## How this repo uses data
- **Verification clip + GT**: derived from `google/fleurs` Somali test split
- **ASR inference**: executed per-segment listed in the verification manifest
- **WER evaluation**: compares hypothesis vs ground truth on the verification set

## Install
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Dataset references
- Training volume: `skydheere/soomali-asr-dataset`
- Verification: `google/fleurs` (Somali config `so_so`, use `test` split)

