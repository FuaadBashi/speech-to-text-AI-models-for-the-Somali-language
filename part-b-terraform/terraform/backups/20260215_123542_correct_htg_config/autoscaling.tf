# Auto Scaling Configuration - Using variables for image and flavor
resource "hcs_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-${var.environment}-as-config"
  
  instance_config {
    flavor   = var.web_flavor
    image    = var.web_image_id
    key_name = hcs_ecs_compute_keypair.main.id
    
    disk {
      size        = 40
      volume_type = "SATA"
      disk_type   = "SYS"
    }
  }
}

# Auto Scaling Group
resource "hcs_as_group" "main" {
  scaling_group_name       = "${var.project_name}-${var.environment}-as-group"
  scaling_configuration_id = hcs_as_configuration.main.id
  vpc_id                   = hcs_vpc.main.id
  
  networks {
    id = hcs_vpc_subnet.private.id
  }
  
  security_groups {
    id = hcs_networking_secgroup.web.id
  }
  
  lbaas_listeners {
    listener_id   = hcs_elb_listener.main.id
    pool_id       = hcs_elb_pool.main.id
    protocol_port = 80
  }
  
  min_instance_number    = 2
  max_instance_number    = 10
  desire_instance_number = 2
  
  available_zones = [var.availability_zone]
}

# Auto Scaling Policy
resource "hcs_as_policy" "main" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scaling-policy"
  scaling_group_id    = hcs_as_group.main.id
  scaling_policy_type = "RECURRENCE"
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  scheduled_policy {
    launch_time      = "07:00"
    recurrence_type  = "Daily"
    recurrence_value = "1"
  }
}
