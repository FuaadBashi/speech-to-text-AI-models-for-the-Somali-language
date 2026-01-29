# WER Methodology (Part A)

This project evaluates Somali ASR quality using Word Error Rate (WER) on a fixed verification clip.

---

## 1) What we compute

We compute WER on the verification clip in two modes:

- **WER-clean:** hypothesis vs `verification_gt_clean.txt`
- **WER-raw:** hypothesis vs `verification_gt_raw.txt`

Optionally we also compute **CER** (Character Error Rate) as a supporting metric.

---

## 2) Why we use a manifest + per-segment WER

The verification clip is stitched from multiple utterances, but the ground truth exists naturally as **one transcript per utterance**.

To keep evaluation auditable and robust:

1) Build the stitched WAV to meet the “~5-minute verification clip” requirement.
2) Maintain a **manifest** listing each segment used (in order).
3) Run ASR **per segment**, producing **one hypothesis line per segment**.

This guarantees:
- GT has N lines
- HYP has N lines
- WER can be computed line-aligned (prevents long-form alignment drift)

---

## 3) Definitions and reporting

### Overall WER
Computed by concatenating all reference words and all hypothesis words across the full clip, then computing:

WER = (S + D + I) / N

Where:
- S = substitutions
- D = deletions
- I = insertions
- N = number of reference words

### Average segment WER
Computed by taking the mean WER across segments (each segment scored independently).
This helps identify whether errors are concentrated in a subset of utterances.

We report both because they answer different questions:
- **Overall WER**: “How good is the system on the whole clip?”
- **Avg segment WER**: “Are errors spiky / concentrated?”

---

## 4) Text normalisation (conservative)

Implemented in a single normalisation module.

Typical rules:
- Unicode normalisation (NFKC)
- Lowercasing
- Collapse repeated whitespace
- Strip leading/trailing whitespace
- Remove punctuation that does not affect word identity (implementation-defined)
- Preserve Somali Latin script characters

We report RAW and CLEAN to keep scoring honest.

---

## 5) Inputs and outputs

### Inputs
- Ground truth:
  - `outputs/verification/verification_gt_clean.txt`
  - `outputs/verification/verification_gt_raw.txt`
- Hypothesis:
  - `outputs/transcripts/clean.txt`
  - `outputs/transcripts/raw.txt`

### Outputs
- `outputs/metrics/wer_report.json`
- Optional diagnostics:
  - `outputs/metrics/per_segment_report.csv`
  - `outputs/metrics/per_segment_report.md`

---

## 6) Reproducibility

A reviewer can reproduce the evaluation because:
- the verification set is defined by the manifest:
  - `outputs/verification/verification_manifest.json`
- the exact segments used are preserved:
  - `outputs/verification/_tmp_audio/` (segment WAVs)

Re-running the pipeline regenerates the hypotheses and the WER report deterministically (given the same model checkpoint + decoding config).
