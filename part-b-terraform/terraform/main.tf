terraform {
  required_version = ">= 1.0"
  
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.86.0"
    }
  }
}

provider "huaweicloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = var.region
  auth_url   = var.auth_url
  insecure   = true
}
