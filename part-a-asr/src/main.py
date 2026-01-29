#!/usr/bin/env python3
"""
Main script to run all notebook cells in order
Converted from: LEGIT_Somali_ASR_Training_Complete.ipynb
"""

print("=" * 80)
print("🎙️  SOMALI ASR TRAINING PIPELINE")
print("=" * 80)

# Step 1: Setup and Installation
print("\n" + "=" * 80)
print("STEP 1: Setup and Installation")
print("=" * 80)
exec(open('setup_and_install.py').read())

# Step 2: Build Verification Clip
print("\n" + "=" * 80)
print("STEP 2: Build 5-Minute Verification Clip")
print("=" * 80)
exec(open('build_verification_clip.py').read())

# Step 3: Training - Imports and Config
print("\n" + "=" * 80)
print("STEP 3: Load Training Libraries and Configuration")
print("=" * 80)
exec(open('training_imports_and_config.py').read())

# Step 4: Training Configuration
print("\n" + "=" * 80)
print("STEP 4: Set Training Parameters")
print("=" * 80)
exec(open('training_configuration.py').read())

# Step 5: Run Training
print("\n" + "=" * 80)
print("STEP 5: Start Model Training")
print("=" * 80)
exec(open('training_run.py').read())

# Step 6: Evaluation Setup
print("\n" + "=" * 80)
print("STEP 6: Setup Evaluation")
print("=" * 80)
exec(open('evaluation_setup.py').read())

# Step 7: Comprehensive Evaluation
print("\n" + "=" * 80)
print("STEP 7: Run Comprehensive Evaluation")
print("=" * 80)
exec(open('evaluation_comprehensive.py').read())

# Note: Skipping download scripts (Colab-specific)
print("\n" + "=" * 80)
print("ℹ️  Skipping download scripts (download_results.py, download_package.py)")
print("   These are Google Colab-specific and not needed locally")
print("=" * 80)

print("\n" + "=" * 80)
print("✅ TRAINING PIPELINE COMPLETE")
print("=" * 80)
print("\n📂 Check outputs/ folder for results:")
print("  - outputs/final_model/          (trained model)")
print("  - outputs/verification/         (evaluation results)")
print("  - outputs/checkpoints/          (training checkpoints)")
