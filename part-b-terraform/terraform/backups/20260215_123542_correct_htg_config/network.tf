# VPC
resource "hcs_vpc" "main" {
  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr
}

# Public Subnet
resource "hcs_vpc_subnet" "public" {
  name       = "${var.project_name}-${var.environment}-public-subnet"
  cidr       = var.public_subnet_cidr
  gateway_ip = cidrhost(var.public_subnet_cidr, 1)
  vpc_id     = hcs_vpc.main.id
}

# Private Subnet
resource "hcs_vpc_subnet" "private" {
  name       = "${var.project_name}-${var.environment}-private-subnet"
  cidr       = var.private_subnet_cidr
  gateway_ip = cidrhost(var.private_subnet_cidr, 1)
  vpc_id     = hcs_vpc.main.id
}
