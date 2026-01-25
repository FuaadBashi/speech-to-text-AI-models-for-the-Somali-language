variable "subnet_id" { type = string }
variable "db_sg_id" { type = string }
variable "engine" { type = string }
variable "version" { type = string }
variable "flavor" { type = string }
variable "password" { type = string, sensitive = true }

# TODO: Create managed DB instance (RDS) in private subnet with SG
output "db_endpoint" { value = null }
