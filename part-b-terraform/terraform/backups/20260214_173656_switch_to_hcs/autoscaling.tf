# Autoscaling Configuration for Web Tier

resource "huaweicloud_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-web-as-config"
  
  instance_config {
    flavor    = var.instance_flavor
    image     = var.instance_image
    key_name  = huaweicloud_compute_keypair.main.id
    
    disk {
      size        = 40
      volume_type = "SSD"
      disk_type   = "SYS"
    }
    
    security_group_ids = [huaweicloud_networking_secgroup.web.id]
  }
}

resource "huaweicloud_as_group" "main" {
  scaling_group_name       = "${var.project_name}-web-as-group"
  scaling_configuration_id = huaweicloud_as_configuration.main.id
  
  min_instance_number = 2
  max_instance_number = 6
  desire_instance_number = 2
  
  vpc_id = huaweicloud_vpc.main.id
  
  networks {
    id = huaweicloud_vpc_subnet.private.id
  }
  
  # Attach to load balancer pool
  lbaas_listeners {
    pool_id       = huaweicloud_elb_pool.main.id
    protocol_port = 80
  }
  
  delete_instances = "yes"
  delete_publicip  = true
  
  tags = {
    Name        = "${var.project_name}-web-as-group"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Scale up policy
resource "huaweicloud_as_policy" "scale_up" {
  scaling_policy_name = "${var.project_name}-scale-up"
  scaling_policy_type = "ALARM"
  scaling_group_id    = huaweicloud_as_group.main.id
  
  alarm_id = huaweicloud_ces_alarmrule.cpu_high.id
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  cool_down_time = 300
}

# Scale down policy  
resource "huaweicloud_as_policy" "scale_down" {
  scaling_policy_name = "${var.project_name}-scale-down"
  scaling_policy_type = "ALARM"
  scaling_group_id    = huaweicloud_as_group.main.id
  
  alarm_id = huaweicloud_ces_alarmrule.cpu_low.id
  
  scaling_policy_action {
    operation       = "REMOVE"
    instance_number = 1
  }
  
  cool_down_time = 300
}

# CPU High Alarm for scale up
resource "huaweicloud_ces_alarmrule" "cpu_high" {
  alarm_name = "${var.project_name}-cpu-high"
  
  metric {
    namespace   = "SYS.AS"
    metric_name = "cpu_util"
    dimensions {
      name  = "AutoScalingGroup"
      value = huaweicloud_as_group.main.id
    }
  }
  
  condition {
    period              = 300
    filter              = "average"
    comparison_operator = ">"
    value               = 70
    count               = 1
  }
  
  alarm_enabled = true
  alarm_level   = 2
}

# CPU Low Alarm for scale down
resource "huaweicloud_ces_alarmrule" "cpu_low" {
  alarm_name = "${var.project_name}-cpu-low"
  
  metric {
    namespace   = "SYS.AS"
    metric_name = "cpu_util"
    dimensions {
      name  = "AutoScalingGroup"
      value = huaweicloud_as_group.main.id
    }
  }
  
  condition {
    period              = 300
    filter              = "average"
    comparison_operator = "<"
    value               = 30
    count               = 3
  }
  
  alarm_enabled = true
  alarm_level   = 3
}
