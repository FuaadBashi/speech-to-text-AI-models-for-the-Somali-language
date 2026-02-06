# Auto Scaling Configuration
# This replaces manual instances with auto-scaling group

resource "huaweicloud_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-${var.environment}-asg-config"
  instance_config {
    image    = local.ubuntu_image_id  # FIXED: Changed from data source
    flavor   = var.instance_flavor
    key_name = var.key_pair_name
    
    disk {
      size        = 40
      volume_type = "SATA"
      disk_type   = "SYS"
    }

    security_group_ids = [
      huaweicloud_networking_secgroup.web.id
    ]

    user_data = base64encode(file("${path.module}/user-data.sh"))
  }
}

resource "huaweicloud_as_group" "main" {
  scaling_group_name       = "${var.project_name}-${var.environment}-asg"
  scaling_configuration_id = huaweicloud_as_configuration.main.id
  
  min_instance_number = 2
  max_instance_number = 4
  desire_instance_number = 2
  
  vpc_id = huaweicloud_vpc.main.id
  
  networks {
    id = huaweicloud_vpc_subnet.private.id
  }
  
  lbaas_listeners {
    pool_id       = huaweicloud_elb_pool.main.id
    protocol_port = 80
  }
  
  delete_instances = "yes"
  delete_publicip  = true
  
  tags = {
    Environment = var.environment
    Name        = "${var.project_name}-${var.environment}-asg"
  }
}

# Scaling Policy - Scale up when CPU > 70%
resource "huaweicloud_as_policy" "scale_up" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-up"
  scaling_group_id    = huaweicloud_as_group.main.id
  scaling_policy_type = "ALARM"
  alarm_id            = huaweicloud_ces_alarmrule.cpu_high.id
  
  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
  
  cool_down_time = 300
}

# Scaling Policy - Scale down when CPU < 30%
resource "huaweicloud_as_policy" "scale_down" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-down"
  scaling_group_id    = huaweicloud_as_group.main.id
  scaling_policy_type = "ALARM"
  alarm_id            = huaweicloud_ces_alarmrule.cpu_low.id
  
  scaling_policy_action {
    operation       = "REMOVE"
    instance_number = 1
  }
  
  cool_down_time = 300
}

# Cloud Eye Alarm - High CPU
resource "huaweicloud_ces_alarmrule" "cpu_high" {
  alarm_name           = "${var.project_name}-${var.environment}-cpu-high"
  alarm_description    = "Trigger when CPU usage exceeds 70%"
  alarm_enabled        = true
  alarm_level          = 2
  alarm_action_enabled = true
  
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
    unit                = "%"
    count               = 1
  }
}

# Cloud Eye Alarm - Low CPU
resource "huaweicloud_ces_alarmrule" "cpu_low" {
  alarm_name           = "${var.project_name}-${var.environment}-cpu-low"
  alarm_description    = "Trigger when CPU usage is below 30%"
  alarm_enabled        = true
  alarm_level          = 2
  alarm_action_enabled = true
  
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
    unit                = "%"
    count               = 1
  }
}
