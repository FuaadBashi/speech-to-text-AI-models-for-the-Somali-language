variable "vpc_id" { type = string }
variable "subnet_id" { type = string }
variable "peer_ip" { type = string }
variable "psk" { type = string, sensitive = true }

# TODO: Create VPN gateway + connection/tunnel to peer_ip using psk
output "vpn_id" { value = null }
