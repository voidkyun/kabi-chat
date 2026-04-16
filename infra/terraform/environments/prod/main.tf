terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "early_access_stack" {
  source = "../../modules/lightsail_early_access"

  instance_name        = "${var.project_name}-prod"
  availability_zone    = var.availability_zone
  blueprint_id         = var.blueprint_id
  bundle_id            = var.bundle_id
  key_pair_name        = var.key_pair_name
  user_data            = var.user_data
  enable_static_ip     = true
  enable_auto_snapshot = true
  snapshot_time_utc    = var.snapshot_time_utc
  public_ports = [
    {
      protocol  = "tcp"
      from_port = 80
      to_port   = 80
      cidrs     = ["0.0.0.0/0"]
    },
    {
      protocol  = "tcp"
      from_port = 443
      to_port   = 443
      cidrs     = ["0.0.0.0/0"]
    },
    {
      protocol  = "tcp"
      from_port = 22
      to_port   = 22
      cidrs     = var.ssh_allowed_cidrs
    }
  ]
  tags = {
    Project     = var.project_name
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

output "instance_name" {
  value = module.early_access_stack.instance_name
}

output "public_ip_address" {
  value = module.early_access_stack.public_ip_address
}

output "ssh_username" {
  value = module.early_access_stack.username
}
