terraform {
  required_version = ">= 1.5.0"
  required_providers {
    hcs = {
      source  = "huaweicloud/hcs"
      version = "~> 2.4.0"
    }
  }
}

provider "hcs" {
  region     = "region-02"
  project_id = "fdff1c30076d4a29830d60cc6b73cbeb"
  access_key = var.access_key
  secret_key = var.secret_key
  insecure   = true

  endpoints = {
    iam          = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"
    ecs          = "https://ecs.htgcloud-region-02.htgclouds.com"
    vpc          = "https://vpc.htgcloud-region-02.htgclouds.com"
    evs          = "https://evs.htgcloud-region-02.htgclouds.com"
    elb          = "https://elb.htgcloud-region-02.htgclouds.com"
    eip          = "https://vpc.htgcloud-region-02.htgclouds.com"
    ims          = "https://ims.htgcloud-region-02.htgclouds.com"
    obs          = "https://obsv3.htgcloud-region-02.htgclouds.com"
    autoscaling  = "https://as.htgcloud-region-02.htgclouds.com"
    rds          = "https://rds.htgcloud-region-02.htgclouds.com"
    nat          = "https://nat.htgcloud-region-02.htgclouds.com"
  }
}
