# Project Configuration
variable "project_name" {
  description = "Project name in HTG Cloud"
  type        = string
  default     = "htgcloud-region-02"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# HTG Cloud Credentials
variable "access_key" {
  description = "HTG Cloud Access Key"
  type        = string
  default     = "DHAWLD4BCTYRLU61VB4R"
}

variable "secret_key" {
  description = "HTG Cloud Secret Key"
  type        = string
  sensitive   = true
  default     = "ND2Xv3V8XIPoJ0Mfdfe3cHAMuC6o9IBZm142JbX6"
}

# Network Configuration
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
  description = "Availability zone"
  type        = string
  default     = "region-02a"
}

# Compute Configuration
variable "instance_flavor" {
  description = "Instance flavor/type"
  type        = string
  default     = "s3.large.2"
}

variable "instance_image" {
  description = "Image ID for compute instances"
  type        = string
  default     = "Ubuntu 22.04 server 64bit"
}

variable "key_pair_name" {
  description = "SSH key pair name"
  type        = string
  default     = "htg-devops-key"
}

# Database Configuration
variable "db_flavor" {
  description = "RDS instance flavor"
  type        = string
  default     = "rds.mysql.s1.medium"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "dbadmin"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  default     = "DbPassword123!"
  sensitive   = true
}

# Web Server Configuration
variable "web_flavor" {
  description = "Flavor for web servers"
  type        = string
  default     = "s3.large.2"
}

variable "web_image_id" {
  description = "Image ID for web servers"
  type        = string
  default     = "Ubuntu 22.04 server 64bit"
}

# Bastion/VPN Configuration
variable "bastion_flavor" {
  description = "Flavor for bastion/VPN server"
  type        = string
  default     = "s3.medium.2"
}

variable "bastion_image_id" {
  description = "Image ID for bastion server"
  type        = string
  default     = "Ubuntu 22.04 server 64bit"
}

variable "region" {
  description = "HTG Cloud region"
  type        = string
  default     = "region-02"
}
