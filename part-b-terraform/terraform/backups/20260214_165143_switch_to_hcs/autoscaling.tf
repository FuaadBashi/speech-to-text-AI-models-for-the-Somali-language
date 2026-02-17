# Auto Scaling Configuration
resource "huaweicloud_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-${var.environment}-as-config"
  
  instance_config {
    flavor    = data.huaweicloud_compute_flavors.main.ids[0]
    image     = var.image_id
    key_name  = huaweicloud_compute_keypair.main.id
    
    disk {
      size        = 40
      volume_type = "SAS"
      disk_type   = "SYS"
    }
  }
}

resource "huaweicloud_as_group" "main" {
  scaling_group_name       = "${var.project_name}-${var.environment}-as-group"
  scaling_configuration_id = huaweicloud_as_configuration.main.id
  
  min_instance_number = var.min_instances
  max_instance_number = var.max_instances
  desire_instance_number = var.desired_instances
  
  vpc_id = huaweicloud_vpc.main.id
  
  networks {
    id = huaweicloud_vpc_subnet.private.id
  }
  
  lbaas_listeners {
    listener_id   = huaweicloud_elb_listener.http.id
    pool_id       = huaweicloud_elb_pool.main.id
    protocol_port = 80
  }
  
  delete_publicip = true
  delete_instances = "yes"
}

resource "huaweicloud_as_policy" "scale_up" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-up"
  scaling_group_id    = huaweicloud_as_group.main.id
  scaling_policy_type = "ALARM"
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  cool_down_time = 300
}

resource "huaweicloud_as_policy" "scale_down" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-down"
  scaling_group_id    = huaweicloud_as_group.main.id
  scaling_policy_type = "ALARM"
  
  scaling_policy_action {
    operation       = "REMOVE"
    instance_number = 1
  }
  
  cool_down_time = 300
}
