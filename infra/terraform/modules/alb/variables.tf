variable "name_prefix" {
  type        = string
  description = "Prefix used in resource naming."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the ALB."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for the ALB."
}

variable "container_port" {
  type        = number
  description = "Backend container port used by the target group."
}

variable "health_check_path" {
  type        = string
  description = "Health check path used by the target group."
  default     = "/healthz"
}

variable "internal" {
  type        = bool
  description = "Whether the ALB is internal."
  default     = false
}

variable "certificate_arn" {
  type        = string
  description = "Optional ACM certificate ARN."
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Common tags."
  default     = {}
}
