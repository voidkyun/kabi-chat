variable "aws_region" {
  description = "AWS region for the dev environment."
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name prefix for Terraform-managed resources."
  type        = string
  default     = "kabi-chat"
}

variable "availability_zone" {
  description = "Lightsail availability zone."
  type        = string
}

variable "blueprint_id" {
  description = "Lightsail blueprint id."
  type        = string
}

variable "bundle_id" {
  description = "Lightsail bundle id."
  type        = string
}

variable "key_pair_name" {
  description = "Existing Lightsail key pair name."
  type        = string
  default     = null
}

variable "user_data" {
  description = "Optional single-line bootstrap script."
  type        = string
  default     = null
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to SSH to the dev instance."
  type        = list(string)
}

variable "http_allowed_cidrs" {
  description = "CIDR blocks allowed to access HTTP on the dev instance."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
