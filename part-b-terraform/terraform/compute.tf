# Use a common Ubuntu 22.04 image ID for HTG Cloud
locals {
  # This will be replaced with actual image ID from console
  ubuntu_image_id = "REPLACE_WITH_ACTUAL_IMAGE_ID"
}

# EIP for test instance (disabled by default)
resource "huaweicloud_vpc_eip" "test_instance" {
  count = 0 # Set to 1 to enable test instance

  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.project_name}-${var.environment}-test-eip-${count.index + 1}"
    size        = 5
    share_type  = "PER"
  }

}

# Test ECS Instance (disabled by default)
resource "huaweicloud_compute_instance" "test_web" {
  count = 0 # Set to 1 to enable test instance

  name               = "${var.project_name}-${var.environment}-test-web-${count.index + 1}"
  image_id           = local.ubuntu_image_id
  flavor_id          = var.instance_flavor
  key_pair           = var.key_pair_name
  security_group_ids = [huaweicloud_networking_secgroup.web.id]
  availability_zone  = var.availability_zone

  network {
    uuid = huaweicloud_vpc_subnet.public.id
  }

  user_data = file("${path.module}/user-data.sh")

}

# Associate EIP with test instance
resource "huaweicloud_compute_eip_associate" "test_web" {
  count = 0 # Set to 1 to enable

  public_ip   = huaweicloud_vpc_eip.test_instance[count.index].address
  instance_id = huaweicloud_compute_instance.test_web[count.index].id
}