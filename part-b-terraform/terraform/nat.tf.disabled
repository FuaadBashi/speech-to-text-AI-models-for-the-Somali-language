# EIP for NAT Gateway - Removed unsupported charge_mode
resource "hcs_vpc_eip" "nat" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name       = "${var.project_name}-${var.environment}-nat-bandwidth"
    size       = 10
    share_type = "PER"
  }
}

# NAT Gateway
resource "hcs_nat_gateway" "main" {
  name      = "${var.project_name}-${var.environment}-nat"
  spec      = "1"
  vpc_id    = hcs_vpc.main.id
  subnet_id = hcs_vpc_subnet.public.id
}

# SNAT Rule
resource "hcs_nat_snat_rule" "main" {
  nat_gateway_id = hcs_nat_gateway.main.id
  subnet_id      = hcs_vpc_subnet.private.id
  floating_ip_id = hcs_vpc_eip.nat.id
}
