variable "project_id" {
  description = "The ID of the GCP project."
  type        = string
}

variable "project_name" {
  description = "The name of the GCP project."
  type        = string
}

variable "org_id" {
  description = "The organization ID where the project will be created."
  type        = string
}

variable "billing_account_id" {
  description = "The ID of the billing account to link to the project."
  type        = string
}

variable "project_services" {
  description = "List of APIs to enable for the project."
  type        = list(string)
  default = [
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "servicenetworking.googleapis.com"
  ]
}
