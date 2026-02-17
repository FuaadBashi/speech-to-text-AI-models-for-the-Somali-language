terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    hcs = {
      source  = "huaweicloud/hcs"
      version = "~> 2.4.0"
    }
  }
}

provider "hcs" {
  region      = "Mogadishu-region-hq3h"
  access_key  = var.access_key
  secret_key  = var.secret_key
  tenant_name = "htgcloud-region-02"
  insecure    = true
}
