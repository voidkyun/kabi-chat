output "cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.this.name
}

output "log_group_name" {
  description = "CloudWatch log group name."
  value       = aws_cloudwatch_log_group.this.name
}

output "security_group_id" {
  description = "Security group attached to ECS tasks."
  value       = aws_security_group.this.id
}

output "service_name" {
  description = "ECS service name."
  value       = aws_ecs_service.this.name
}
