variable "name_prefix" {
  type        = string
  description = "Prefix used in resource naming."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones used by the subnets."
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets."
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private app subnets."
}

variable "private_db_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private DB subnets."
}

variable "create_nat_gateway" {
  type        = bool
  description = "Whether to create a NAT gateway for private app egress."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Common tags."
  default     = {}
}
