# RDS MySQL Instance
resource "hcs_rds_instance" "main" {
  name              = "${var.project_name}-${var.environment}-mysql"
  flavor            = var.db_flavor
  vpc_id            = hcs_vpc.main.id
  subnet_id         = hcs_vpc_subnet.private.id
  security_group_id = hcs_networking_secgroup.db.id
  availability_zone = [var.availability_zone]

  db {
    type     = "MySQL"
    version  = "8.0"
    password = var.db_password
  }

  volume {
    type = "CLOUDSSD"
    size = 40
  }

  backup_strategy {
    start_time = "08:00-09:00"
    keep_days  = 7
  }
}
