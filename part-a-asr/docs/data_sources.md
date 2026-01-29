# Data Sources (Part A)

This project uses **two distinct data roles**:
1) a **fixed verification artifact** for auditable evaluation (WER/CER), and
2) an **optional training corpus** to improve Somali ASR performance.

---

## 1) Verification clip (fixed evaluation artifact)

**Dataset:** `google/fleurs`  
**Language:** Somali (`so_so`)  
**Split:** `test`  
**Recommended loader:** `revision="refs/convert/parquet"`, `data_dir="so_so"`

### Why FLEURS is used for verification
- Provides **paired audio + transcripts** with standardised splits (audit-friendly ground truth).
- Suitable for the assessment requirement: prepare a **~5-minute verification clip** and compute WER against ground truth.
- Multi-utterance structure works well with a **manifest-driven** evaluation pipeline (one line per segment, line-aligned WER).

### Why we pin `revision="refs/convert/parquet"`
Some environments/tooling revisions restrict loading datasets via remote scripts. The parquet conversion branch allows loading dataset files without executing remote dataset scripts, improving reproducibility.

**We therefore load:**
- repo: `google/fleurs`
- `revision="refs/convert/parquet"`
- `data_dir="so_so"`

---

## 2) Training dataset (optional fine-tuning volume)

**Dataset:** `skydheere/soomali-asr-dataset`

### Intended use
- Used to **fine-tune** an ASR checkpoint (e.g., Wav2Vec2) to reduce WER on Somali.
- Training is **optional** for the deliverable: Part A can be completed using a fixed verification artifact + evaluation methodology, even without extra fine-tuning.

### Notes on reproducibility
- Training data is kept separate from verification to avoid evaluation leakage.
- All training/evaluation parameters should be recorded (seed, checkpoint, decoding config, text normalisation rules).

---

## Summary
- **Verification (auditable, fixed):** FLEURS Somali test split (~5-minute stitched clip built from multiple utterances)
- **Training (optional):** skydheere Somali ASR dataset (additional Somali speech volume)
