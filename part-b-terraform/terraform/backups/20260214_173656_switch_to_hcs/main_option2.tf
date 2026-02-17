terraform {
  required_version = ">= 1.0"
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.67.0"
    }
  }
}

# Option 2: Single base URL
provider "huaweicloud" {
  region     = "Mogadishu-region-hq3h"
  access_key = "DHAWLD4BCTYRLU61VB4R"
  secret_key = "ND2Xv3V8XIPoJ0Mfdfe3cHAMuC6o9IBZm142JbX6"
  
  cloud      = "htgclouds.com"
  auth_url   = "https://service-hq3.htgclouds.com/v3"
  insecure   = true
}
