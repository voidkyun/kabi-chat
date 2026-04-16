output "instance_name" {
  description = "Instance name."
  value       = aws_lightsail_instance.this.name
}

output "public_ip_address" {
  description = "Public IP address for the instance."
  value       = try(aws_lightsail_static_ip_attachment.this[0].ip_address, aws_lightsail_instance.this.public_ip_address)
}

output "private_ip_address" {
  description = "Private IP address for the instance."
  value       = aws_lightsail_instance.this.private_ip_address
}

output "username" {
  description = "Default SSH username for the selected blueprint."
  value       = aws_lightsail_instance.this.username
}
