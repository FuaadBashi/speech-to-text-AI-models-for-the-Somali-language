output "vpc_id" {
  value = hcs_vpc.main.id
}

output "public_subnet_id" {
  value = hcs_vpc_subnet.public.id
}

output "private_subnet_id" {
  value = hcs_vpc_subnet.private.id
}

output "bastion_private_ip" {
  value = hcs_ecs_compute_instance.bastion.access_ip_v4
}

output "web_private_ip" {
  value = hcs_ecs_compute_instance.web.access_ip_v4
}
