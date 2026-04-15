resource "aws_secretsmanager_secret" "this" {
  for_each = var.secrets

  name                    = "${var.name_prefix}/${each.key}"
  description             = try(each.value.description, null)
  kms_key_id              = try(each.value.kms_key_id, null)
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}"
  })
}
