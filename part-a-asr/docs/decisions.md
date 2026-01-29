# Decisions Log

This document records the *why* behind major design choices (datasets, models, decoding, evaluation, and reproducibility).

---

## 1) Model choice

### Primary: Wav2Vec2 (XLS-R family)
**Why**
- Strong baseline for low-resource ASR adaptation.
- Fine-tuning is feasible on modest compute and integrates cleanly with Hugging Face tooling.

**What we record**
- Exact checkpoint name + revision
- Sampling rate assumptions
- Feature extractor + tokenizer details
- Decoding method (greedy vs LM-assisted, if any)

### Secondary: Whisper (optional comparison)
**Why**
- Whisper provides a robust reference model and is commonly used in speech tasks.
- Useful for sanity-checking transcription quality and error patterns.

---

## 2) Verification dataset: FLEURS Somali test split

**Decision:** use `google/fleurs` (`so_so`, `test`) as the fixed evaluation artifact.

**Why**
- Standardised ground truth and splits support auditability.
- Enables a clear “verification clip + ground truth + WER methodology” submission.

**Implementation note**
- Prefer parquet conversion revision for stable loading across environments.

---

## 3) Why manifest-driven evaluation (segment-by-segment)

**Decision:** do *not* compute WER from one long-form transcript of the stitched clip.

**Why**
- The verification clip is constructed from multiple utterances.
- Long-form inference can introduce alignment drift (insertions/deletions that shift the rest of the transcript).
- Line-aligned scoring is more robust and easier to audit:
  - GT has N lines (one per segment)
  - HYP has N lines (one per segment)
  - WER is computed on aligned lines

---

## 4) Text normalisation policy

**Decision:** report both RAW and CLEAN scoring.

- **RAW**: minimal handling (preserve most punctuation/casing; still normalise whitespace).
- **CLEAN**: conservative normalisation to remove superficial mismatches without hiding true ASR errors.

**CLEAN rules (principles)**
- Unicode normalisation (e.g., NFKC)
- Lowercasing
- Whitespace collapse
- Strip leading/trailing whitespace
- Remove punctuation that does not change word identity
- Preserve Somali Latin characters (do not transliterate)

All rules are implemented in a single normalisation module to keep scoring consistent and reproducible.

---

## 5) Reproducibility & evidence

**Decision:** every submission must be replayable and provable.

Minimum reproducibility artifacts:
- Verification manifest (segment order + source IDs)
- Ground truth files (raw + clean)
- Hypothesis files (raw + clean)
- Metrics report JSON + per-segment diagnostics
- Fixed model identifier + decoding config
- Command sequence to reproduce results from a fresh environment

---

## 6) Known environment pitfalls (recorded for reviewers)

- If dataset/audio loading fails due to dependency issues, prefer deterministic loaders and explicitly list system dependencies (e.g., ffmpeg).
- If cloud deployment is blocked by account verification/payment gating, record screenshots and provide IaC code as evidence of completion attempt.
