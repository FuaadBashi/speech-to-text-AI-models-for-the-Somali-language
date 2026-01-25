# WER Methodology (Part A)

## What we compute
We compute Word Error Rate (WER) on the verification clip:

- **WER-clean**: compares model output vs `verification_gt_clean.txt`
- **WER-raw**: compares model output vs `verification_gt_raw.txt`

Both metrics are calculated after conservative text normalisation.

---

## Why we use a manifest + per-segment WER
The verification clip is stitched from multiple utterances. The ground truth is stored as **one line per utterance** (segment).

To avoid long-form transcription alignment issues, we do:

1) Build the stitched WAV for the “verification clip requirement”.
2) Also keep a **manifest** listing each segment used, in order.
3) Run ASR **per segment** and write **one hypothesis line per segment**.

This yields:
- `GT` has N lines
- `HYP` has N lines
- WER is computed line-aligned (robust and auditable)

---

## Text normalisation rules (conservative)
Implemented in `src/text_normalize.py`. The intent is to reduce superficial mismatch while not hiding substantive ASR errors.

Typical rules:
- Unicode normalisation (NFKC)
- Lowercasing
- Collapse repeated whitespace
- Strip leading/trailing whitespace
- Remove punctuation that does not affect word identity (implementation-specific)
- Keep language characters as-is (Somali Latin script)

---

## Computation
Implemented in `src/evaluate_wer.py` using `jiwer`.

Inputs:
- Ground truth:
  - `outputs/verification/verification_gt_clean.txt`
  - `outputs/verification/verification_gt_raw.txt`
- Hypothesis:
  - `outputs/transcripts/clean.txt`
  - `outputs/transcripts/raw.txt`

Output:
- `outputs/metrics/wer_report.json`

Additionally, the pipeline can emit per-segment diagnostics:
- `outputs/metrics/per_segment_report.csv`
- `outputs/metrics/per_segment_report.md`

---

## Reproducibility
- The verification set is fully defined by:
  - `outputs/verification/verification_manifest.json`
  - the segment wav files in `outputs/verification/_tmp_audio/`
- Any reviewer can re-run the same pipeline and reproduce the WER.
