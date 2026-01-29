# RDS MySQL Instance
resource "huaweicloud_rds_instance" "main" {
  name              = "${var.project_name}-${var.environment}-mysql"
  flavor            = "rds.mysql.s1.medium"
  vpc_id            = huaweicloud_vpc.main.id
  subnet_id         = huaweicloud_vpc_subnet.private.id
  security_group_id = huaweicloud_networking_secgroup.db.id
  availability_zone = [var.availability_zone]

  db {
    type     = "MySQL"
    version  = "8.0"
    password = var.db_password
    port     = 3306
  }

  volume {
    type = "CLOUDSSD"
    size = 40
  }

  backup_strategy {
    start_time = "08:00-09:00"
    keep_days  = 7
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-mysql"
    Environment = var.environment
  }
}

# Database
resource "huaweicloud_rds_database" "app_db" {
  instance_id   = huaweicloud_rds_instance.main.id
  name          = "somali_asr_db"
  character_set = "utf8mb4"
}

# Database User (optional - for application access)
resource "huaweicloud_rds_account" "app_user" {
  instance_id = huaweicloud_rds_instance.main.id
  name        = "app_user"
  password    = var.db_password

  depends_on = [huaweicloud_rds_database.app_db]
}

# Grant privileges to app user
resource "huaweicloud_rds_database_privilege" "app_user_privilege" {
  instance_id = huaweicloud_rds_instance.main.id
  db_name     = huaweicloud_rds_database.app_db.name
  users {
    name     = huaweicloud_rds_account.app_user.name
    readonly = false
  }
}
