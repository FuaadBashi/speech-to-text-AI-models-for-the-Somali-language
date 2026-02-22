#!/bin/bash
echo "=========================================="
echo "Creating Working Configuration"
echo "=========================================="

cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform

# Backup
cp main.tf main.tf.backup_$(date +%Y%m%d_%H%M%S)

# Create provider config that doesn't do IAM lookups
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
  # Use hardcoded region string instead of variable to avoid lookup
  region     = "region-02"
  access_key = var.access_key
  secret_key = var.secret_key
  insecure   = true
  
  # Provide all endpoints explicitly to skip IAM discovery
  endpoints = {
    iam = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
    ecs = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs = "https://evs.htgcloud-region-02.htgclouds.com"
    elb = "https://elb.htgcloud-region-02.htgclouds.com"
    eip = "https://vpc.htgcloud-region-02.htgclouds.com"
    ims = "https://ims.htgcloud-region-02.htgclouds.com"
    obs = "https://obsv3.htgcloud-region-02.htgclouds.com"
    as  = "https://as.htgcloud-region-02.htgclouds.com"
  }
}
TFMAIN

echo "✅ Created provider configuration"
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
echo "Validating..."
terraform validate

if [ $? -ne 0 ]; then
    echo "❌ Validation failed"
    exit 1
fi

echo ""
echo "Creating plan..."
terraform plan -out=tfplan

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "🎉🎉🎉 SUCCESS! 🎉🎉🎉"
    echo "=========================================="
    echo ""
    echo "Terraform plan created successfully!"
    echo ""
    echo "Deploy with:"
    echo "  terraform apply tfplan"
    echo ""
else
    echo ""
    echo "❌ Plan failed"
    echo ""
    echo "If still getting IAM/project errors, you need to:"
    echo "1. Get the Project ID from WhatsApp"
    echo "2. Add this to main.tf in the provider block:"
    echo "   project_id = \"THE_PROJECT_ID_THEY_GIVE_YOU\""
    echo ""
fi

