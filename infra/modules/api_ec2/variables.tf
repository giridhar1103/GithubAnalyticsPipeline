variable "project_name" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "api_image" {
  type = string
}

variable "dashboard_bucket" {
  type = string
}

variable "instance_profile" {
  type = string
}

variable "allowed_cidr_blocks" {
  type = list(string)
}
