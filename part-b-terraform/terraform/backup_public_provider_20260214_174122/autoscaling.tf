# Autoscaling Configuration for Web Tier

resource "hcs_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-web-as-config"
  
  instance_config {
    flavor    = var.instance_flavor
    image     = var.instance_image
    key_name  = hcs_compute_keypair.main.id
    
    disk {
      size        = 40
      volume_type = "SSD"
      disk_type   = "SYS"
    }
    
    security_group_ids = [hcs_networking_secgroup.web.id]
  }
}

resource "hcs_as_group" "main" {
  scaling_group_name       = "${var.project_name}-web-as-group"
  scaling_configuration_id = hcs_as_configuration.main.id
  
  min_instance_number = 2
  max_instance_number = 6
  desire_instance_number = 2
  
  vpc_id = hcs_vpc.main.id
  
  networks {
    id = hcs_vpc_subnet.private.id
  }
  
  # Attach to load balancer pool
  lbaas_listeners {
    pool_id       = hcs_elb_pool.main.id
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
resource "hcs_as_policy" "scale_up" {
  scaling_policy_name = "${var.project_name}-scale-up"
  scaling_policy_type = "ALARM"
  scaling_group_id    = hcs_as_group.main.id
  
  alarm_id = hcs_ces_alarmrule.cpu_high.id
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  cool_down_time = 300
}

# Scale down policy  
resource "hcs_as_policy" "scale_down" {
  scaling_policy_name = "${var.project_name}-scale-down"
  scaling_policy_type = "ALARM"
  scaling_group_id    = hcs_as_group.main.id
  
  alarm_id = hcs_ces_alarmrule.cpu_low.id
  
  scaling_policy_action {
    operation       = "REMOVE"
    instance_number = 1
  }
  
  cool_down_time = 300
}

# CPU High Alarm for scale up
resource "hcs_ces_alarmrule" "cpu_high" {
  alarm_name = "${var.project_name}-cpu-high"
  
  metric {
    namespace   = "SYS.AS"
    metric_name = "cpu_util"
    dimensions {
      name  = "AutoScalingGroup"
      value = hcs_as_group.main.id
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
resource "hcs_ces_alarmrule" "cpu_low" {
  alarm_name = "${var.project_name}-cpu-low"
  
  metric {
    namespace   = "SYS.AS"
    metric_name = "cpu_util"
    dimensions {
      name  = "AutoScalingGroup"
      value = hcs_as_group.main.id
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
