# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = hcs_vpc.main.id
}

output "public_subnet_id" {
  description = "Public Subnet ID"
  value       = hcs_vpc_subnet.public.id
}

output "private_subnet_id" {
  description = "Private Subnet ID"
  value       = hcs_vpc_subnet.private.id
}

# Load Balancer Outputs
output "load_balancer_ip" {
  description = "Load Balancer Public IP (use this to access the application)"
  value       = hcs_vpc_eip.lb.address
}

output "load_balancer_url" {
  description = "Load Balancer URL"
  value       = "http://${hcs_vpc_eip.lb.address}"
}

# NAT Gateway Output
output "nat_gateway_ip" {
  description = "NAT Gateway Public IP"
  value       = hcs_vpc_eip.nat.address
}

# VPN Outputs
output "vpn_server_ip" {
  description = "VPN Server Public IP"
  value       = hcs_vpc_eip.vpn.address
}

output "vpn_ssh_command" {
  description = "Command to SSH into VPN server"
  value       = "ssh -i ${var.key_pair_name}.pem ubuntu@${hcs_vpc_eip.vpn.address}"
}

# Test Instance Outputs (when enabled)
output "test_instance_ips" {
  description = "Test instance public IPs"
  value       = hcs_vpc_eip.test_instance[*].address
}

output "test_instance_ssh_commands" {
  description = "Commands to SSH into test instances"
  value = [
    for ip in hcs_vpc_eip.test_instance[*].address :
    "ssh -i ${var.key_pair_name}.pem ubuntu@${ip}"
  ]
}

# Database Outputs
output "database_endpoint" {
  description = "RDS MySQL endpoint"
  value       = hcs_rds_instance.main.private_ips[0]
}

output "database_port" {
  description = "RDS MySQL port"
  value       = 3306
}

output "database_name" {
  description = "Database name"
  value       = hcs_rds_mysql_database.app_db.name
}

# Auto Scaling Outputs
output "autoscaling_group_id" {
  description = "Auto Scaling Group ID"
  value       = hcs_as_group.main.id
}

output "autoscaling_group_name" {
  description = "Auto Scaling Group Name"
  value       = hcs_as_group.main.scaling_group_name
}

# Security Group Outputs
output "lb_security_group_id" {
  description = "Load Balancer Security Group ID"
  value       = hcs_networking_secgroup.lb.id
}

output "web_security_group_id" {
  description = "Web Server Security Group ID"
  value       = hcs_networking_secgroup.web.id
}

output "db_security_group_id" {
  description = "Database Security Group ID"
  value       = hcs_networking_secgroup.db.id
}

# Quick Access Instructions
output "quick_start_instructions" {
  sensitive   = true
  description = "Quick start instructions"
  value       = <<-EOT
  
  ========================================
  DEPLOYMENT SUCCESSFUL!
  ========================================
  
  1. Access the application:
     ${hcs_vpc_eip.lb.address}
  
  2. Connect to VPN server:
     ssh -i ${var.key_pair_name}.pem ubuntu@${hcs_vpc_eip.vpn.address}
  
  3. Test instances (if enabled):
     ${join("\n     ", [for ip in hcs_vpc_eip.test_instance[*].address : "ssh -i ${var.key_pair_name}.pem ubuntu@${ip}"])}
  
  4. Database connection:
     Host: ${hcs_rds_instance.main.private_ips[0]}
     Port: 3306
     Database: ${hcs_rds_mysql_database.app_db.name}
     Username: ${var.db_username}
  
  5. Auto-scaling is configured:
     Min: ${var.asg_min_size}
     Max: ${var.asg_max_size}
     Current: ${var.asg_desired_capacity}
  
  ========================================
  
  EOT
}
