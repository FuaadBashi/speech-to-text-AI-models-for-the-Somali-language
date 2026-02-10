# Availability Zones
data "huaweicloud_availability_zones" "available" {}

# Get available BMS (Bare Metal Server) flavors as ECS flavors don't exist
data "huaweicloud_bms_flavors" "main" {
  availability_zone = data.huaweicloud_availability_zones.available.names[0]
}

# For images, we'll use a variable instead since huaweicloud_images data source doesn't exist
# You'll need to get the image ID from your HCS console or administrator
