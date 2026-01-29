# Somali ASR Infrastructure - Terraform Deployment

Complete Terraform configuration for deploying a production-ready, auto-scaling web infrastructure on Huawei Cloud.

## 🏗️ Architecture Overview

This infrastructure deploys:

- **VPC**: `10.0.0.0/16` with public and private subnets
- **Public Subnet** (`10.0.1.0/24`): Load Balancer, NAT Gateway, VPN Server
- **Private Subnet** (`10.0.2.0/24`): Auto-scaled Web Servers, RDS MySQL
- **Load Balancer**: Public-facing ELB with health checks
- **Auto Scaling**: Min 2, Max 4 instances with CPU-based scaling
- **Database**: RDS MySQL 8.0 in private subnet
- **Security**: Layered security groups with principle of least privilege
- **VPN**: OpenVPN server for secure admin access

## 📋 Prerequisites

### 1. Install Required Tools

- **Terraform** >= 1.0 ([Download](https://www.terraform.io/downloads))
- **Git** (optional but recommended)
- **SSH client** (built-in on Mac/Linux)

### 2. Huawei Cloud Account Setup

1. **Create IAM Credentials**:
   - Log into Huawei Cloud Console
   - Navigate to: My Credentials → Access Keys
   - Create new Access Key/Secret Key pair
   - Save these securely (you'll need them in `terraform.tfvars`)

2. **Create SSH Key Pair**:
   - Console → Elastic Cloud Server → Key Pairs
   - Create new key pair (e.g., `my-ssh-key`)
   - Download the `.pem` file
   - Set permissions: `chmod 400 my-ssh-key.pem`

3. **Required Permissions**:
   Ensure your IAM user has permissions for:
   - VPC, Subnet, Security Groups
   - ECS (Elastic Cloud Server)
   - ELB (Elastic Load Balancer)
   - AS (Auto Scaling)
   - RDS (Relational Database Service)
   - VPN Gateway
   - EIP (Elastic IP)

## 🚀 Quick Start

### Step 1: Clone and Configure

```bash
# Clone or create the directory
mkdir -p somali-asr-infra
cd somali-asr-infra

# Copy the example tfvars file
cp terraform.tfvars.example terraform.tfvars

# Edit with your credentials
nano terraform.tfvars
```

### Step 2: Edit `terraform.tfvars`

```hcl
access_key    = "YOUR_ACTUAL_ACCESS_KEY"
secret_key    = "YOUR_ACTUAL_SECRET_KEY"
region        = "ap-southeast-1"
key_pair_name = "my-ssh-key"
admin_cidr    = "YOUR_PUBLIC_IP/32"  # Find at https://whatismyip.com
db_password   = "YourSecurePassword123!"
```

### Step 3: Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Format and validate
terraform fmt
terraform validate

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply
```

## 📊 Incremental Deployment Strategy

For easier troubleshooting, deploy in phases:

### Phase 1: Network Foundation
Deploy only VPC and subnets first:
```bash
# Comment out all resources except in network.tf
terraform apply
```

### Phase 2: Security Groups
```bash
# Uncomment security.tf resources
terraform apply
```

### Phase 3: Test Single Instance
```bash
# Set count = 1 in compute.tf
terraform apply
# Test: curl http://<test-instance-ip>
```

### Phase 4: Load Balancer
```bash
# Uncomment loadbalancer.tf
# Uncomment member resources
terraform apply
```

### Phase 5: Auto Scaling
```bash
# Set test instance count = 0
# Deploy autoscaling.tf
terraform apply
```

### Phase 6: Database
```bash
# Deploy database.tf
terraform apply
```

### Phase 7: VPN
```bash
# Deploy vpn.tf
terraform apply
```

## 🎯 Testing the Deployment

### 1. Verify Load Balancing

```bash
# Get load balancer IP from outputs
terraform output load_balancer_url

# Test multiple times to see different hostnames
curl http://<load-balancer-ip>
curl http://<load-balancer-ip>
curl http://<load-balancer-ip>
```

Each request should show a different hostname/instance ID, proving load balancing works.

### 2. Test Auto Scaling

**Generate CPU load** (from any instance or external machine):

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Generate load
ab -n 10000 -c 100 http://<load-balancer-ip>/

# Watch scaling in Huawei Cloud Console
# Auto Scaling → Scaling Groups → Instance List
```

**Monitor scaling**:
- Watch instance count increase when CPU > 70%
- Watch instance count decrease when CPU < 30%

### 3. Test Database Connectivity

SSH into a web server and test database:

```bash
# SSH to VPN first
ssh -i my-ssh-key.pem ubuntu@<vpn-ip>

# From VPN, SSH to a web server
ssh ubuntu@<private-web-server-ip>

# Test database connection
sudo apt install mysql-client
mysql -h <database-endpoint> -u admin -p
```

### 4. Configure VPN Access

**On VPN Server**:

```bash
# SSH to VPN server
ssh -i my-ssh-key.pem ubuntu@<vpn-ip>

# Run OpenVPN installation script
wget https://git.io/vpn -O openvpn-install.sh
sudo bash openvpn-install.sh

# Follow prompts:
# - Accept defaults
# - Create client configuration

# Download client config
scp -i my-ssh-key.pem ubuntu@<vpn-ip>:/root/client.ovpn .
```

**On Your Machine**:

```bash
# Install OpenVPN client
# Mac: brew install openvpn
# Ubuntu: sudo apt install openvpn
# Windows: Download from openvpn.net

# Connect
sudo openvpn client.ovpn
```

## 📸 Required Screenshots for Assessment

Take these screenshots during testing:

1. **terraform-apply-success.png**: Terminal showing successful `terraform apply`
2. **load-balancer-working.png**: Browser showing the application via LB IP
3. **different-hostnames.png**: Two browser tabs showing different hostnames
4. **auto-scaling-instances.png**: Console showing 2→3/4 instances under load
5. **database-created.png**: RDS console showing database details
6. **vpn-connected.png**: VPN client connected with route information

Save to `screenshots/` directory.

## 🔧 Troubleshooting

### Terraform Issues

**Terraform init fails**:
```bash
# Check internet connectivity
ping registry.terraform.io

# Clear cache and retry
rm -rf .terraform
terraform init
```

**Apply hangs**:
```bash
# Ctrl+C to stop
# Check resource status in console
terraform show
# Remove lock if needed (ONLY if certain)
terraform force-unlock <lock-id>
```

**Plan shows unexpected changes**:
```bash
# Check current state
terraform show
# Refresh state
terraform refresh
```

### Instance Issues

**User-data script failed**:
```bash
# SSH to instance
ssh -i my-ssh-key.pem ubuntu@<instance-ip>

# Check logs
sudo tail -f /var/log/user-data.log
sudo tail -f /var/log/cloud-init-output.log

# Check Apache status
sudo systemctl status apache2

# Test Apache config
sudo apache2ctl configtest
```

**Can't SSH to instance**:
- Check security group allows SSH from your IP
- Verify correct key pair name in tfvars
- Ensure instance has public IP (or use VPN)
- Check key permissions: `chmod 400 my-ssh-key.pem`

### Load Balancer Issues

**Health check failing**:
```bash
# Check if Apache is running on instances
curl http://<instance-private-ip>

# Check health check path in loadbalancer.tf (should be "/")
# Verify security group allows traffic from LB to instances
```

### Database Issues

**Can't connect to database**:
- Ensure you're connecting from a web server (not internet)
- Check security group allows 3306 from web SG
- Verify database endpoint in outputs
- Test with: `telnet <db-endpoint> 3306`

### Auto Scaling Issues

**Instances not scaling up**:
```bash
# Generate more load
ab -n 50000 -c 200 http://<load-balancer-ip>/

# Check CPU metrics in Cloud Eye console
# Verify alarm rules are active
# Check scaling policy cooldown period (5 minutes)
```

## 🔐 Security Hardening

Before final submission:

1. **Restrict SSH Access**:
   ```hcl
   # In terraform.tfvars
   admin_cidr = "<your-vpn-cidr>/24"  # Not 0.0.0.0/0
   ```

2. **Move Web Servers to Private Subnet**:
   ```hcl
   # In compute.tf and autoscaling.tf
   network {
     uuid = huaweicloud_vpc_subnet.private.id  # Not public
   }
   ```

3. **Remove Test Instance Public IPs**:
   ```hcl
   # In compute.tf
   count = 0  # Disable test instances
   ```

4. **Enable HTTPS** (optional):
   - Add SSL certificate to load balancer
   - Update listener to port 443
   - Redirect HTTP to HTTPS

## 📝 Project Structure

```
terraform/
├── main.tf              # Provider configuration
├── variables.tf         # Variable definitions
├── terraform.tfvars     # Your values (DO NOT COMMIT)
├── network.tf           # VPC, subnets, NAT
├── security.tf          # Security groups and rules
├── compute.tf           # Test ECS instances
├── loadbalancer.tf      # ELB configuration
├── autoscaling.tf       # Auto Scaling Group
├── database.tf          # RDS MySQL
├── vpn.tf               # VPN/Bastion server
├── outputs.tf           # Output values
├── user-data.sh         # Instance bootstrap script
├── .gitignore           # Git ignore rules
└── app/
    └── index.php        # Application file
```

## 🧹 Cleanup

To destroy all resources:

```bash
# WARNING: This will delete everything
terraform destroy

# Confirm by typing: yes
```

## 📚 Additional Resources

- [Huawei Cloud Terraform Provider Docs](https://registry.terraform.io/providers/huaweicloud/huaweicloud/latest/docs)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [OpenVPN Installation Guide](https://github.com/Nyr/openvpn-install)

## ⚠️ Important Notes

1. **Never commit secrets**: `terraform.tfvars` is in `.gitignore`
2. **Cost monitoring**: Monitor Huawei Cloud costs in console
3. **Resource limits**: Check quota limits for your account
4. **Testing**: Always test in dev environment first
5. **Backups**: RDS has automatic backups (7 days retention)

## 📞 Support

For issues:
1. Check troubleshooting section above
2. Review Terraform logs: `TF_LOG=DEBUG terraform apply`
3. Check Huawei Cloud service status
4. Review security group rules

---

**Created for Somali ASR Infrastructure Assessment**  
Version 1.0 | January 2026
