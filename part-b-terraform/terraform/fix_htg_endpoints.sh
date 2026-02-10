#!/bin/bash
# HTG Cloud Endpoint Fix - Corrected Version
# This script properly configures Terraform to use HTG Cloud's custom endpoints

set -e  # Exit on error

echo "=========================================="
echo "HTG Cloud Endpoint Configuration Fix"
echo "=========================================="
echo ""

TERRAFORM_DIR="$HOME/Desktop/ai-devops-assessment/part-b-terraform/terraform"
cd "$TERRAFORM_DIR"

# Step 1: Backup current main.tf
echo "Step 1: Creating backup..."
if [ -f "main.tf" ]; then
    cp main.tf "main.tf.backup_$(date +%Y%m%d_%H%M%S)"
    echo "✓ Backup created"
else
    echo "⚠ No existing main.tf found"
fi

# Step 2: Create corrected main.tf with proper endpoint syntax
echo ""
echo "Step 2: Creating corrected main.tf with HTG Cloud endpoints..."
cat > main.tf << 'EOF'
terraform {
  required_version = ">= 1.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.86.0"
    }
  }
}

provider "huaweicloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = var.region
  auth_url   = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com/v3"
  insecure   = true
  
  # Custom HTG Cloud endpoints - individual arguments
  ecs_endpoint = "https://ecs-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  vpc_endpoint = "https://vpc-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  elb_endpoint = "https://elb-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  rds_endpoint = "https://rds-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  as_endpoint  = "https://as-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  nat_endpoint = "https://nat-apigateway-proxy.htgcloud-region-02.htgclouds.com"
}
EOF
echo "✓ Created main.tf with custom HTG Cloud endpoints"

# Step 3: Ensure all required variables exist
echo ""
echo "Step 3: Checking for required variables..."
if ! grep -q "variable \"access_key\"" variables.tf; then
    echo "Adding access_key variable..."
    cat >> variables.tf << 'EOF'

variable "access_key" {
  description = "HTG Cloud Access Key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "HTG Cloud Secret Key"
  type        = string
  sensitive   = true
}
EOF
    echo "✓ Added authentication variables"
else
    echo "✓ Variables already exist"
fi

# Step 4: Validate configuration
echo ""
echo "Step 4: Validating Terraform configuration..."
terraform validate
VALIDATE_STATUS=$?

if [ $VALIDATE_STATUS -eq 0 ]; then
    echo ""
    echo "✓ Validation successful!"
else
    echo ""
    echo "⚠ Validation failed. Check errors above."
    exit 1
fi

# Step 5: Test with terraform plan
echo ""
echo "Step 5: Testing connection to HTG Cloud..."
echo "(This will attempt to connect using the custom endpoints)"
echo ""

terraform plan -out=tfplan 2>&1 | tee plan_output.log

# Check if plan was successful
if grep -q "Plan:" plan_output.log; then
    echo ""
    echo "=========================================="
    echo "🎉 SUCCESS! HTG Cloud connection working!"
    echo "=========================================="
    echo ""
    echo "Your infrastructure is ready to deploy:"
    grep "Plan:" plan_output.log
    echo ""
    echo "To deploy, run:"
    echo "  terraform apply tfplan"
    echo ""
elif grep -q "no such host" plan_output.log; then
    echo ""
    echo "=========================================="
    echo "⚠️  Endpoint Resolution Issue Detected"
    echo "=========================================="
    echo ""
    echo "The custom endpoints are configured correctly, but DNS resolution"
    echo "may still be failing. This could be due to:"
    echo ""
    echo "1. Network connectivity to HTG Cloud"
    echo "2. Incorrect endpoint URLs"
    echo "3. HTG Cloud infrastructure issues"
    echo ""
    echo "Next steps:"
    echo "  - Verify you can access https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
    echo "  - Contact HTG Cloud support for correct endpoint URLs"
    echo "  - Check if VPN/network access is required"
elif grep -q "Authentication failed" plan_output.log; then
    echo ""
    echo "=========================================="
    echo "⚠️  Authentication Issue"
    echo "=========================================="
    echo ""
    echo "Endpoints are reachable but authentication failed."
    echo "Check your access_key and secret_key in terraform.tfvars"
else
    echo ""
    echo "=========================================="
    echo "⚠️  Unexpected Error"
    echo "=========================================="
    echo ""
    echo "Check plan_output.log for details"
fi

echo ""
echo "=========================================="
echo "Fix script completed"
echo "=========================================="
