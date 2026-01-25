output "lb_public_ip" {
  description = "Public IP / address of the load balancer (use to test the app)."
  value       = module.lb.lb_public_ip
}
