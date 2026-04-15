variable "project_name" {
  type        = string
  description = "Project name used in resource naming."
  default     = "kabi-chat"
}

variable "environment" {
  type        = string
  description = "Logical environment name."
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "AWS region for the environment."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones used by the environment."
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets."
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private application subnets."
}

variable "private_db_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private database subnets."
}

variable "backend_image_tag" {
  type        = string
  description = "Image tag deployed to ECS."
  default     = "latest"
}

variable "backend_container_port" {
  type        = number
  description = "Backend container port."
  default     = 8000
}

variable "backend_cpu" {
  type        = number
  description = "Fargate task CPU units."
  default     = 512
}

variable "backend_memory" {
  type        = number
  description = "Fargate task memory in MiB."
  default     = 1024
}

variable "backend_desired_count" {
  type        = number
  description = "Desired task count for the ECS service."
  default     = 1
}

variable "backend_health_check_path" {
  type        = string
  description = "Health check path exposed by the backend."
  default     = "/healthz"
}

variable "acm_certificate_arn" {
  type        = string
  description = "Optional ACM certificate ARN for HTTPS listener."
  default     = null
}

variable "create_nat_gateway" {
  type        = bool
  description = "Whether to create a single NAT gateway for private app subnets."
  default     = true
}

variable "app_environment_variables" {
  type        = map(string)
  description = "Plain environment variables injected into the ECS task."
  default     = {}
}

variable "db_name" {
  type        = string
  description = "PostgreSQL database name."
  default     = "kabi_chat"
}

variable "db_username" {
  type        = string
  description = "PostgreSQL master username."
  default     = "kabi_chat"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class."
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "Initial RDS allocated storage in GiB."
  default     = 20
}

variable "db_multi_az" {
  type        = bool
  description = "Whether to enable Multi-AZ for the database."
  default     = false
}

variable "db_backup_retention_period" {
  type        = number
  description = "Retention days for automated backups."
  default     = 7
}

variable "db_deletion_protection" {
  type        = bool
  description = "Whether to enable deletion protection on the database."
  default     = false
}

variable "db_skip_final_snapshot" {
  type        = bool
  description = "Whether to skip the final snapshot on destroy."
  default     = true
}
