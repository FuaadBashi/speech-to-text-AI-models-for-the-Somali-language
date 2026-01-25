# Data Sources (Part A)

## Verification clip (fixed evaluation artifact)
**Dataset:** `google/fleurs`  
**Language:** Somali (`so_so`)  
**Split:** `test`  
**Revision used:** `refs/convert/parquet`

### Why this dataset is used for verification
- It provides **consistent audio + transcripts** suitable for objective WER evaluation.
- It is a standard multilingual benchmark dataset with well-defined splits.
- The assessment requires a **5+ minute verification clip** with an auditable ground truth transcript.

### Why `revision="refs/convert/parquet"`
Recent versions of the Hugging Face `datasets` library no longer support dataset **loading via remote dataset scripts** in the same way as older versions. The parquet conversion branch provides dataset files in a format that can be loaded without executing dataset scripts.

We therefore load:
- repo: `google/fleurs`
- `revision="refs/convert/parquet"`
- `data_dir="so_so"`

---

## Training dataset (optional fine-tuning volume)
**Dataset:** `skydheere/soomali-asr-dataset`

### Intended use
- This dataset is used only if we decide to **fine-tune** a Whisper checkpoint to reduce WER on Somali.
- Training is not required to produce a valid Part A deliverable; the baseline pipeline works end-to-end without it.

---

## Summary
- Verification: FLEURS Somali test (auditable, fixed)
- Training (optional): skydheere Somali ASR dataset (volume)
