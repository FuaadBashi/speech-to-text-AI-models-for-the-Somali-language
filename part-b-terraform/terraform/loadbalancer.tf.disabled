# EIP for Load Balancer
resource "hcs_vpc_eip" "lb" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name       = "${var.project_name}-${var.environment}-lb-bandwidth"
    size       = 10
    share_type = "PER"
  }
}

# Load Balancer
resource "hcs_elb_loadbalancer" "main" {
  name              = "${var.project_name}-${var.environment}-lb"
  vpc_id            = hcs_vpc.main.id
  cross_vpc_backend = false
  
  availability_zone = [
    data.hcs_availability_zones.available.names[0]
  ]
}

# Note: EIP association to load balancer may need to be done manually in HCS
# or through a different resource type. The vip_port_id attribute doesn't exist in HCS provider.

# Load Balancer Listener
resource "hcs_elb_listener" "main" {
  name            = "${var.project_name}-${var.environment}-listener"
  protocol        = "HTTP"
  protocol_port   = 80
  loadbalancer_id = hcs_elb_loadbalancer.main.id
}

# Load Balancer Pool
resource "hcs_elb_pool" "main" {
  name        = "${var.project_name}-${var.environment}-pool"
  protocol    = "HTTP"
  lb_method   = "ROUND_ROBIN"
  listener_id = hcs_elb_listener.main.id
}

# Health Monitor
resource "hcs_elb_monitor" "main" {
  protocol    = "HTTP"
  interval    = 20
  timeout     = 10
  max_retries = 3
  url_path    = "/"
  pool_id     = hcs_elb_pool.main.id
}
