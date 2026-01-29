# Quick Start Guide

Get your infrastructure running in 15 minutes.

## 1. Prerequisites ✅

- [ ] Terraform installed (`terraform version`)
- [ ] Huawei Cloud account
- [ ] Access Key & Secret Key
- [ ] SSH key pair created in Huawei Cloud
- [ ] Your public IP address

## 2. Configure (2 minutes)

```bash
cd terraform/

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Required values**:
```hcl
access_key    = "YOUR_ACCESS_KEY"
secret_key    = "YOUR_SECRET_KEY"
key_pair_name = "my-ssh-key"
admin_cidr    = "YOUR_IP/32"
db_password   = "SecurePass123!"
```

## 3. Deploy (10 minutes)

```bash
# Initialize
terraform init

# Deploy everything
terraform apply

# Type: yes
```

## 4. Test (3 minutes)

```bash
# Get load balancer URL
terraform output load_balancer_url

# Open in browser
# Refresh multiple times - hostname should change
```

## 5. Common Commands

```bash
# See all outputs
terraform output

# See plan without applying
terraform plan

# Destroy everything
terraform destroy
```

## 6. Troubleshooting

**Can't access load balancer?**
- Wait 5 minutes for instances to boot
- Check: `terraform output load_balancer_url`

**Terraform errors?**
- Check credentials in terraform.tfvars
- Verify key pair exists in Huawei Cloud
- Run: `terraform init` again

**Need help?**
- Read: DEPLOYMENT_GUIDE.md (detailed)
- Read: README.md (comprehensive)

## Architecture at a Glance

```
Internet
   ↓
Load Balancer (Public IP)
   ↓
2-4 Web Servers (Private Subnet)
   ↓
MySQL Database (Private Subnet)
   
Admin Access: VPN Server (Public IP)
```

## What Gets Created

- ✅ VPC with public/private subnets
- ✅ Load Balancer with public IP
- ✅ Auto Scaling Group (2-4 instances)
- ✅ MySQL Database (RDS)
- ✅ NAT Gateway
- ✅ VPN Server
- ✅ Security Groups

## Cost Estimate

Approximate monthly cost (varies by region):
- ECS instances (2-4): $30-60
- Load Balancer: $15
- Database (small): $25
- Bandwidth: $10-30
- **Total**: ~$80-130/month

💡 **Tip**: Run `terraform destroy` when not using to avoid charges!

---

**Need detailed instructions?** See `DEPLOYMENT_GUIDE.md`
