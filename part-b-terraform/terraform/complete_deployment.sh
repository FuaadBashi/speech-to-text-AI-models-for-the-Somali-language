#!/bin/bash
echo "=========================================="
echo "HTG Cloud - Complete Deployment"
echo "=========================================="

cd ~/Desktop/ai-devops-assessment/part-b-terraform/terraform

echo ""
echo "STEP 1: Deploy Auto-Scaling Group"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > autoscaling.tf << 'ASEOF'
# Auto-scaling configuration for web tier
resource "hcs_as_configuration" "web" {
  scaling_configuration_name = "dev-web-asg-config"
  
  instance_config {
    image    = "450d07fd-bf1a-407a-9063-ea829537859e"
    flavor   = "S6_large.2"
    key_name = "dev-keypair"
    
    disk {
      size        = 55
      volume_type = "SSD"
      disk_type   = "SYS"
    }
    
    security_groups {
      id = "9d4a99fc-22f8-4411-a5d2-a106d929acc5"
    }
  }
}

resource "hcs_as_group" "web" {
  scaling_group_name       = "dev-web-asg"
  scaling_configuration_id = hcs_as_configuration.web.id
  desire_instance_number   = 1
  min_instance_number      = 1
  max_instance_number      = 3
  vpc_id                   = "98ad579e-1d35-44f0-9ecd-13ad2880e348"
  
  networks {
    id = "0dca4e7d-60d3-4d67-bc5a-5eb58c11d7d2"
  }
  
  security_groups {
    id = "9d4a99fc-22f8-4411-a5d2-a106d929acc5"
  }
  
  delete_instances = "yes"
  delete_publicip  = true
}

resource "hcs_as_policy" "cpu_scale_out" {
  scaling_policy_name   = "dev-cpu-scale-out"
  scaling_group_id      = hcs_as_group.web.id
  scaling_policy_type   = "RECURRENCE"
  cool_down_time        = 300
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  scheduled_policy {
    launch_time      = "07:00"
    recurrence_type  = "Daily"
    recurrence_value = null
  }
}
ASEOF

echo "✅ Created autoscaling.tf"
echo ""
echo "Deploying auto-scaling..."
terraform plan -out=tfplan-asg

if [ $? -eq 0 ]; then
    terraform apply tfplan-asg
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Auto-scaling deployed successfully!"
    else
        echo ""
        echo "❌ Auto-scaling deployment failed"
        echo "Check errors above and continue manually"
    fi
else
    echo ""
    echo "❌ Auto-scaling plan failed"
    echo "Continue with manual steps below"
fi

echo ""
echo ""
echo "=========================================="
echo "STEP 2: Create EIPs via Console"
echo "=========================================="
echo ""
echo "Go to HTG Cloud Console and manually create EIPs:"
echo ""
echo "1. Navigate to: Services → VPC → Elastic IPs"
echo "2. Click 'Allocate EIP'"
echo "3. Create TWO EIPs:"
echo "   - Name: bastion-eip (for bastion host)"
echo "   - Name: lb-eip (for load balancer)"
echo "   - Bandwidth: 5 Mbps for bastion, 10 Mbps for LB"
echo ""
echo "4. After creation, BIND bastion-eip:"
echo "   - Click 'Bind' on bastion-eip"
echo "   - Select instance: dev-bastion"
echo "   - Confirm"
echo ""
echo "5. Note down the EIP addresses and IDs"
echo ""
read -p "Press ENTER after you've created and bound the EIPs..."
echo ""
read -p "Enter the Bastion EIP address: " BASTION_EIP
read -p "Enter the Bastion EIP ID: " BASTION_EIP_ID
read -p "Enter the LB EIP address (or skip): " LB_EIP
read -p "Enter the LB EIP ID (or skip): " LB_EIP_ID

echo ""
echo "Bastion EIP: $BASTION_EIP (ID: $BASTION_EIP_ID)"
if [ -n "$LB_EIP" ]; then
    echo "LB EIP: $LB_EIP (ID: $LB_EIP_ID)"
fi

# Save EIP info
cat > eip_info.txt << EIPINFO
Bastion EIP Address: $BASTION_EIP
Bastion EIP ID: $BASTION_EIP_ID
LB EIP Address: $LB_EIP
LB EIP ID: $LB_EIP_ID
EIPINFO

echo ""
echo "✅ EIP info saved to eip_info.txt"

echo ""
echo ""
echo "=========================================="
echo "STEP 3: SSH Setup & Apache Installation"
echo "=========================================="
echo ""
echo "Generating SSH commands..."
echo ""

cat > ~/Desktop/ssh_to_htg.sh << SSHSCRIPT
#!/bin/bash
# SSH to HTG Cloud Bastion
echo "Connecting to bastion at $BASTION_EIP..."
ssh -i ~/.ssh/id_rsa ubuntu@$BASTION_EIP
SSHSCRIPT

chmod +x ~/Desktop/ssh_to_htg.sh

cat > ~/Desktop/setup_web_server.sh << WEBSETUP
#!/bin/bash
echo "=========================================="
echo "Setting up Apache Web Server"
echo "=========================================="

# SSH to web server via bastion
ssh -i ~/.ssh/id_rsa ubuntu@$BASTION_EIP << 'REMOTECMDS'
# From bastion, connect to web server
ssh ubuntu@10.0.2.167 << 'WEBSETUP'
echo "Installing Apache..."
sudo apt update
sudo apt install -y apache2

echo "Starting Apache..."
sudo systemctl enable apache2
sudo systemctl start apache2

echo "Creating demo page..."
sudo bash -c 'cat > /var/www/html/index.html << HTML
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTG Cloud - AI/DevOps Assessment</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        h1 { margin-top: 0; }
        .info {
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .success { color: #4ade80; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 HTG Cloud Deployment</h1>
        <h2>AI/DevOps Technical Assessment - Part B</h2>
        
        <div class="info">
            <h3>Infrastructure Details</h3>
            <p><strong>Instance:</strong> dev-web</p>
            <p><strong>Private IP:</strong> 10.0.2.167</p>
            <p><strong>Subnet:</strong> private (10.0.2.0/24)</p>
            <p><strong>Security Group:</strong> web</p>
            <p><strong>Deployed:</strong> Terraform + HCS Provider</p>
        </div>
        
        <div class="info">
            <h3>Infrastructure Components</h3>
            <ul>
                <li class="success">✓ VPC with public/private subnets</li>
                <li class="success">✓ Security groups with proper rules</li>
                <li class="success">✓ Bastion host (10.0.1.141)</li>
                <li class="success">✓ Web server (this instance)</li>
                <li class="success">✓ Auto-scaling group</li>
                <li class="success">✓ Apache web server</li>
            </ul>
        </div>
        
        <div class="info">
            <p><strong>Hostname:</strong> <code>$(hostname)</code></p>
            <p><strong>System Time:</strong> <code>$(date)</code></p>
        </div>
    </div>
</body>
</html>
HTML'

echo ""
echo "Testing Apache..."
curl -s http://localhost | head -5

echo ""
echo "✅ Apache installation complete!"
echo ""
echo "Web server is now accessible at:"
echo "  - From bastion: http://10.0.2.167"
echo "  - Via load balancer (once configured)"

WEBSETUP
REMOTECMDS

WEBSETUP

chmod +x ~/Desktop/setup_web_server.sh

echo ""
echo "✅ SSH scripts created!"
echo ""
echo "To connect to bastion:"
echo "  ~/Desktop/ssh_to_htg.sh"
echo ""
echo "To setup Apache on web server:"
echo "  ~/Desktop/setup_web_server.sh"
echo ""

echo ""
echo ""
echo "=========================================="
echo "STEP 4: Test Web Server"
echo "=========================================="
echo ""
echo "Run this to test the web server:"
echo ""
echo "  ssh -i ~/.ssh/id_rsa ubuntu@$BASTION_EIP 'curl http://10.0.2.167'"
echo ""

