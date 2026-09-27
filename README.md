# Somali Speech Recognition and Cloud Infrastructure

An assessment project with two components: a Somali ASR training/evaluation workflow and Terraform infrastructure for Huawei Cloud Stack.

## Start here

| Component | Documentation | Source |
| --- | --- | --- |
| Speech recognition | [Part A overview](part-a-asr/README.md) | [ASR scripts](part-a-asr/src) |
| Evaluation | [WER methodology](part-a-asr/docs/wer_methodology.md) | [Evaluation script](part-a-asr/src/evaluation_comprehensive.py) |
| Data provenance | [Data sources](part-a-asr/docs/data_sources.md) | [Verification-clip builder](part-a-asr/src/build_verification_clip.py) |
| Infrastructure | [Terraform guide](part-b-terraform/terraform/README.md) | [Terraform configuration](part-b-terraform/terraform) |
| Deployment details | [Deployment guide](part-b-terraform/terraform/DEPLOYMENT_GUIDE.md) | [Variables](part-b-terraform/terraform/variables.tf) |

## ASR workflow

```bash
git clone https://github.com/FuaadBashi/speech-to-text-AI-models-for-the-Somali-language.git
cd speech-to-text-AI-models-for-the-Somali-language
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r part-a-asr/requirements.txt
```

Review the [training configuration](part-a-asr/src/training_configuration.py) and setup scripts before training. The workflow was converted from notebook cells, depends on external datasets/models, and can require a GPU and FFmpeg. Its entry point runs sibling scripts relative to the current working directory:

```bash
cd part-a-asr/src
python main.py
```

## Infrastructure workflow

From the repository root, inspect `part-b-terraform/terraform` and its example variables before configuring a cloud account. Initialization and validation use:

```bash
cd part-b-terraform/terraform
terraform init
terraform validate
```

These commands do not establish that a deployment is running. Some configurations are stored with `.disabled` or `.backup` suffixes; Terraform does not load those as active `.tf` resources.

## Results and reproducibility

The earlier README reported **7.41% WER** on a verification clip. That is a historical reported result, not a result reproduced by this documentation pass. The checked-in methodology distinguishes raw and normalized transcripts, overall WER, and average segment WER. Reproduce and retain the checkpoint, clip manifest, references, hypotheses, and scoring configuration before quoting a benchmark.

The repository demonstrates ASR experimentation and infrastructure-as-code work. Production readiness and a currently deployed resource count are not established here.
