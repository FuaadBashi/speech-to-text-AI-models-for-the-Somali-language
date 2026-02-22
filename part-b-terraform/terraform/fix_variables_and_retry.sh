#!/bin/bash
echo "=========================================="
echo "Fixing Variables and Retrying"
echo "=========================================="

cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform

# Make sure variables.tf has region variable
if ! grep -q 'variable "region"' variables.tf; then
    cat >> variables.tf << 'VARS'

variable "region" {
  description = "HTG Cloud region"
  type        = string
  default     = "region-02"
}
VARS
fi

# Make sure terraform.tfvars has region
if ! grep -q '^region' terraform.tfvars; then
    echo 'region = "region-02"' >> terraform.tfvars
fi

echo "✅ Variables configured"
echo ""

# Clean and retry
rm -rf .terraform.lock.hcl terraform.tfstate* tfplan

echo "Running terraform plan..."
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
    echo "❌ Still failing. Output above shows the error."
    echo ""
    echo "If it's still a project/authentication error,"
    echo "send this WhatsApp message:"
    echo ""
    cat << 'MSG'
"Hi, I need the Project ID for 'htgcloud-region-02_ai-devops-assessment'.

I cannot find it in the HTG Cloud console. Could you please provide 
the exact Project ID value that I should use in Terraform?

Thank you!"
MSG
    echo ""
fi

