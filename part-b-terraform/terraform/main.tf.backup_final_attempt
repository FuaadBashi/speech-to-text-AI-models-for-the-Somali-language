terraform {
  required_version = ">= 1.0"
  required_providers {
    hcs = {
      source  = "huaweicloud/hcs"
      version = "~> 2.4.0"
    }
  }
}

provider "hcs" {
  auth_url     = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
  region       = "region-02"
  project_name = var.project_name
  cloud        = "htgcloud"
  access_key   = var.access_key
  secret_key   = var.secret_key
  insecure     = true
  
  endpoints = {
    ecs = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs = "https://evs.htgcloud-region-02.htgclouds.com"
    elb = "https://elb.htgcloud-region-02.htgclouds.com"
    ims = "https://ims.htgcloud-region-02.htgclouds.com"
    obs = "https://obsv3.htgcloud-region-02.htgclouds.com"
    eip = "https://eip.htgcloud-region-02.htgclouds.com"
    nat = "https://nat.htgcloud-region-02.htgclouds.com"
    as  = "https://as.htgcloud-region-02.htgclouds.com"
    rds = "https://rds.htgcloud-region-02.htgclouds.com"
    ces = "https://ces.htgcloud-region-02.htgclouds.com"
  }
}
