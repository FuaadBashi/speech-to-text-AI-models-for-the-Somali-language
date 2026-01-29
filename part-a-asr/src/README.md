# Somali ASR Training - Source Files

Converted from: `LEGIT_Somali_ASR_Training_Complete.ipynb`

## 📁 Files

### Core Pipeline Files (run in order)

1. **`setup_and_install.py`** - Install dependencies and create directories
2. **`build_verification_clip.py`** - Build 5-minute verification audio with manifest
3. **`training_imports_and_config.py`** - Import libraries and load dataset
4. **`training_configuration.py`** - Set training hyperparameters
5. **`training_run.py`** - Start model training (~1 hour)
6. **`evaluation_setup.py`** - Setup evaluation framework
7. **`evaluation_comprehensive.py`** - Run comprehensive WER evaluation

### Utility Files

- **`download_results.py`** - Download results (Google Colab only)
- **`download_package.py`** - Download package (Google Colab only)

### Main Script

- **`main.py`** - Run all steps automatically

## 🚀 Usage

### Option 1: Run Complete Pipeline

```bash
python main.py
```

This will run all steps from setup to evaluation automatically.

### Option 2: Run Individual Steps

```bash
# Step 1: Setup
python setup_and_install.py

# Step 2: Build verification clip
python build_verification_clip.py

# Step 3: Import and configure
python training_imports_and_config.py

# Step 4: Set training parameters
python training_configuration.py

# Step 5: Train model
python training_run.py

# Step 6: Setup evaluation
python evaluation_setup.py

# Step 7: Evaluate model
python evaluation_comprehensive.py
```

### Option 3: Run Only Specific Parts

```bash
# Just build verification clip
python build_verification_clip.py

# Just run evaluation (after training)
python evaluation_setup.py
python evaluation_comprehensive.py
```

## 📊 Expected Results

After running the complete pipeline:

```
📊 EVALUATION RESULTS
════════════════════════════════════════════
🎯 Word Error Rate (WER):
  Overall: 9.09%
  Average: 7.41%

🎉 ✅ TARGET ACHIEVED! (WER ≤ 10%)
════════════════════════════════════════════
```

## 📂 Output Structure

```
outputs/
├── verification/
│   ├── verification.wav              (5-minute audio)
│   ├── verification_manifest.json    (segment info)
│   ├── evaluation_results.json       (WER metrics)
│   ├── detailed_evaluation_all_segments.json
│   ├── detailed_evaluation_all_segments.csv
│   └── full_comparison_all_129_segments.txt
├── final_model/                      (trained model)
├── checkpoints/                      (training checkpoints)
└── logs/                             (training logs)
```

## ⚙️ Requirements

Install before running:

```bash
pip install datasets==2.19.0 transformers==4.44.2 accelerate==0.34.2 \
    evaluate==0.4.2 soundfile librosa jiwer sentencepiece scipy
```

Or if you have a requirements.txt:

```bash
pip install -r requirements.txt
```

## 💡 Notes

- **Training time**: ~1 hour on GPU, 3-4 hours on CPU
- **GPU required**: Highly recommended for training
- **Download scripts**: Only work in Google Colab, skip them locally
- **Run in order**: Steps depend on previous steps

## 🐛 Troubleshooting

**Import errors?**
```bash
pip install --upgrade datasets transformers accelerate
```

**CUDA out of memory?**
- Reduce batch size in `training_configuration.py`

**Audio decoding errors?**
```bash
# Install ffmpeg
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
```

## 📚 Original Source

This code was converted from the Jupyter notebook:
`LEGIT_Somali_ASR_Training_Complete.ipynb`

Each `.py` file corresponds to a cell in the original notebook, with descriptive names for clarity.
