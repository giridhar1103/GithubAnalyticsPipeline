terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "data_lake" {
  source       = "../../modules/data_lake"
  project_name = var.project_name
}

module "iam" {
  source       = "../../modules/iam"
  project_name = var.project_name
  bucket_arn   = module.data_lake.bucket_arn
}

module "glue" {
  source        = "../../modules/glue"
  project_name  = var.project_name
  bucket_name   = module.data_lake.bucket_name
  glue_role_arn = module.iam.glue_role_arn
}

module "api" {
  source              = "../../modules/api_ec2"
  project_name        = var.project_name
  instance_type       = var.api_instance_type
  api_image           = var.api_image
  dashboard_bucket    = module.data_lake.bucket_name
  instance_profile    = module.iam.ec2_instance_profile_name
  allowed_cidr_blocks = var.allowed_cidr_blocks
}

module "load_balancer" {
  source        = "../../modules/alb"
  project_name  = var.project_name
  instance_id   = module.api.instance_id
  instance_port = 80
}

module "monitoring" {
  source       = "../../modules/monitoring"
  project_name = var.project_name
}
