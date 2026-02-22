#!/bin/bash
echo "=========================================="
echo "Switch to Using Project ID"
echo "=========================================="

cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform

echo ""
echo "Enter the Project ID you found in HTG Cloud console:"
echo "(It should be a long string like: bb2e17e822bd425b6d4e4cb0a0e1f581)"
echo ""
read -p "Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Project ID provided"
    exit 1
fi

echo ""
echo "Using Project ID: $PROJECT_ID"
echo ""

# Backup current files
cp main.tf main.tf.backup_before_project_id
cp variables.tf variables.tf.backup_before_project_id
cp terraform.tfvars terraform.tfvars.backup_before_project_id

# Update main.tf to use project_id instead of project_name
cat > main.tf << TFMAIN
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
  auth_url   = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  region     = "region-02"
  project_id = var.project_id  # Using project_id instead of project_name
  access_key = var.access_key
  secret_key = var.secret_key
  insecure   = true
  
  endpoints = {
    iam = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
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

# Add project_id variable to variables.tf if it doesn't exist
if ! grep -q "variable \"project_id\"" variables.tf; then
    cat >> variables.tf << 'TFVARS'

variable "project_id" {
  description = "HTG Cloud Project ID"
  type        = string
}
TFVARS
fi

# Remove project_name variable if it exists
sed -i '' '/variable "project_name"/,/^}/d' variables.tf

# Update terraform.tfvars
cat > terraform.tfvars << TFVARSCONTENT
# HTG Cloud Configuration
project_id = "$PROJECT_ID"

# Credentials (from HTG_CLOUD_VALUES.txt)
access_key = "DHAWLD4BCTYRLU61VB4R"
secret_key = "ND2Xv3V8XIPoJ0Mfdfe3cHAMuC6o9IBZm142JbX6"

# Region Configuration
region            = "region-02"
availability_zone = "hq3_AZ1"

# Network Configuration
vpc_cidr   = "172.16.0.0/16"
subnet_cidr = "172.16.1.0/24"

# Compute Configuration
web_instance_count = 2
web_flavor         = "c3.large.2"
db_flavor          = "c3.large.2"

# Image Configuration
image_name = "Ubuntu 20.04 server 64bit"

# Tags
environment = "production"
project     = "ai-devops"
TFVARSCONTENT

echo "✅ Updated configuration files to use project_id"
echo ""

# Clean slate
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* tfplan

echo "Initializing Terraform..."
terraform init

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Init failed"
    exit 1
fi

echo ""
echo "Validating configuration..."
terraform validate

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Validation failed"
    exit 1
fi

echo ""
echo "Creating execution plan..."
terraform plan -out=tfplan

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "🎉🎉🎉 SUCCESS! 🎉🎉🎉"
    echo "=========================================="
    echo ""
    echo "Terraform plan created successfully!"
    echo ""
    echo "Review the plan above, then deploy with:"
    echo ""
    echo "  cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform"
    echo "  terraform apply tfplan"
    echo ""
else
    echo ""
    echo "❌ Plan failed - check the errors above"
    echo ""
    echo "If still failing, reply to the WhatsApp message with:"
    echo "  'Still getting errors with project_id. Can you double-check"
    echo "   the exact value I should use?'"
fi

