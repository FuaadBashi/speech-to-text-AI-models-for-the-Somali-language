# Security Group for Bastion
resource "hcs_networking_secgroup" "bastion" {
  name        = "${var.project_name}-${var.environment}-bastion-sg"
  description = "Security group for bastion host"
}

resource "hcs_networking_secgroup_rule" "bastion_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = hcs_networking_secgroup.bastion.id
}

# Security Group for Web Servers
resource "hcs_networking_secgroup" "web" {
  name        = "${var.project_name}-${var.environment}-web-sg"
  description = "Security group for web servers"
}

resource "hcs_networking_secgroup_rule" "web_http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = hcs_networking_secgroup.web.id
}

resource "hcs_networking_secgroup_rule" "web_https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = hcs_networking_secgroup.web.id
}

resource "hcs_networking_secgroup_rule" "web_ssh_from_bastion" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_group_id   = hcs_networking_secgroup.bastion.id
  security_group_id = hcs_networking_secgroup.web.id
}

# Security Group for Database
resource "hcs_networking_secgroup" "db" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Security group for database"
}

resource "hcs_networking_secgroup_rule" "db_mysql" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 3306
  port_range_max    = 3306
  remote_group_id   = hcs_networking_secgroup.web.id
  security_group_id = hcs_networking_secgroup.db.id
}

# Security Group for Load Balancer
resource "hcs_networking_secgroup" "lb" {
  name        = "${var.project_name}-${var.environment}-lb-sg"
  description = "Security group for load balancer"
}

resource "hcs_networking_secgroup_rule" "lb_http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = hcs_networking_secgroup.lb.id
}

resource "hcs_networking_secgroup_rule" "lb_https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = hcs_networking_secgroup.lb.id
}
