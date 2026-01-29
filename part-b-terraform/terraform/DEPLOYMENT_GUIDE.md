# Deployment Guide - Step by Step

This guide walks you through deploying the infrastructure from zero to complete.

## 🎯 Goal

By the end of this guide, you will have:
- ✅ A working load-balanced web application
- ✅ Auto-scaling between 2-4 instances
- ✅ Private database accessible from web servers
- ✅ VPN for secure admin access
- ✅ Evidence screenshots for assessment

## ⏱️ Time Required

- First-time setup: 30-45 minutes
- Subsequent deployments: 10-15 minutes

---

## Phase 0: Prerequisites (15 minutes)

### 0.1 Install Terraform

**MacOS**:
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform version  # Should show 1.0+
```

**Linux (Ubuntu/Debian)**:
```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
terraform version
```

**Windows**:
- Download from: https://www.terraform.io/downloads
- Extract to `C:\terraform`
- Add to PATH
- Open new PowerShell: `terraform version`

### 0.2 Get Huawei Cloud Credentials

1. **Log into Huawei Cloud Console**
   - Go to: https://console.huaweicloud.com

2. **Create Access Key**
   - Click your username (top right) → My Credentials
   - Access Keys → Create Access Key
   - **SAVE BOTH**: Access Key ID and Secret Access Key
   - You cannot retrieve the secret key later!

3. **Create SSH Key Pair**
   - Console → Service List → Elastic Cloud Server
   - Key Pairs (left menu)
   - Create Key Pair
   - Name it: `my-ssh-key` (or your preferred name)
   - Download the `.pem` file
   - Save to a secure location

4. **Set Key Permissions** (Mac/Linux):
   ```bash
   chmod 400 ~/Downloads/my-ssh-key.pem
   mv ~/Downloads/my-ssh-key.pem ~/.ssh/
   ```

5. **Find Your Public IP**
   - Visit: https://whatismyip.com
   - Note your IP address (e.g., `203.0.113.45`)

---

## Phase 1: Network Foundation (5 minutes)

### 1.1 Configure Variables

```bash
cd terraform/

# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**Fill in these values**:
```hcl
access_key    = "YOUR_ACCESS_KEY_HERE"
secret_key    = "YOUR_SECRET_KEY_HERE"
region        = "ap-southeast-1"
key_pair_name = "my-ssh-key"
admin_cidr    = "203.0.113.45/32"  # YOUR public IP
db_password   = "MySecurePass123!"
```

### 1.2 Deploy Network

```bash
# Initialize Terraform
terraform init

# Format files
terraform fmt

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Deploy
terraform apply
```

When prompted, type: `yes`

### 1.3 Verify Network

**In Huawei Cloud Console**:
- Virtual Private Cloud → Your VPCs
- Should see: `somali-asr-infra-dev-vpc`
- Click on it → Subnets
- Should see:
  - `somali-asr-infra-dev-public-subnet` (10.0.1.0/24)
  - `somali-asr-infra-dev-private-subnet` (10.0.2.0/24)

**✅ Checkpoint**: VPC and subnets exist

---

## Phase 2: Security Groups (2 minutes)

Security groups are already in your terraform files, so they deployed in Phase 1.

### 2.1 Verify Security Groups

**In Console**:
- Virtual Private Cloud → Access Control → Security Groups
- Should see 4 security groups:
  - `somali-asr-infra-dev-lb-sg`
  - `somali-asr-infra-dev-web-sg`
  - `somali-asr-infra-dev-db-sg`
  - `somali-asr-infra-dev-vpn-sg`

**✅ Checkpoint**: All security groups created with correct rules

---

## Phase 3: Test Instance (5 minutes)

### 3.1 Deploy Test Instance

The test instance is already configured. Just verify:

```bash
# Check outputs
terraform output test_instance_ips
terraform output test_instance_ssh_commands
```

### 3.2 Test SSH Access

```bash
# Use the command from output, or:
ssh -i ~/.ssh/my-ssh-key.pem ubuntu@<TEST_INSTANCE_IP>
```

**First time**: Type `yes` when asked about fingerprint

### 3.3 Verify Apache Installation

```bash
# Check user-data log
sudo tail -f /var/log/user-data.log

# Wait until you see: "User-data script completed successfully"
# Press Ctrl+C to exit

# Check Apache status
sudo systemctl status apache2

# Should show: "active (running)"
```

### 3.4 Test in Browser

```bash
# Get the IP
terraform output test_instance_ips

# Open in browser:
http://<TEST_INSTANCE_IP>
```

**You should see**: Colorful web page with "Somali ASR" title and instance details

**📸 Screenshot tip**: This is good for testing, but save screenshots for load balancer

**✅ Checkpoint**: Test instance serves web page

---

## Phase 4: Load Balancer (5 minutes)

### 4.1 Enable Load Balancer Members

Edit `terraform/loadbalancer.tf`:

```bash
nano loadbalancer.tf
```

Find the section at the bottom (around line 80):
```hcl
# Manual backend members (for testing before auto-scaling)
# Uncomment these when you have test instances
/*
resource "huaweicloud_elb_member" "test_web" {
  ...
}
*/
```

**Remove the `/*` and `*/`** to uncomment the resource.

### 4.2 Apply Changes

```bash
terraform apply
```

### 4.3 Get Load Balancer IP

```bash
terraform output load_balancer_url
```

### 4.4 Test Load Balancer

```bash
# Test from command line
curl http://<LOAD_BALANCER_IP>

# Open in browser
# Open: http://<LOAD_BALANCER_IP>
```

### 4.5 Verify Load Balancing

**In browser**:
1. Open the load balancer URL
2. Note the hostname shown
3. Refresh the page (F5)
4. Hostname should change (if you have 2+ instances)

**📸 SCREENSHOT #1**: `load-balancer-working.png`
- Browser showing the application via LB IP

**📸 SCREENSHOT #2**: `different-hostnames.png`
- Two browser tabs side-by-side showing different hostnames

**✅ Checkpoint**: Load balancer distributes traffic to instances

---

## Phase 5: Auto Scaling (5 minutes)

### 5.1 Disable Test Instances

Edit `terraform/compute.tf`:

```bash
nano compute.tf
```

Change `count = 1` to `count = 0` in these resources:
- `huaweicloud_vpc_eip.test_instance`
- `huaweicloud_compute_instance.test_web`
- `huaweicloud_compute_eip_associate.test_web`

### 5.2 Comment Out Manual LB Members

Edit `terraform/loadbalancer.tf`:

```bash
nano loadbalancer.tf
```

Put `/*` before and `*/` after the `huaweicloud_elb_member.test_web` resource to comment it out again.

### 5.3 Deploy Auto Scaling

```bash
terraform apply
```

**Important**: This will:
- Destroy test instances
- Create auto-scaling group
- Launch 2 new instances automatically
- Attach them to load balancer

### 5.4 Verify Auto Scaling

**In Console**:
- Auto Scaling → Scaling Groups
- Click: `somali-asr-infra-dev-as-group`
- Click "Instances" tab
- Should show 2 instances: "InService"

**Test in browser**:
- Refresh load balancer URL several times
- Should see different hostnames

**📸 SCREENSHOT #3**: `auto-scaling-instances.png`
- Console showing instances in auto-scaling group

**✅ Checkpoint**: Auto-scaling group running with 2 instances

### 5.5 Test Scaling Up

**Generate load**:

```bash
# Install Apache Bench (if not already installed)
# Mac: brew install httpd
# Linux: sudo apt install apache2-utils

# Generate load
ab -n 10000 -c 100 http://<LOAD_BALANCER_IP>/
```

**Watch scaling**:
- Console → Auto Scaling → Scaling Groups
- Click your group → "Instances" tab
- Refresh every 30 seconds
- After 5 minutes of high CPU (>70%), should scale to 3 instances

**📸 SCREENSHOT #4**: `auto-scaling-instances.png` (updated)
- Console showing 3 or 4 instances after scaling

**✅ Checkpoint**: Auto-scaling responds to load

---

## Phase 6: Database (3 minutes)

Database is already in your terraform files!

### 6.1 Verify Database

```bash
# Get database endpoint
terraform output database_endpoint
```

**In Console**:
- Relational Database Service → Instances
- Should see: `somali-asr-infra-dev-mysql`
- Status: "Available"

**📸 SCREENSHOT #5**: `database-created.png`
- Console showing RDS instance details

### 6.2 Test Database Connection

```bash
# SSH to VPN server (we'll set this up next)
# Then SSH to a web server from VPN
# Then test DB connection:

sudo apt install mysql-client -y
mysql -h <DB_ENDPOINT> -u admin -p
# Enter password from terraform.tfvars

# If successful:
mysql> SHOW DATABASES;
mysql> EXIT;
```

**✅ Checkpoint**: Database accessible from web servers

---

## Phase 7: VPN Access (10 minutes)

### 7.1 Get VPN Server IP

```bash
terraform output vpn_server_ip
```

### 7.2 SSH to VPN Server

```bash
ssh -i ~/.ssh/my-ssh-key.pem ubuntu@<VPN_SERVER_IP>
```

### 7.3 Install OpenVPN

```bash
# Download installation script
wget https://git.io/vpn -O openvpn-install.sh

# Run installer
sudo bash openvpn-install.sh
```

**Follow prompts**:
1. IP address: (accept default - should be your VPN server IP)
2. Protocol: (accept default - UDP)
3. Port: (accept default - 1194)
4. DNS: (accept default or choose 1 for current system)
5. Client name: `my-client`
6. Press Enter to confirm

**Installation takes 2-3 minutes**

### 7.4 Download Client Config

```bash
# On VPN server:
cat ~/my-client.ovpn

# Copy the entire output
```

**On your local machine**:

```bash
# Create file
nano ~/my-client.ovpn

# Paste the content
# Save and exit (Ctrl+O, Enter, Ctrl+X)
```

### 7.5 Connect to VPN

**Mac/Linux**:
```bash
sudo openvpn ~/my-client.ovpn
```

**Windows**:
- Install OpenVPN GUI from: https://openvpn.net/community-downloads/
- Copy `my-client.ovpn` to `C:\Program Files\OpenVPN\config\`
- Right-click OpenVPN GUI → Run as Administrator
- Right-click tray icon → Connect

### 7.6 Verify VPN Connection

**New terminal** (keep VPN running in first terminal):

```bash
# Check routes
# Mac/Linux:
netstat -rn | grep 10.0

# Should show routes to 10.0.0.0/16

# Test ping to private instance
ping <PRIVATE_INSTANCE_IP>
```

**📸 SCREENSHOT #6**: `vpn-connected.png`
- VPN client showing connected status
- Include routing table

**✅ Checkpoint**: VPN provides access to private network

---

## Phase 8: Final Hardening (5 minutes)

### 8.1 Restrict SSH Access

Edit `terraform.tfvars`:

```bash
nano terraform.tfvars
```

Change:
```hcl
admin_cidr = "10.8.0.0/24"  # VPN client network
```

### 8.2 Apply Changes

```bash
terraform apply
```

**✅ Checkpoint**: SSH only accessible via VPN

---

## Phase 9: Final Testing & Screenshots

### 9.1 Complete Test Checklist

- [ ] Load balancer accessible from internet
- [ ] Different hostnames on refresh
- [ ] Auto-scaling group has 2+ instances
- [ ] Can generate load and trigger scale-up
- [ ] Database exists and is accessible from web servers
- [ ] VPN connects successfully
- [ ] Can access private instances via VPN

### 9.2 Screenshot Checklist

- [ ] `terraform-apply-success.png` - Terminal output
- [ ] `load-balancer-working.png` - Browser showing app
- [ ] `different-hostnames.png` - Two tabs with different hosts
- [ ] `auto-scaling-instances.png` - Console with instances
- [ ] `database-created.png` - RDS console
- [ ] `vpn-connected.png` - VPN client connected

---

## 🎉 Congratulations!

You have successfully deployed a production-ready, auto-scaling web infrastructure on Huawei Cloud!

## Next Steps

1. **Document your work**: Write up your implementation process
2. **Prepare presentation**: Create slides explaining your architecture
3. **Practice demo**: Walk through your deployment
4. **Review security**: Ensure all best practices followed

## Cleanup (When Done)

```bash
# WARNING: This destroys everything!
terraform destroy

# Type: yes
```

---

## 🆘 Common Issues

### "Error: Provider not found"
```bash
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### "Error: Unauthorized"
- Check access_key and secret_key in tfvars
- Verify IAM user has correct permissions

### "Error: Key pair not found"
- Verify key pair name exactly matches in Huawei Cloud
- Check region matches

### "Health check failed"
- Wait 5 minutes for instances to fully boot
- SSH to instance and check Apache: `sudo systemctl status apache2`
- Check security group allows traffic from LB

### "Can't connect to database"
- Ensure connecting from web server (not internet)
- Check security group allows 3306 from web SG
- Verify password in tfvars

### "Auto scaling not working"
- Check Cloud Eye alarms are active
- Generate sustained load (not just brief spike)
- Wait 5 minutes for cooldown period
- Verify scaling policies are enabled

---

**Good luck with your deployment! 🚀**
