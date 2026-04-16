resource "aws_lightsail_instance" "this" {
  name              = var.instance_name
  availability_zone = var.availability_zone
  blueprint_id      = var.blueprint_id
  bundle_id         = var.bundle_id
  key_pair_name     = var.key_pair_name
  user_data         = var.user_data

  dynamic "add_on" {
    for_each = var.enable_auto_snapshot ? [1] : []

    content {
      type          = "AutoSnapshot"
      snapshot_time = var.snapshot_time_utc
      status        = "Enabled"
    }
  }

  tags = var.tags
}

resource "aws_lightsail_static_ip" "this" {
  count = var.enable_static_ip ? 1 : 0

  name = "${var.instance_name}-static-ip"
}

resource "aws_lightsail_static_ip_attachment" "this" {
  count = var.enable_static_ip ? 1 : 0

  static_ip_name = aws_lightsail_static_ip.this[0].name
  instance_name  = aws_lightsail_instance.this.name
}

resource "aws_lightsail_instance_public_ports" "this" {
  instance_name = aws_lightsail_instance.this.name

  dynamic "port_info" {
    for_each = var.public_ports

    content {
      protocol  = port_info.value.protocol
      from_port = port_info.value.from_port
      to_port   = port_info.value.to_port
      cidrs     = port_info.value.cidrs
    }
  }
}
