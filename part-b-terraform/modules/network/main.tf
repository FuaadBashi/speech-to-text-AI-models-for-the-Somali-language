variable "vpc_cidr" { type = string }
variable "public_subnet_cidr" { type = string }
variable "private_subnet_cidr" { type = string }

# TODO: Create VPC + 2 subnets + routing + (optional) NAT/IGW/EIP depending on provider capabilities
# Output vpc_id, public_subnet_id, private_subnet_id

output "vpc_id" { value = null }
output "public_subnet_id" { value = null }
output "private_subnet_id" { value = null }
