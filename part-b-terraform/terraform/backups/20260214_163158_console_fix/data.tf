# Availability Zones
data "huaweicloud_availability_zones" "available" {}

data "huaweicloud_bms_flavors" "main" {
  availability_zone = data.huaweicloud_availability_zones.available.names[0]
}
