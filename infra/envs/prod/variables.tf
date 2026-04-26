variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "github-analytics"
}

variable "api_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "api_image" {
  type    = string
  default = "<aws_account_id>.dkr.ecr.<region>.amazonaws.com/github-analytics-api:latest"
}

variable "allowed_cidr_blocks" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}
