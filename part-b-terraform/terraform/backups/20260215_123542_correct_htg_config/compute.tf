# SSH Key Pair
resource "hcs_ecs_compute_keypair" "main" {
  name       = "${var.project_name}-${var.environment}-keypair"
  public_key = file("~/.ssh/id_rsa.pub")
}

# Bastion Host - Using variables for image and flavor
resource "hcs_ecs_compute_instance" "bastion" {
  name               = "${var.project_name}-${var.environment}-bastion"
  image_id           = var.bastion_image_id
  flavor_id          = var.bastion_flavor
  security_group_ids = [hcs_networking_secgroup.bastion.id]
  availability_zone  = var.availability_zone
  key_pair           = hcs_ecs_compute_keypair.main.name

  network {
    uuid = hcs_vpc_subnet.public.id
  }
}

# EIP for Bastion - Removed unsupported charge_mode
resource "hcs_vpc_eip" "bastion" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name       = "${var.project_name}-${var.environment}-bastion-bandwidth"
    size       = 5
    share_type = "PER"
  }
}

resource "hcs_ecs_compute_eip_associate" "bastion" {
  public_ip   = hcs_vpc_eip.bastion.address
  instance_id = hcs_ecs_compute_instance.bastion.id
}
