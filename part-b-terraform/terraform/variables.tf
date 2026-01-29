variable "access_key" {
  description = "Huawei Cloud Access Key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Huawei Cloud Secret Key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Huawei Cloud Region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "somali-asr-infra"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Private subnet CIDR block"
  type        = string
  default     = "10.0.2.0/24"
}

variable "availability_zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "ap-southeast-1a"
}

variable "key_pair_name" {
  description = "SSH key pair name (must exist in Huawei Cloud)"
  type        = string
}

variable "admin_cidr" {
  description = "Admin IP CIDR for SSH access (your public IP or VPN CIDR)"
  type        = string
  default     = "0.0.0.0/0"  # CHANGE THIS in production to your specific IP/VPN
}

variable "instance_flavor" {
  description = "ECS instance flavor"
  type        = string
  default     = "s6.small.1"
}

variable "instance_image" {
  description = "ECS instance image ID (Ubuntu 22.04)"
  type        = string
  default     = "ubuntu_22_04_x86_64"  # This may need adjustment based on region
}

variable "db_password" {
  description = "RDS MySQL root password"
  type        = string
  sensitive   = true
}

variable "db_username" {
  description = "RDS MySQL root username"
  type        = string
  default     = "admin"
}

variable "asg_min_size" {
  description = "Auto Scaling Group minimum size"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Auto Scaling Group maximum size"
  type        = number
  default     = 4
}

variable "asg_desired_capacity" {
  description = "Auto Scaling Group desired capacity"
  type        = number
  default     = 2
}
