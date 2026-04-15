variable "repository_name" {
  type        = string
  description = "ECR repository name."
}

variable "image_tag_mutability" {
  type        = string
  description = "ECR image tag mutability."
  default     = "MUTABLE"
}

variable "scan_on_push" {
  type        = bool
  description = "Whether to enable image scanning on push."
  default     = true
}

variable "max_image_count" {
  type        = number
  description = "Number of images retained by the lifecycle policy."
  default     = 20
}

variable "tags" {
  type        = map(string)
  description = "Common tags."
  default     = {}
}
