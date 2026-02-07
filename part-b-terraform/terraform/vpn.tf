# VPN/Bastion Server Configuration
# Provides secure administrative access to private resources

# Security Group for VPN/Bastion
resource "huaweicloud_networking_secgroup" "vpn" {
  name                 = "${var.project_name}-${var.environment}-vpn-sg"
  description          = "Security group for VPN/Bastion server"
  delete_default_rules = true
}

# Allow SSH from admin IP
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

# Allow OpenVPN (UDP 1194)
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

# Allow all outbound
resource "huaweicloud_networking_secgroup_rule" "vpn_egress" {
  security_group_id = huaweicloud_networking_secgroup.vpn.id
  direction         = "egress"
  ethertype         = "IPv4"
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow all outbound"
}

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

# VPN/Bastion Instance
resource "huaweicloud_compute_instance" "vpn" {
  name               = "${var.project_name}-${var.environment}-vpn"
  image_id           = local.ubuntu_image_id # FIXED: Changed from data source
  flavor_id          = "s6.small.1"          # Small instance is sufficient
  key_pair           = var.key_pair_name
  security_group_ids = [huaweicloud_networking_secgroup.vpn.id]
  availability_zone  = var.availability_zone

  network {
    uuid = huaweicloud_vpc_subnet.public.id
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install OpenVPN
    apt-get install -y openvpn easy-rsa
    
    # Enable IP forwarding
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    sysctl -p
    
    # Create setup script for later configuration
    cat > /root/setup-openvpn.sh <<'SETUP'
    #!/bin/bash
    # OpenVPN setup script
    # Run this after connecting via SSH
    
    # Initialize PKI
    make-cadir ~/openvpn-ca
    cd ~/openvpn-ca
    
    # Configure vars
    echo "Setup complete. Follow OpenVPN documentation to complete PKI setup."
    SETUP
    
    chmod +x /root/setup-openvpn.sh
    
    # Log completion
    echo "VPN server setup complete at $(date)" > /var/log/vpn-setup.log
  EOF

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn"
    Environment = var.environment
    Role        = "vpn-bastion"
  }
}

# Associate EIP with VPN instance
resource "huaweicloud_compute_eip_associate" "vpn" {
  public_ip   = huaweicloud_vpc_eip.vpn.address
  instance_id = huaweicloud_compute_instance.vpn.id
}
