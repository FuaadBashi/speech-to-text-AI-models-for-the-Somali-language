# VPC
resource "hcs_vpc" "main" {
  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr

}

# Public Subnet (for Load Balancer and NAT Gateway)
resource "hcs_vpc_subnet" "public" {
  name       = "${var.project_name}-${var.environment}-public-subnet"
  cidr       = var.public_subnet_cidr
  gateway_ip = cidrhost(var.public_subnet_cidr, 1)
  vpc_id     = hcs_vpc.main.id

  # Enable DHCP
  dhcp_enable = true

}

# Private Subnet (for Web Servers and Database)
resource "hcs_vpc_subnet" "private" {
  name       = "${var.project_name}-${var.environment}-private-subnet"
  cidr       = var.private_subnet_cidr
  gateway_ip = cidrhost(var.private_subnet_cidr, 1)
  vpc_id     = hcs_vpc.main.id

  # Enable DHCP
  dhcp_enable = true

}

# NAT Gateway (for outbound internet access from private subnet)
resource "hcs_vpc_eip" "nat" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.project_name}-${var.environment}-nat-eip"
    size        = 5
    share_type  = "PER"
  }

}

resource "hcs_nat_gateway" "main" {
  name                  = "${var.project_name}-${var.environment}-nat"
  spec                  = "1"
  vpc_id                = hcs_vpc.main.id
  subnet_id             = hcs_vpc_subnet.public.id

}

resource "hcs_nat_snat_rule" "main" {
  nat_gateway_id = hcs_nat_gateway.main.id
  floating_ip_id = hcs_vpc_eip.nat.id
  subnet_id      = hcs_vpc_subnet.private.id
}
