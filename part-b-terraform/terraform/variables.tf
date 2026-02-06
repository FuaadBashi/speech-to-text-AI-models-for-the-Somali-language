# Authentication Variables
variable "region" {
  description = "HTG Cloud Region"
  type        = string
  default     = "Mogadishu-region-hq3"
}

variable "access_key" {
  description = "HTG Cloud Access Key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "HTG Cloud Secret Key"
  type        = string
  sensitive   = true
}

# SSH Configuration
variable "key_pair_name" {
  description = "SSH key pair name for instances"
  type        = string
}

variable "admin_cidr" {
  description = "Admin IP address in CIDR format for SSH access"
  type        = string
}

# Database Configuration
variable "db_password" {
  description = "RDS Database password"
  type        = string
  sensitive   = true
}

# Project Configuration
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "somali-asr"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "prod"
}

# Compute Configuration
variable "instance_flavor" {
  description = "ECS instance flavor/type"
  type        = string
  default     = "s6.large.2"
}

variable "availability_zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "Mogadishu-region-hq3a"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.2.0/24"
}