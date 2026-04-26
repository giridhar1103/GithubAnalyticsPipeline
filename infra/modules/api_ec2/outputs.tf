output "public_dns" {
  value = aws_instance.api.public_dns
}

output "instance_id" {
  value = aws_instance.api.id
}
