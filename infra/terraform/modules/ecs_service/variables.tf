variable "name_prefix" {
  type        = string
  description = "Prefix used in resource naming."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the ECS service."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for the ECS tasks."
}

variable "alb_security_group_id" {
  type        = string
  description = "Security group ID of the ALB."
}

variable "target_group_arn" {
  type        = string
  description = "Target group ARN used by the ECS service."
}

variable "repository_url" {
  type        = string
  description = "ECR repository URL for the backend image."
}

variable "image_tag" {
  type        = string
  description = "Container image tag."
}

variable "container_port" {
  type        = number
  description = "Backend container port."
}

variable "cpu" {
  type        = number
  description = "Fargate task CPU units."
}

variable "memory" {
  type        = number
  description = "Fargate task memory in MiB."
}

variable "desired_count" {
  type        = number
  description = "Desired service count."
}

variable "environment_variables" {
  type        = map(string)
  description = "Plain environment variables injected into the task."
  default     = {}
}

variable "secret_arns" {
  type        = map(string)
  description = "Map of env var name to Secrets Manager ARN."
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "Common tags."
  default     = {}
}
