variable "instance_name" {
  description = "Lightsail instance name."
  type        = string
}

variable "availability_zone" {
  description = "Lightsail availability zone, for example ap-northeast-1a."
  type        = string
}

variable "blueprint_id" {
  description = "Lightsail blueprint id, for example ubuntu_24_04."
  type        = string
}

variable "bundle_id" {
  description = "Lightsail bundle id sized for early access traffic."
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

variable "enable_static_ip" {
  description = "Whether to allocate and attach a static IP."
  type        = bool
  default     = true
}

variable "enable_auto_snapshot" {
  description = "Whether to enable Lightsail automatic snapshots."
  type        = bool
  default     = true
}

variable "snapshot_time_utc" {
  description = "Automatic snapshot time in UTC."
  type        = string
  default     = "17:00"
}

variable "public_ports" {
  description = "Publicly open Lightsail ports."
  type = list(object({
    protocol  = string
    from_port = number
    to_port   = number
    cidrs     = list(string)
  }))
}

variable "tags" {
  description = "Tags applied to Lightsail resources."
  type        = map(string)
  default     = {}
}
