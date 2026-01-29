# Note: This file creates initial test instances
# For production, these will be replaced by auto-scaling group

# Get the latest Ubuntu 22.04 image
data "huaweicloud_images_image" "ubuntu" {
  name        = "Ubuntu 22.04 server 64bit"
  most_recent = true
  visibility  = "public"
}

# EIP for test instance (temporary - remove when using private subnet)
resource "huaweicloud_vpc_eip" "test_instance" {
  count = 1  # Set to 0 when using auto-scaling

  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.project_name}-${var.environment}-test-eip-${count.index + 1}"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-test-eip-${count.index + 1}"
    Environment = var.environment
  }
}

# Test ECS Instance (for initial testing)
resource "huaweicloud_compute_instance" "test_web" {
  count = 1  # Set to 0 when using auto-scaling

  name              = "${var.project_name}-${var.environment}-test-web-${count.index + 1}"
  image_id          = data.huaweicloud_images_image.ubuntu.id
  flavor_id         = var.instance_flavor
  key_pair          = var.key_pair_name
  security_group_ids = [huaweicloud_networking_secgroup.web.id]
  availability_zone = var.availability_zone

  network {
    uuid = huaweicloud_vpc_subnet.public.id  # Change to private subnet later
  }

  user_data = file("${path.module}/user-data.sh")

  tags = {
    Name        = "${var.project_name}-${var.environment}-test-web-${count.index + 1}"
    Environment = var.environment
    Role        = "web-server"
  }
}

# Associate EIP with test instance
resource "huaweicloud_compute_eip_associate" "test_web" {
  count = 1  # Set to 0 when using auto-scaling

  public_ip   = huaweicloud_vpc_eip.test_instance[count.index].address
  instance_id = huaweicloud_compute_instance.test_web[count.index].id
}
