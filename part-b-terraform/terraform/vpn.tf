# VPN/Bastion Host ECS Instance
# This provides admin access to private resources via OpenVPN

# EIP for VPN server
resource "huaweicloud_vpc_eip" "vpn" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.project_name}-${var.environment}-vpn-eip"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn-eip"
    Environment = var.environment
  }
}

# Security Group for VPN Server
resource "huaweicloud_networking_secgroup" "vpn" {
  name                 = "${var.project_name}-${var.environment}-vpn-sg"
  description          = "Security group for VPN/Bastion server"
  delete_default_rules = true
}

# VPN - Allow OpenVPN (UDP 1194)
resource "huaweicloud_networking_secgroup_rule" "vpn_openvpn_ingress" {
  security_group_id = huaweicloud_networking_secgroup.vpn.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "udp"
  port_range_min    = 1194
  port_range_max    = 1194
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow OpenVPN"
}

# VPN - Allow SSH from admin
resource "huaweicloud_networking_secgroup_rule" "vpn_ssh_ingress" {
  security_group_id = huaweicloud_networking_secgroup.vpn.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.admin_cidr
  description       = "Allow SSH from admin"
}

# VPN - Allow all outbound
resource "huaweicloud_networking_secgroup_rule" "vpn_egress" {
  security_group_id = huaweicloud_networking_secgroup.vpn.id
  direction         = "egress"
  ethertype         = "IPv4"
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow all outbound"
}

# VPN Server Instance
resource "huaweicloud_compute_instance" "vpn" {
  name              = "${var.project_name}-${var.environment}-vpn"
  image_id          = data.huaweicloud_images_image.ubuntu.id
  flavor_id         = "s6.small.1"
  key_pair          = var.key_pair_name
  security_group_ids = [huaweicloud_networking_secgroup.vpn.id]
  availability_zone = var.availability_zone

  network {
    uuid = huaweicloud_vpc_subnet.public.id
  }

  # User data to install OpenVPN
  user_data = <<-EOF
              #!/bin/bash
              set -e
              
              # Log everything
              exec > >(tee -a /var/log/vpn-setup.log)
              exec 2>&1
              
              echo "Starting VPN server setup at $(date)"
              
              # Update system
              apt-get update
              apt-get upgrade -y
              
              # Install OpenVPN
              apt-get install -y openvpn easy-rsa
              
              echo "VPN server packages installed at $(date)"
              
              # Note: Manual configuration required after deployment
              # See README for OpenVPN setup instructions
              EOF

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn"
    Environment = var.environment
    Role        = "vpn-bastion"
  }
}

# Associate EIP with VPN server
resource "huaweicloud_compute_eip_associate" "vpn" {
  public_ip   = huaweicloud_vpc_eip.vpn.address
  instance_id = huaweicloud_compute_instance.vpn.id
}
