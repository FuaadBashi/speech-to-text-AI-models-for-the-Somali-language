# Elastic Load Balancer
resource "huaweicloud_elb_loadbalancer" "main" {
  name              = "${var.project_name}-${var.environment}-elb"
  availability_zone = ["region-02a"] 
  vpc_id            = huaweicloud_vpc.main.id
  ipv4_subnet_id    = huaweicloud_vpc_subnet.public.ipv4_subnet_id
  cross_vpc_backend = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-elb"
    Environment = var.environment
  }
}

# EIP for Load Balancer
resource "huaweicloud_vpc_eip" "lb" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.project_name}-${var.environment}-lb-eip"
    size        = 10
    share_type  = "PER"
    charge_mode = "traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-lb-eip"
    Environment = var.environment
  }
}

# Associate EIP with Load Balancer
resource "huaweicloud_elb_ipgroup" "lb_eip" {
  name = "${var.project_name}-${var.environment}-lb-ipgroup"

  ip_list {
    ip          = huaweicloud_vpc_eip.lb.address
    description = "Load Balancer EIP"
  }
}

# HTTP Listener
resource "huaweicloud_elb_listener" "http" {
  name            = "${var.project_name}-${var.environment}-http-listener"
  protocol        = "HTTP"
  protocol_port   = 80
  loadbalancer_id = huaweicloud_elb_loadbalancer.main.id

  tags = {
    Name        = "${var.project_name}-${var.environment}-http-listener"
    Environment = var.environment
  }
}

# Backend Server Group
resource "huaweicloud_elb_pool" "main" {
  name            = "${var.project_name}-${var.environment}-pool"
  protocol        = "HTTP"
  lb_method       = "ROUND_ROBIN"
  listener_id     = huaweicloud_elb_listener.http.id

  # Persistence settings (optional)
  persistence {
    type        = "HTTP_COOKIE"
    cookie_name = "SERVERID"
  }
}

# Health Check
resource "huaweicloud_elb_monitor" "main" {
  pool_id     = huaweicloud_elb_pool.main.id
  protocol    = "HTTP"
  interval    = 30
  timeout     = 10
  max_retries = 3
  url_path    = "/"
  port        = 80
  status_code = "200"
}

# Manual backend members (for testing before auto-scaling)
# Uncomment these when you have test instances
/*
resource "huaweicloud_elb_member" "test_web" {
  count = length(huaweicloud_compute_instance.test_web)

  address       = huaweicloud_compute_instance.test_web[count.index].access_ip_v4
  protocol_port = 80
  pool_id       = huaweicloud_elb_pool.main.id
  subnet_id     = huaweicloud_vpc_subnet.public.ipv4_subnet_id
  weight        = 1

  name = "${var.project_name}-${var.environment}-member-${count.index + 1}"
}
*/
