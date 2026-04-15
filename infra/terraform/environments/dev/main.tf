locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "voidkyun/kabi-chat"
  }

  application_secrets = {
    DATABASE_URL = {
      description = "Django DATABASE_URL for ${var.environment}"
    }
    DISCORD_CLIENT_SECRET = {
      description = "Discord OAuth client secret for ${var.environment}"
    }
    DJANGO_SECRET_KEY = {
      description = "Django secret key for ${var.environment}"
    }
    JWT_SIGNING_KEY = {
      description = "JWT signing key for ${var.environment}"
    }
  }
}

module "network" {
  source = "../../modules/network"

  name_prefix              = local.name_prefix
  vpc_cidr                 = var.vpc_cidr
  availability_zones       = var.availability_zones
  public_subnet_cidrs      = var.public_subnet_cidrs
  private_app_subnet_cidrs = var.private_app_subnet_cidrs
  private_db_subnet_cidrs  = var.private_db_subnet_cidrs
  create_nat_gateway       = var.create_nat_gateway
  tags                     = local.common_tags
}

module "ecr_backend" {
  source = "../../modules/ecr"

  repository_name = "${local.name_prefix}-backend"
  tags            = local.common_tags
}

module "secrets" {
  source = "../../modules/secrets"

  name_prefix = local.name_prefix
  secrets     = local.application_secrets
  tags        = local.common_tags
}

module "alb" {
  source = "../../modules/alb"

  name_prefix       = local.name_prefix
  vpc_id            = module.network.vpc_id
  subnet_ids        = module.network.public_subnet_ids
  container_port    = var.backend_container_port
  health_check_path = var.backend_health_check_path
  certificate_arn   = var.acm_certificate_arn
  tags              = local.common_tags
}

module "ecs_service" {
  source = "../../modules/ecs_service"

  name_prefix           = local.name_prefix
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_app_subnet_ids
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = module.alb.target_group_arn
  repository_url        = module.ecr_backend.repository_url
  image_tag             = var.backend_image_tag
  container_port        = var.backend_container_port
  cpu                   = var.backend_cpu
  memory                = var.backend_memory
  desired_count         = var.backend_desired_count
  environment_variables = merge(
    {
      AUTH_FRONTEND_CALLBACK_URL = "set-per-environment"
      DISCORD_CLIENT_ID          = "set-per-environment"
      DISCORD_REDIRECT_URI       = "set-per-environment"
      DJANGO_DEBUG               = "0"
    },
    var.app_environment_variables,
  )
  secret_arns = module.secrets.secret_arns
  tags        = local.common_tags
}

module "rds" {
  source = "../../modules/rds_postgres"

  name_prefix                = local.name_prefix
  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.private_db_subnet_ids
  allowed_security_group_ids = [module.ecs_service.security_group_id]
  db_name                    = var.db_name
  master_username            = var.db_username
  instance_class             = var.db_instance_class
  allocated_storage          = var.db_allocated_storage
  multi_az                   = var.db_multi_az
  backup_retention_period    = var.db_backup_retention_period
  deletion_protection        = var.db_deletion_protection
  skip_final_snapshot        = var.db_skip_final_snapshot
  tags                       = local.common_tags
}
