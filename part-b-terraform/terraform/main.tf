# Terraform Configuration
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.86.0"
    }
  }
}

# Configure the HuaweiCloud Provider for HTG Cloud
provider "huaweicloud" {
  region      = var.region
  access_key  = var.access_key
  secret_key  = var.secret_key
  insecure    = true

  endpoints = {
    iam   = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com:443"
    ecs   = "https://ecs.htgcloud-region-02.htgclouds.com:443"
    vpc   = "https://vpc.htgcloud-region-02.htgclouds.com:443"
    evs   = "https://evs.htgcloud-region-02.htgclouds.com:443"
    obs   = "https://obsv3.htgcloud-region-02.htgclouds.com:443"
    ims   = "https://ims.htgcloud-region-02.htgclouds.com:443"
    elb   = "https://elb.htgcloud-region-02.htgclouds.com:443"
    cce   = "https://cce.htgcloud-region-02.htgclouds.com:443"
    bms   = "https://bms.htgcloud-region-02.htgclouds.com:443"
    vpcep = "https://vpcep.htgcloud-region-02.htgclouds.com:443"
    rds   = "https://rds.htgcloud-region-02.htgclouds.com:443"
    nat   = "https://nat.htgcloud-region-02.htgclouds.com:443"
  }
}