output "endpoint" {
  description = "RDS endpoint hostname."
  value       = aws_db_instance.this.address
}

output "master_user_secret_arn" {
  description = "ARN of the AWS-managed master user secret."
  value       = try(aws_db_instance.this.master_user_secret[0].secret_arn, null)
}

output "port" {
  description = "Database port."
  value       = aws_db_instance.this.port
}

output "security_group_id" {
  description = "Database security group ID."
  value       = aws_security_group.this.id
}
