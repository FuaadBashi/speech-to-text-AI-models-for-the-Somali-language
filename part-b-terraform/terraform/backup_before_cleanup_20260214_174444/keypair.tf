# SSH Keypair
resource "hcs_compute_keypair" "main" {
  name       = "${var.project_name}-${var.environment}-keypair"
  public_key = file(pathexpand("~/.ssh/id_rsa.pub"))
}
