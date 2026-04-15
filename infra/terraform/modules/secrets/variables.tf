variable "name_prefix" {
  type        = string
  description = "Prefix used in resource naming."
}

variable "secrets" {
  type = map(object({
    description = optional(string)
    kms_key_id  = optional(string)
  }))
  description = "Application secrets to create in Secrets Manager."
}

variable "tags" {
  type        = map(string)
  description = "Common tags."
  default     = {}
}
