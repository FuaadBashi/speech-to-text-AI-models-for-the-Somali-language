# Load Balancer Configuration
resource "hcs_elb_loadbalancer" "main" {
  name              = "${var.project_name}-${var.environment}-lb"
  description       = "Main load balancer"
  vpc_id            = hcs_vpc.main.id
  cross_vpc_backend = false
  
  availability_zone = [
    data.hcs_availability_zones.available.names[0]
  ]
}

resource "hcs_vpc_eip" "lb" {
  publicip {
    type = "5_bgp"
  }
  
  bandwidth {
    name        = "${var.project_name}-${var.environment}-lb-bandwidth"
    size        = 10
    share_type  = "PER"
  }
}

# resource "hcs_vpc_eip_associate" "lb" {
#   public_ip  = hcs_vpc_eip.lb.address
#   port_id    = hcs_elb_loadbalancer.main.vip_subnet_id
# }

resource "hcs_elb_listener" "http" {
  name            = "${var.project_name}-${var.environment}-http-listener"
  description     = "HTTP listener"
  protocol        = "HTTP"
  protocol_port   = 80
  loadbalancer_id = hcs_elb_loadbalancer.main.id
  
  idle_timeout     = 60
  request_timeout  = 60
  response_timeout = 60
}

resource "hcs_elb_pool" "main" {
  name        = "${var.project_name}-${var.environment}-pool"
  protocol    = "HTTP"
  lb_method   = "ROUND_ROBIN"
  listener_id = hcs_elb_listener.http.id
  
  persistence {
    type = "HTTP_COOKIE"
  }
}

resource "hcs_elb_monitor" "main" {
  pool_id     = hcs_elb_pool.main.id
  protocol    = "HTTP"
  interval    = 20
  timeout     = 10
  max_retries = 3
  url_path    = "/health"
  port        = 80
}
