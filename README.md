# AI & DevOps Technical Assessment — Scaffold

This repository is a **submission-ready scaffold** for the assessment described in *AI & DevOps Technical Assessment.pdf*.
It includes:
- **Part A (ASR / Somali)**: scripts for building a 5+ minute verification clip (FLEURS test), running Whisper inference,
  and computing WER with a documented normalisation pipeline.
- **Part B (Terraform / Huawei Cloud / HTG)**: a production-style Terraform layout with modules for network, security,
  VPN, compute+autoscaling, load balancer, and managed DB, plus instance bootstrap assets for an Apache demo app.

**Generated:** 2026-01-25T11:05:36Z

---

## Quick start (VS Code)

1. Download/unzip the repository.
2. Open the folder in VS Code.
3. Follow Part A and Part B READMEs:

- Part A: `part-a-asr/README.md`
- Part B: `part-b-terraform/README.md`

---

## Notes
- This scaffold focuses on clean structure and reproducibility. Replace `TODO:` sections with your final implementation details.
- Keep secrets out of Git: use `terraform.tfvars` (not committed), environment variables, or a secrets manager.

