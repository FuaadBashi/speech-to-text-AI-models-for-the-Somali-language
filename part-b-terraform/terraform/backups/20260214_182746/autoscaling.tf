# Auto Scaling Configuration
resource "hcs_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-${var.environment}-as-config"
  
  instance_config {
    flavor    = data.hcs_ecs_flavors.main.ids[0]
    image     = data.hcs_images.main.images[0].id
    key_name  = hcs_ecs_compute_keypair.main.id
    
    disk {
      size        = 40
      volume_type = "SAS"
      disk_type   = "SYS"
    }
    
    security_groups = [hcs_networking_secgroup.web.id]
  }
}

resource "hcs_as_group" "main" {
  scaling_group_name       = "${var.project_name}-${var.environment}-as-group"
  scaling_configuration_id = hcs_as_configuration.main.id
  
  min_instance_number = var.min_instances
  max_instance_number = var.max_instances
  desire_instance_number = var.desired_instances
  
  vpc_id = hcs_vpc.main.id
  
  networks {
    id = hcs_vpc_subnet.private.id
  }
  
  security_groups {
    id = hcs_networking_secgroup.web.id
  }
  
  lbaas_listeners {
    pool_id       = hcs_elb_pool.main.id
    protocol_port = 80
  }
  
  delete_publicip = true
  delete_instances = "yes"
}

resource "hcs_as_policy" "scale_up" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-up"
  scaling_group_id    = hcs_as_group.main.id
  scaling_policy_type = "ALARM"
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  cool_down_time = 300
}

resource "hcs_as_policy" "scale_down" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-down"
  scaling_group_id    = hcs_as_group.main.id
  scaling_policy_type = "ALARM"
  
  scaling_policy_action {
    operation       = "REMOVE"
    instance_number = 1
  }
  
  cool_down_time = 300
}
