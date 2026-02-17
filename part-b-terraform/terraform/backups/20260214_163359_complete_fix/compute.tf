
locals { 
  ubuntu_image_id = "bb050e32-4c21-433a-ba73-9d32bef446e9"
}


resource "huaweicloud_vpc_eip" "test_instance" {
  count = 0 

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
  count = 0 

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

resource "huaweicloud_compute_eip_associate" "test_web" {
  count = 0 # Set to 1 to enable

  public_ip   = huaweicloud_vpc_eip.test_instance[count.index].address
  instance_id = huaweicloud_compute_instance.test_web[count.index].id
}