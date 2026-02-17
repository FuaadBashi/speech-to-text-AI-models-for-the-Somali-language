# Load Balancer Security Group
resource "hcs_networking_secgroup" "lb" {
  name                 = "${var.project_name}-${var.environment}-lb-sg"
  description          = "Security group for Load Balancer"
  delete_default_rules = true
}

# LB - Allow HTTP from internet
resource "hcs_networking_secgroup_rule" "lb_http_ingress" {
  security_group_id = hcs_networking_secgroup.lb.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow HTTP from internet"
}

# LB - Allow HTTPS from internet
resource "hcs_networking_secgroup_rule" "lb_https_ingress" {
  security_group_id = hcs_networking_secgroup.lb.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow HTTPS from internet"
}

# LB - Allow all outbound
resource "hcs_networking_secgroup_rule" "lb_egress" {
  security_group_id = hcs_networking_secgroup.lb.id
  direction         = "egress"
  ethertype         = "IPv4"
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow all outbound"
}

# Web Server Security Group
resource "hcs_networking_secgroup" "web" {
  name                 = "${var.project_name}-${var.environment}-web-sg"
  description          = "Security group for Web Servers"
  delete_default_rules = true
}

# Web - Allow HTTP from LB
resource "hcs_networking_secgroup_rule" "web_http_from_lb" {
  security_group_id = hcs_networking_secgroup.web.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_group_id   = hcs_networking_secgroup.lb.id
  description       = "Allow HTTP from Load Balancer"
}

# Web - Allow SSH from admin (change admin_cidr to restrict)
resource "hcs_networking_secgroup_rule" "web_ssh_ingress" {
  security_group_id = hcs_networking_secgroup.web.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.admin_cidr
  description       = "Allow SSH from admin/VPN"
}

# Web - Allow all outbound
resource "hcs_networking_secgroup_rule" "web_egress" {
  security_group_id = hcs_networking_secgroup.web.id
  direction         = "egress"
  ethertype         = "IPv4"
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow all outbound"
}

# Database Security Group
resource "hcs_networking_secgroup" "db" {
  name                 = "${var.project_name}-${var.environment}-db-sg"
  description          = "Security group for Database"
  delete_default_rules = true
}

# DB - Allow MySQL from Web servers only
resource "hcs_networking_secgroup_rule" "db_mysql_from_web" {
  security_group_id = hcs_networking_secgroup.db.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 3306
  port_range_max    = 3306
  remote_group_id   = hcs_networking_secgroup.web.id
  description       = "Allow MySQL from Web Servers"
}

# DB - Allow all outbound
resource "hcs_networking_secgroup_rule" "db_egress" {
  security_group_id = hcs_networking_secgroup.db.id
  direction         = "egress"
  ethertype         = "IPv4"
  remote_ip_prefix  = "0.0.0.0/0"
  description       = "Allow all outbound"
}
