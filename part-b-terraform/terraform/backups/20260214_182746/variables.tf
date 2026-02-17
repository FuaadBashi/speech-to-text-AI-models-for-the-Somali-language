variable "region" {
  description = "HTG Cloud region"
  type        = string
  default     = "Mogadishu-region-hq3h"
}

variable "availability_zone" {
  description = "Availability zone"
  type        = string
  default     = "hq3_AZ1"
}

variable "access_key" {
  description = "HTG Cloud access key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "HTG Cloud secret key"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "ai-devops"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Private subnet CIDR"
  type        = string
  default     = "10.0.2.0/24"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_flavor" {
  description = "RDS instance flavor"
  type        = string
  default     = "rds.mysql.s1.medium"
}

variable "bastion_flavor" {
  description = "Bastion host flavor"
  type        = string
  default     = "s3.medium.2"
}

variable "web_flavor" {
  description = "Web server flavor"
  type        = string
  default     = "s3.medium.2"
}

variable "bastion_image_id" {
  description = "Bastion host image ID (leave empty to skip)"
  type        = string
  default     = ""
}

variable "web_image_id" {
  description = "Web server image ID (leave empty to skip)"
  type        = string
  default     = ""
}

variable "key_pair_name" {
  description = "SSH key pair name"
  type        = string
  default     = "my-keypair"
}
