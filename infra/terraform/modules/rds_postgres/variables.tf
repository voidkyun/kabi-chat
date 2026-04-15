variable "name_prefix" {
  type        = string
  description = "Prefix used in resource naming."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the database."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for the database."
}

variable "allowed_security_group_ids" {
  type        = list(string)
  description = "Security groups allowed to access PostgreSQL."
  default     = []
}

variable "db_name" {
  type        = string
  description = "Database name."
}

variable "master_username" {
  type        = string
  description = "Master username."
}

variable "instance_class" {
  type        = string
  description = "RDS instance class."
}

variable "allocated_storage" {
  type        = number
  description = "Allocated storage in GiB."
}

variable "multi_az" {
  type        = bool
  description = "Whether to enable Multi-AZ."
  default     = false
}

variable "backup_retention_period" {
  type        = number
  description = "Automated backup retention days."
  default     = 7
}

variable "deletion_protection" {
  type        = bool
  description = "Whether to enable deletion protection."
  default     = false
}

variable "skip_final_snapshot" {
  type        = bool
  description = "Whether to skip the final snapshot on destroy."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Common tags."
  default     = {}
}
