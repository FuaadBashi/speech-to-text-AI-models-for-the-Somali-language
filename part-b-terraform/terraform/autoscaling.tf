# Auto Scaling Configuration
resource "huaweicloud_as_configuration" "main" {
  scaling_configuration_name = "${var.project_name}-${var.environment}-as-config"

  instance_config {
    flavor   = var.instance_flavor
    image    = data.huaweicloud_images_image.ubuntu.id
    key_name = var.key_pair_name

    disk {
      size        = 40
      volume_type = "SATA"
      disk_type   = "SYS"
    }

    security_group_ids = [huaweicloud_networking_secgroup.web.id]

    user_data = base64encode(file("${path.module}/user-data.sh"))
  }
}

# Auto Scaling Group
resource "huaweicloud_as_group" "main" {
  scaling_group_name       = "${var.project_name}-${var.environment}-as-group"
  scaling_configuration_id = huaweicloud_as_configuration.main.id
  desire_instance_number   = var.asg_desired_capacity
  min_instance_number      = var.asg_min_size
  max_instance_number      = var.asg_max_size
  vpc_id                   = huaweicloud_vpc.main.id
  delete_publicip          = true
  delete_instances         = "yes"

  networks {
    id = huaweicloud_vpc_subnet.private.id
  }

  security_groups {
    id = huaweicloud_networking_secgroup.web.id
  }

  lbaas_listeners {
    pool_id       = huaweicloud_elb_pool.main.id
    protocol_port = 80
    weight        = 1
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-as-group"
    Environment = var.environment
  }
}

# Scale Up Policy (CPU > 70%)
resource "huaweicloud_as_policy" "scale_up" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-up"
  scaling_group_id    = huaweicloud_as_group.main.id
  scaling_policy_type = "ALARM"
  alarm_id            = huaweicloud_ces_alarmrule.cpu_high.id
  cool_down_time      = 300

  scaling_policy_action {
    operation       = "ADD"
    instance_number = 1
  }
}

# Scale Down Policy (CPU < 30%)
resource "huaweicloud_as_policy" "scale_down" {
  scaling_policy_name = "${var.project_name}-${var.environment}-scale-down"
  scaling_group_id    = huaweicloud_as_group.main.id
  scaling_policy_type = "ALARM"
  alarm_id            = huaweicloud_ces_alarmrule.cpu_low.id
  cool_down_time      = 300

  scaling_policy_action {
    operation       = "REMOVE"
    instance_number = 1
  }
}

# High CPU Alarm (> 70%)
resource "huaweicloud_ces_alarmrule" "cpu_high" {
  alarm_name           = "${var.project_name}-${var.environment}-cpu-high"
  alarm_description    = "Trigger when CPU usage is above 70%"
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

# Low CPU Alarm (< 30%)
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
    count               = 3
  }
}
