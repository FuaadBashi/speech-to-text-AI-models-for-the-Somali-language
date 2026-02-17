# Data sources for HTG Cloud

# Availability zones - use the actual AZ from your console
# Your instances show: hq3_AZ1
data "huaweicloud_availability_zones" "available" {
  # Filter available zones
  state = "available"
}

# Note: Based on console, your AZ is "hq3_AZ1"
# If data source fails, hardcode it in resources as:
# availability_zone = "hq3_AZ1"
