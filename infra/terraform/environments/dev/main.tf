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

  instance_name        = "${var.project_name}-dev"
  availability_zone    = var.availability_zone
  blueprint_id         = var.blueprint_id
  bundle_id            = var.bundle_id
  key_pair_name        = var.key_pair_name
  user_data            = var.user_data
  enable_static_ip     = false
  enable_auto_snapshot = false
  public_ports = [
    {
      protocol  = "tcp"
      from_port = 22
      to_port   = 22
      cidrs     = var.ssh_allowed_cidrs
    },
    {
      protocol  = "tcp"
      from_port = 80
      to_port   = 80
      cidrs     = var.http_allowed_cidrs
    }
  ]
  tags = {
    Project     = var.project_name
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

output "instance_name" {
  value = module.early_access_stack.instance_name
}

output "public_ip_address" {
  value = module.early_access_stack.public_ip_address
}
