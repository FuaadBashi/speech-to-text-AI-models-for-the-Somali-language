# Root module wiring: envs/dev
#
# TODO:
# - Replace resource types and arguments to match your provider (huaweicloud vs hcso).
# - Map module outputs into downstream modules.

module "network" {
  source               = "../../modules/network"
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidr   = var.public_subnet_cidr
  private_subnet_cidr  = var.private_subnet_cidr
}

module "security" {
  source = "../../modules/security"
  vpc_id = module.network.vpc_id
}

module "lb" {
  source            = "../../modules/lb"
  vpc_id            = module.network.vpc_id
  subnet_id         = module.network.public_subnet_id
  lb_sg_id          = module.security.lb_sg_id
}

module "compute_asg" {
  source              = "../../modules/compute_asg"
  vpc_id              = module.network.vpc_id
  subnet_id           = module.network.private_subnet_id
  app_sg_id           = module.security.app_sg_id
  instance_flavor     = var.instance_flavor
  image_id            = var.image_id
  keypair_name        = var.keypair_name
  min_size            = var.min_size
  max_size            = var.max_size
  desired_capacity    = var.desired_capacity
  backend_pool_id     = module.lb.backend_pool_id
  user_data_path      = "${path.module}/../../user_data/cloud_init.yaml"
}

module "db" {
  source             = "../../modules/db"
  subnet_id          = module.network.private_subnet_id
  db_sg_id           = module.security.db_sg_id
  engine             = var.db_engine
  version            = var.db_version
  flavor             = var.db_flavor
  password           = var.db_password
}

module "vpn" {
  source      = "../../modules/vpn"
  vpc_id      = module.network.vpc_id
  subnet_id   = module.network.public_subnet_id
  peer_ip     = var.vpn_peer_ip
  psk         = var.vpn_psk
}
