variable "vpc_id" { type = string }

# TODO: Create security groups with least privilege:
# - lb_sg: allow 80/443 from 0.0.0.0/0
# - app_sg: allow 80 from lb_sg only
# - db_sg: allow DB port from app_sg only

output "lb_sg_id" { value = null }
output "app_sg_id" { value = null }
output "db_sg_id" { value = null }
