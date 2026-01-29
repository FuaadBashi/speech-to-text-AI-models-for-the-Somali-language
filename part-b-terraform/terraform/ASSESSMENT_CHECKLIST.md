# Assessment Submission Checklist

Use this checklist to ensure you have everything required for Part B submission.

## 📋 Pre-Deployment Checklist

- [ ] Terraform installed and working (`terraform version`)
- [ ] Huawei Cloud account created
- [ ] IAM Access Key and Secret Key obtained
- [ ] SSH key pair created in Huawei Cloud Console
- [ ] SSH key downloaded and permissions set (`chmod 400`)
- [ ] Your public IP address identified
- [ ] `terraform.tfvars` configured with all credentials

## 🏗️ Infrastructure Deployment Checklist

### Core Infrastructure
- [ ] VPC created (10.0.0.0/16)
- [ ] Public subnet created (10.0.1.0/24)
- [ ] Private subnet created (10.0.2.0/24)
- [ ] NAT Gateway deployed in public subnet
- [ ] All 4 security groups created with correct rules

### Load Balancer
- [ ] ELB created with public IP
- [ ] HTTP listener configured on port 80
- [ ] Backend pool created
- [ ] Health check configured (path: `/`, interval: 30s)
- [ ] Load balancer accessible from internet
- [ ] Application loads via LB URL

### Auto Scaling
- [ ] Auto Scaling configuration created
- [ ] Auto Scaling group created
- [ ] Min size: 2, Max size: 4, Desired: 2
- [ ] Instances attached to load balancer
- [ ] Instances running in private subnet
- [ ] Scale-up policy configured (CPU > 70%)
- [ ] Scale-down policy configured (CPU < 30%)
- [ ] Cloud Eye alarms created and active

### Database
- [ ] RDS MySQL instance created
- [ ] Database in private subnet
- [ ] Security group allows 3306 from web servers only
- [ ] Database accessible from web servers
- [ ] Database NOT accessible from internet

### VPN/Security
- [ ] VPN server created in public subnet
- [ ] OpenVPN installed and configured
- [ ] VPN client configuration downloaded
- [ ] VPN connection successful
- [ ] Private instances accessible via VPN
- [ ] SSH restricted to VPN CIDR (not 0.0.0.0/0)

## 🧪 Testing Checklist

### Load Balancing Tests
- [ ] Load balancer responds on port 80
- [ ] Application displays correctly
- [ ] Refreshing page shows different hostnames
- [ ] Both/all instances serving traffic
- [ ] Health checks passing

### Auto Scaling Tests
- [ ] Initial deployment has 2 instances
- [ ] Generated CPU load with Apache Bench
- [ ] Observed scale-up to 3 or 4 instances
- [ ] Instances added to load balancer automatically
- [ ] After load stops, instances scale down
- [ ] Cooldown period respected (5 minutes)

### Database Tests
- [ ] SSH to web server successful
- [ ] MySQL client installed
- [ ] Connected to database from web server
- [ ] Can list databases
- [ ] Cannot connect from internet

### Security Tests
- [ ] Web servers in private subnet (no public IPs)
- [ ] Only load balancer has public IP (plus VPN/NAT)
- [ ] SSH to web servers only works via VPN
- [ ] Security group rules verified
- [ ] Database only accessible from web servers

## 📸 Screenshot Requirements

All screenshots must be clear, readable, and properly named:

- [ ] `terraform-apply-success.png`
  - Terminal showing successful `terraform apply`
  - All resources created
  - No errors visible
  
- [ ] `load-balancer-working.png`
  - Browser showing application via load balancer IP
  - Application displays correctly
  - Instance hostname visible
  
- [ ] `different-hostnames.png`
  - Two browser tabs/windows side-by-side
  - Both showing the application
  - Different hostnames clearly visible
  - Proves load balancing
  
- [ ] `auto-scaling-instances.png`
  - Huawei Cloud Console
  - Auto Scaling → Scaling Groups → Instances tab
  - Shows 2+ instances (ideally 3-4)
  - Instance status: "InService"
  
- [ ] `database-created.png`
  - Huawei Cloud Console
  - RDS → Instances
  - Database details visible
  - Status: "Available"
  
- [ ] `vpn-connected.png`
  - VPN client screenshot
  - Connection status: Connected
  - Routes to 10.0.0.0/16 visible

## 📄 Documentation Requirements

- [ ] README.md completed
- [ ] DEPLOYMENT_GUIDE.md reviewed
- [ ] Architecture diagram created (optional but recommended)
- [ ] All Terraform files properly formatted (`terraform fmt`)
- [ ] All Terraform files validated (`terraform validate`)
- [ ] Comments added where necessary
- [ ] No sensitive data in files (check .gitignore)

## 🔐 Security Requirements Met

- [ ] No hardcoded credentials in Terraform files
- [ ] `terraform.tfvars` in .gitignore
- [ ] SSH keys not committed to repository
- [ ] Web servers in private subnet
- [ ] Database in private subnet
- [ ] Only essential ports open in security groups
- [ ] Admin access via VPN only
- [ ] Strong database password used
- [ ] Security group rules follow least privilege

## 📊 Terraform Best Practices

- [ ] All resources properly tagged
- [ ] Variables used instead of hardcoded values
- [ ] Outputs defined for important values
- [ ] Resources organized in logical files
- [ ] Naming conventions consistent
- [ ] State file not committed (.gitignore)
- [ ] Provider version pinned
- [ ] No deprecated resource types used

## 🎯 Assessment Criteria Met

### Infrastructure (40%)
- [ ] VPC with public and private subnets
- [ ] NAT Gateway for outbound internet
- [ ] Proper network isolation
- [ ] Security groups configured correctly

### Load Balancing (20%)
- [ ] ELB deployed with public IP
- [ ] Health checks configured
- [ ] Traffic distributed across instances
- [ ] Demonstrated with different hostnames

### Auto Scaling (20%)
- [ ] Scaling group configured (min 2, max 4)
- [ ] Scale-up policy triggered
- [ ] Scale-down policy triggered
- [ ] Instances automatically join load balancer

### Database (10%)
- [ ] RDS MySQL deployed
- [ ] Private subnet placement
- [ ] Accessible from web servers
- [ ] Not accessible from internet

### Security (10%)
- [ ] VPN configured for admin access
- [ ] Private subnet for web/db
- [ ] Security groups properly restrictive
- [ ] No public IPs on web servers

## 📦 Submission Package

Your final submission should include:

```
somali-asr-infra/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars.example  (NOT terraform.tfvars)
│   ├── network.tf
│   ├── security.tf
│   ├── compute.tf
│   ├── loadbalancer.tf
│   ├── autoscaling.tf
│   ├── database.tf
│   ├── vpn.tf
│   ├── outputs.tf
│   ├── user-data.sh
│   ├── .gitignore
│   ├── README.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── QUICK_START.md
│   └── app/
│       └── index.php
├── screenshots/
│   ├── terraform-apply-success.png
│   ├── load-balancer-working.png
│   ├── different-hostnames.png
│   ├── auto-scaling-instances.png
│   ├── database-created.png
│   └── vpn-connected.png
└── documentation/
    ├── architecture-diagram.png (optional)
    └── implementation-report.pdf (if required)
```

## ✅ Final Verification

Before submission:

- [ ] Run `terraform validate`
- [ ] Run `terraform fmt`
- [ ] Run `terraform plan` (should show no changes)
- [ ] All screenshots collected
- [ ] All documentation complete
- [ ] No sensitive data exposed
- [ ] Tested `terraform destroy`
- [ ] Tested fresh `terraform apply`

## 🚀 Optional Enhancements (Bonus Points)

- [ ] HTTPS configured on load balancer
- [ ] Custom domain name
- [ ] CloudWatch/Cloud Eye monitoring configured
- [ ] Automated backups for database
- [ ] Multi-AZ deployment
- [ ] Blue-green deployment strategy
- [ ] Infrastructure diagram included

## 📝 Common Mistakes to Avoid

- ❌ Committing terraform.tfvars with credentials
- ❌ Using 0.0.0.0/0 for SSH in production
- ❌ Web servers in public subnet with public IPs
- ❌ Database accessible from internet
- ❌ Not testing auto-scaling
- ❌ Screenshots not showing required information
- ❌ Missing evidence of load balancing
- ❌ Not documenting VPN setup

## 🎓 Grading Rubric Reference

| Component | Points | Your Status |
|-----------|--------|-------------|
| VPC & Networking | 20 | ☐ Complete |
| Load Balancer | 15 | ☐ Complete |
| Auto Scaling | 20 | ☐ Complete |
| Database | 10 | ☐ Complete |
| Security (VPN) | 15 | ☐ Complete |
| Documentation | 10 | ☐ Complete |
| Screenshots | 10 | ☐ Complete |
| **Total** | **100** | |

## 📞 Getting Help

If stuck:
1. Check DEPLOYMENT_GUIDE.md troubleshooting section
2. Review Terraform error messages carefully
3. Check Huawei Cloud Console for resource status
4. Verify all prerequisites completed
5. Review security group rules

---

## ✨ Ready to Submit?

If you checked all items above, you're ready! 🎉

**Final command**:
```bash
# Create submission archive
tar -czf somali-asr-infra-submission.tar.gz \
  terraform/ screenshots/ documentation/

# Verify archive
tar -tzf somali-asr-infra-submission.tar.gz | head -20
```

**Good luck with your assessment!** 🚀
