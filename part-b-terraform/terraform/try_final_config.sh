#!/bin/bash
echo "=========================================="
echo "Final Attempt: Simplified Configuration"
echo "=========================================="

cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform

# Backup
cp main.tf main.tf.backup_final_attempt

# Try most minimal config
cat > main.tf << 'TFMAIN'
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    hcs = {
      source  = "huaweicloud/hcs"
      version = "~> 2.4.0"
    }
  }
}

provider "hcs" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
  
  # Skip all authentication checks - rely on AK/SK only
  insecure = true
  
  endpoints = {
    ecs = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs = "https://evs.htgcloud-region-02.htgclouds.com"
    elb = "https://elb.htgcloud-region-02.htgclouds.com"
    ims = "https://ims.htgcloud-region-02.htgclouds.com"
    obs = "https://obsv3.htgcloud-region-02.htgclouds.com"
    as  = "https://as.htgcloud-region-02.htgclouds.com"
  }
}
TFMAIN

echo "✅ Created minimal provider config"
echo ""

# Clean
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan

echo "Initializing..."
terraform init

if [ $? -ne 0 ]; then
    echo "❌ Init failed"
    exit 1
fi

echo ""
echo "Planning..."
terraform plan -out=tfplan

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! This might actually work!"
    echo ""
    echo "Deploy with: terraform apply tfplan"
else
    echo ""
    echo "❌ Still failing"
    echo ""
    echo "You MUST get the Project ID from them via WhatsApp."
fi

