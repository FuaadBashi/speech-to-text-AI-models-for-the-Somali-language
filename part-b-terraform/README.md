# Part B — Terraform (Huawei Cloud / HTG) + Apache Demo App

This scaffold provides a production-style Terraform layout.
You must adapt provider configuration (region/credentials/endpoints) to the environment you were given.

## Target architecture (assessment-aligned)
- VPC + subnets (public + private)
- Security Groups (least privilege)
- Public IP / internet access (e.g., EIP for LB)
- VPN gateway + connection
- ECS instances with Auto Scaling Group
- Elastic Load Balancer in front of ECS
- Managed DB service (RDS)
- Apache + simple app that prints hostname/instance metadata to demonstrate load balancing

## Structure
- `modules/` contains reusable building blocks
- `envs/dev/` is the root module wiring the modules together
- `user_data/` contains cloud-init/bootstrap assets for Apache + demo app

## Getting started (high level)
1. Configure credentials (environment variables or provider block).
2. Choose provider:
   - `huaweicloud/huaweicloud` (public cloud) OR
   - `huaweicloud/hcso` (Huawei Cloud Stack Online)
3. Edit `envs/dev/terraform.tfvars.example` and create `envs/dev/terraform.tfvars` (do NOT commit).
4. Run:
   ```bash
   cd envs/dev
   terraform init
   terraform fmt -recursive
   terraform validate
   terraform plan
   terraform apply
   ```

## Demo app validation
After apply:
- Browse the Load Balancer public IP on port 80.
- Refresh multiple times: hostname/instance-id should vary across instances.

## References
- Terraform module structure (HashiCorp)
- Huawei provider resource docs for ELB/RDS/ECS/AS

