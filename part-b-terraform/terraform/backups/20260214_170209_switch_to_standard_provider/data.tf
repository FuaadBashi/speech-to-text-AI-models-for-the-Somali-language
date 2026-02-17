# Availability zones
data "hcs_availability_zones" "available" {
  state = "available"
}

# Compute flavors for autoscaling
# Changed from hcs_bms_flavors to hcs_compute_flavors
data "hcs_compute_flavors" "main" {
  availability_zone = "hq3_AZ1"
  performance_type  = "normal"
  cpu_core_count    = 2
  memory_size       = 4
}
