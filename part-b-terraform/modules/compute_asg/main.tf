variable "vpc_id" { type = string }
variable "subnet_id" { type = string }
variable "app_sg_id" { type = string }
variable "instance_flavor" { type = string }
variable "image_id" { type = string }
variable "keypair_name" { type = string }
variable "min_size" { type = number }
variable "max_size" { type = number }
variable "desired_capacity" { type = number }
variable "backend_pool_id" { type = string }
variable "user_data_path" { type = string }

# TODO:
# - launch template/config (ECS)
# - auto scaling group with desired/min/max
# - attach instances to lb backend pool
