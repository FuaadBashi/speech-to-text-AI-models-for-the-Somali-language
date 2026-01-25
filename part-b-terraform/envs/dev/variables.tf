variable "region" { type = string, default = "" }

# Network
variable "vpc_cidr" { type = string, default = "10.0.0.0/16" }
variable "public_subnet_cidr" { type = string, default = "10.0.1.0/24" }
variable "private_subnet_cidr" { type = string, default = "10.0.2.0/24" }

# Compute
variable "instance_flavor" { type = string, default = "" }
variable "image_id" { type = string, default = "" }
variable "keypair_name" { type = string, default = "" }
variable "min_size" { type = number, default = 2 }
variable "max_size" { type = number, default = 4 }
variable "desired_capacity" { type = number, default = 2 }

# DB (RDS)
variable "db_engine" { type = string, default = "mysql" }
variable "db_version" { type = string, default = "" }
variable "db_flavor" { type = string, default = "" }
variable "db_password" { type = string, sensitive = true, default = "" }

# VPN
variable "vpn_peer_ip" { type = string, default = "" }
variable "vpn_psk" { type = string, sensitive = true, default = "" }
