resource "hcs_ecs_compute_keypair" "main" {
  name       = "dev-keypair"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDfbNFLSppZjLTXVQKFstHhsGBtG091Ldt6EUXvJliX6AuvdL11dUnhS0YUrLxviFuD4Fv0iQd765YCY8MOVKOJe54o/gsw8dq92KiNLdcnm4AVGmKE+NGF4rpuzQOd6LrM2uuTTa25M7A6QU0k6AIsqipS1lxU0koIuaqn6YDbvxJKh285MWIdATPFraIgFAvnosZA6sKC7Kb6krvSq3BXVf4Kt0+TnxBYMfgWHKCY2sxyKc6DeEJt6XovGm872Mn0P7hjWk5XEBLL4ohgDehgvQCq9og7KQndx4/jZDnnfupEntWJ2fMFDWOHf09dWDo8S8gLM6m0qm62pOBVxsUnQSvcx2O6go47hgfHc7cpluhpTsrp6cqQjRdZ8iOZtkrOI8wjerJPDQR21v7J7Y8+SvItw+L2fDCUb82nZyEDGL/ssiG9ZYoAmJdQ3BDXXJfW41P9lb7jjUicM8ytoFIFr8lWVzAXOdbOV8XU3ep5my8Myhroz0BN4ydHiy103iDr5gNWkiLl02MEpi0a1ompGj5CC46b40oKTE7XaXJ5mnLpWb1iILAAA0SpKdWRqao0FSJ5agZJto55zfzbhj2TmqHyXagHyNOq8qhAhbeg+3u+gWJijAkUFP+RZQRnat62NSboJwYl0/ilNxELWmGLXHMP0TxaL+FaQkrhiU/S4w== terraform-hcs"
}

resource "hcs_ecs_compute_instance" "bastion" {
  name              = "dev-bastion"
  image_id          = "450d07fd-bf1a-407a-9063-ea829537859e"
  flavor_id         = "S6_large.1"
  key_pair          = hcs_ecs_compute_keypair.main.name
  availability_zone = "az1.hq3"

  network {
    uuid = hcs_vpc_subnet.public.id
  }

  security_group_ids = [hcs_networking_secgroup.bastion.id]
}

resource "hcs_ecs_compute_instance" "web" {
  name              = "dev-web"
  image_id          = "450d07fd-bf1a-407a-9063-ea829537859e"
  flavor_id         = "S6_large.1"
  key_pair          = hcs_ecs_compute_keypair.main.name
  availability_zone = "az1.hq3"

  network {
    uuid = hcs_vpc_subnet.private.id
  }

  security_group_ids = [hcs_networking_secgroup.web.id]
}
