terraform {
  required_version = ">= 1.0"
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.67.0"
    }
  }
}

# Option 1: Minimal config - let provider figure it out
provider "huaweicloud" {
  region     = "Mogadishu-region-hq3h"
  access_key = "DHAWLD4BCTYRLU61VB4R"
  secret_key = "ND2Xv3V8XIPoJ0Mfdfe3cHAMuC6o9IBZm142JbX6"
  
  # Just point to base domain
  cloud    = "htgclouds.com"
  insecure = true
}
