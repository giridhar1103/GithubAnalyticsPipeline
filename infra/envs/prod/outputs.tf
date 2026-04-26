output "data_lake_bucket" {
  value = module.data_lake.bucket_name
}

output "api_public_dns" {
  value = module.api.public_dns
}

output "load_balancer_dns" {
  value = module.load_balancer.dns_name
}
