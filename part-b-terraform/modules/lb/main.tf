variable "vpc_id" { type = string }
variable "subnet_id" { type = string }
variable "lb_sg_id" { type = string }

# TODO: Create ELB (public) + listener (80) + backend pool + health check
output "lb_public_ip" { value = null }
output "backend_pool_id" { value = null }
