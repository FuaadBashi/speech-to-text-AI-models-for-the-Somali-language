#!/bin/bash
echo "=========================================="
echo "Testing Provider Without Project Lookup"
echo "=========================================="

cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform

# Backup current config
cp main.tf main.tf.backup
cp terraform.tfvars terraform.tfvars.backup

# Try using tenant_name instead of project_name
cat > test_provider.tf << 'TFTEST'
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    hcs = {
      source  = "huaweicloud/hcs"
      version = "~> 2.4.0"
    }
  }
}

# Try with tenant_name instead of project_name
provider "hcs" {
  auth_url     = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  region       = "region-02"
  tenant_name  = "HTG-Workspace"  # Use tenant instead of project
  access_key   = var.access_key
  secret_key   = var.secret_key
  insecure     = true
  endpoints = {
    ecs = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs = "https://evs.htgcloud-region-02.htgclouds.com"
    elb = "https://elb.htgcloud-region-02.htgclouds.com"
    ims = "https://ims.htgcloud-region-02.htgclouds.com"
    obs = "https://obsv3.htgcloud-region-02.htgclouds.com"
  }
}

# Simple test - try to query availability zones
data "hcs_availability_zones" "test" {}

output "zones" {
  value = data.hcs_availability_zones.test.names
}
TFTEST

echo ""
echo "Test 1: Using tenant_name = 'HTG-Workspace'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
rm -rf .terraform .terraform.lock.hcl
terraform init -upgrade
terraform plan

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS with tenant_name!"
    mv test_provider.tf main.tf
    rm main.tf.backup terraform.tfvars.backup
    exit 0
fi

echo ""
echo "Test 2: Using domain_name instead"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > test_provider.tf << 'TFTEST2'
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
  auth_url     = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  region       = "region-02"
  domain_name  = "HTG-Workspace"
  access_key   = var.access_key
  secret_key   = var.secret_key
  insecure     = true
  endpoints = {
    ecs = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs = "https://evs.htgcloud-region-02.htgclouds.com"
    elb = "https://elb.htgcloud-region-02.htgclouds.com"
    ims = "https://ims.htgcloud-region-02.htgclouds.com"
    obs = "https://obsv3.htgcloud-region-02.htgclouds.com"
  }
}

data "hcs_availability_zones" "test" {}

output "zones" {
  value = data.hcs_availability_zones.test.names
}
TFTEST2

rm -rf .terraform .terraform.lock.hcl
terraform init -upgrade
terraform plan

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS with domain_name!"
    mv test_provider.tf main.tf
    rm main.tf.backup terraform.tfvars.backup
    exit 0
fi

echo ""
echo "Test 3: Skip project/tenant entirely (AK/SK only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > test_provider.tf << 'TFTEST3'
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
  auth_url     = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  region       = "region-02"
  # No project/tenant - rely on AK/SK scoping
  access_key   = var.access_key
  secret_key   = var.secret_key
  insecure     = true
  endpoints = {
    ecs = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs = "https://evs.htgcloud-region-02.htgclouds.com"
    elb = "https://elb.htgcloud-region-02.htgclouds.com"
    ims = "https://ims.htgcloud-region-02.htgclouds.com"
    obs = "https://obsv3.htgcloud-region-02.htgclouds.com"
  }
}

data "hcs_availability_zones" "test" {}

output "zones" {
  value = data.hcs_availability_zones.test.names
}
TFTEST3

rm -rf .terraform .terraform.lock.hcl
terraform init -upgrade
terraform plan

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS without project scoping!"
    mv test_provider.tf main.tf
    rm main.tf.backup terraform.tfvars.backup
    exit 0
fi

# Restore original files
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "❌ All tests failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mv main.tf.backup main.tf
mv terraform.tfvars.backup terraform.tfvars
rm test_provider.tf

echo ""
echo "The IAM endpoint seems inaccessible or incompatible."
echo ""
echo "RECOMMENDATION: Contact Felix/provider and share:"
echo "  'The IAM API endpoint returns APIGW.0101 error."
echo "   Can you verify the correct authentication method?"
echo "   Should I use project_name, tenant_name, or just AK/SK?'"
echo ""

