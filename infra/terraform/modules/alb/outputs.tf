output "arn" {
  description = "ALB ARN."
  value       = aws_lb.this.arn
}

output "dns_name" {
  description = "ALB DNS name."
  value       = aws_lb.this.dns_name
}

output "security_group_id" {
  description = "ALB security group ID."
  value       = aws_security_group.this.id
}

output "target_group_arn" {
  description = "Target group ARN for the backend."
  value       = aws_lb_target_group.backend.arn
}

output "zone_id" {
  description = "ALB hosted zone ID."
  value       = aws_lb.this.zone_id
}
