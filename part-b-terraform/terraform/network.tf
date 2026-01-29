# VPC
resource "huaweicloud_vpc" "main" {
  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Public Subnet (for Load Balancer and NAT Gateway)
resource "huaweicloud_vpc_subnet" "public" {
  name       = "${var.project_name}-${var.environment}-public-subnet"
  cidr       = var.public_subnet_cidr
  gateway_ip = cidrhost(var.public_subnet_cidr, 1)
  vpc_id     = huaweicloud_vpc.main.id

  # Enable DHCP
  dhcp_enable = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-subnet"
    Environment = var.environment
    Type        = "public"
  }
}

# Private Subnet (for Web Servers and Database)
resource "huaweicloud_vpc_subnet" "private" {
  name       = "${var.project_name}-${var.environment}-private-subnet"
  cidr       = var.private_subnet_cidr
  gateway_ip = cidrhost(var.private_subnet_cidr, 1)
  vpc_id     = huaweicloud_vpc.main.id

  # Enable DHCP
  dhcp_enable = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-subnet"
    Environment = var.environment
    Type        = "private"
  }
}

# NAT Gateway (for outbound internet access from private subnet)
resource "huaweicloud_vpc_eip" "nat" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.project_name}-${var.environment}-nat-eip"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-nat-eip"
    Environment = var.environment
  }
}

resource "huaweicloud_nat_gateway" "main" {
  name                = "${var.project_name}-${var.environment}-nat"
  spec                = "1"
  vpc_id              = huaweicloud_vpc.main.id
  subnet_id           = huaweicloud_vpc_subnet.public.id
  enterprise_project_id = "0"

  tags = {
    Name        = "${var.project_name}-${var.environment}-nat"
    Environment = var.environment
  }
}

resource "huaweicloud_nat_snat_rule" "main" {
  nat_gateway_id = huaweicloud_nat_gateway.main.id
  floating_ip_id = huaweicloud_vpc_eip.nat.id
  subnet_id      = huaweicloud_vpc_subnet.private.id
}
