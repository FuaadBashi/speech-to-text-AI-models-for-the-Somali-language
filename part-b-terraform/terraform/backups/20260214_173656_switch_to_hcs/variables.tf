# ============================================
# COMPLETE VARIABLES FILE FOR TERRAFORM
# ============================================
# HTG Cloud Infrastructure Variables
# Project: Somali ASR AI DevOps Assessment

# ============================================
# Huawei Cloud Provider Variables
# ============================================
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
  description = "Huawei Cloud region"
  type        = string
  default     = "Mogadishu-region-hq3"
}

variable "availability_zone" {
  description = "Availability zone within the region"
  type        = string
  default     = "Mogadishu-region-hq3a"
}

variable "project_name" {
  description = "Project name for resources"
  type        = string
  default     = "somali-asr"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# ============================================
# Network Variables
# ============================================
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for the private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

# ============================================
# Security Variables
# ============================================
variable "admin_cidr" {
  description = "CIDR block for admin SSH access (your public IP)"
  type        = string
  default     = "0.0.0.0/0" # Override in terraform.tfvars with your specific IP
}

# ============================================
# Compute Instance Variables
# ============================================
variable "instance_flavor" {
  description = "Flavor ID for compute instances"
  type        = string
  default     = "s6.large.2"
}

variable "image_id" {
  description = "Image ID for compute instances (get from HTG Cloud console)"
  type        = string
  # Must be provided in terraform.tfvars
}

variable "key_pair_name" {
  description = "Name of the SSH key pair"
  type        = string
  default     = "htg-fuaad-key"
}

# ============================================
# Database Variables
# ============================================
variable "db_username" {
  description = "Master username for RDS database"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for RDS database"
  type        = string
  sensitive   = true
  # Must be provided in terraform.tfvars
}

variable "db_name" {
  description = "Name of the database to create"
  type        = string
  default     = "somali_asr_db"
}

variable "db_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "8.0"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "rds.mysql.s1.large"
}

variable "db_storage_size" {
  description = "Database storage size in GB"
  type        = number
  default     = 40
}

# ============================================
# Auto Scaling Variables
# ============================================
variable "asg_min_size" {
  description = "Minimum number of instances in the Auto Scaling Group"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Maximum number of instances in the Auto Scaling Group"
  type        = number
  default     = 10
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in the Auto Scaling Group"
  type        = number
  default     = 2
}

variable "scale_up_threshold" {
  description = "CPU threshold percentage to trigger scale up"
  type        = number
  default     = 70
}

variable "scale_down_threshold" {
  description = "CPU threshold percentage to trigger scale down"
  type        = number
  default     = 30
}

# ============================================
# VPN Variables
# ============================================
variable "vpn_instance_flavor" {
  description = "Flavor for VPN instance"
  type        = string
  default     = "s6.small.1"
}

variable "vpn_user" {
  description = "OpenVPN username"
  type        = string
  default     = "vpnuser"
}

variable "vpn_password" {
  description = "OpenVPN password"
  type        = string
  sensitive   = true
  # Must be provided in terraform.tfvars
}

# ============================================
# Load Balancer Variables
# ============================================
variable "lb_bandwidth" {
  description = "Bandwidth for load balancer EIP in Mbps"
  type        = number
  default     = 5
}

# ============================================
# NAT Gateway Variables
# ============================================
variable "nat_bandwidth" {
  description = "Bandwidth for NAT gateway EIP in Mbps"
  type        = number
  default     = 5
}

# ============================================
# Tags
# ============================================
variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "Somali-ASR"
  }
}

# Auto-scaling instance count variables
variable "min_instances" {
  description = "Minimum number of instances in auto-scaling group"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of instances in auto-scaling group"
  type        = number
  default     = 5
}

variable "desired_instances" {
  description = "Desired number of instances in auto-scaling group"
  type        = number
  default     = 2
}

# HTG Cloud authentication variables
variable "user_name" {
  description = "HTG Cloud username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "password" {
  description = "HTG Cloud password"
  type        = string
  default     = ""
  sensitive   = true
}

# ============================================
# HTG Cloud Authentication
# ============================================

variable "auth_url" {
  description = "HTG Cloud authentication URL"
  type        = string
  default     = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com/v3"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into instances"
  type        = string
  default     = "0.0.0.0/0"
}

# Instance image for autoscaling
variable "instance_image" {
  description = "Image ID for compute instances"
  type        = string
  default     = "Ubuntu 22.04 server 64bit"  # You can change this to match your available images
}
