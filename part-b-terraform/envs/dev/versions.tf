terraform {
  required_version = ">= 1.5.0"

  required_providers {
    # Choose ONE provider below depending on your environment.
    # huaweicloud = {
    #   source  = "huaweicloud/huaweicloud"
    #   version = ">= 1.62.0"
    # }

    hcso = {
      source  = "huaweicloud/hcso"
      version = ">= 1.0.0"
    }
  }
}
