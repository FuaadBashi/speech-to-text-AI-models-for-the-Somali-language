output "vpc_id" {
  value       = hcs_vpc.main.id
  description = "VPC ID"
}

output "public_subnet_id" {
  value       = hcs_vpc_subnet.public.id
  description = "Public Subnet ID"
}

output "private_subnet_id" {
  value       = hcs_vpc_subnet.private.id
  description = "Private Subnet ID"
}

output "bastion_public_ip" {
  value       = hcs_vpc_eip.bastion.address
  description = "Bastion Host Public IP"
}

output "nat_gateway_id" {
  value       = hcs_nat_gateway.main.id
  description = "NAT Gateway ID"
}

output "nat_public_ip" {
  value       = hcs_vpc_eip.nat.address
  description = "NAT Gateway Public IP"
}

output "rds_instance_id" {
  value       = hcs_rds_instance.main.id
  description = "RDS Instance ID"
}

output "rds_endpoint" {
  value       = hcs_rds_instance.main.private_ips
  description = "RDS Private Endpoint"
}

output "load_balancer_id" {
  value       = hcs_elb_loadbalancer.main.id
  description = "Load Balancer ID"
}

output "load_balancer_eip" {
  value       = hcs_vpc_eip.lb.address
  description = "Load Balancer EIP (needs manual association in console)"
}

output "autoscaling_group_id" {
  value       = hcs_as_group.main.id
  description = "Auto Scaling Group ID"
}
