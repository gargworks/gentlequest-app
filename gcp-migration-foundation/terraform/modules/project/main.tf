resource "google_project" "project" {
  project_id = var.project_id
  name       = var.project_name
  org_id     = var.org_id
  billing_account = var.billing_account_id
}

resource "google_project_service" "project_services" {
  for_each = toset(var.project_services)
  project  = google_project.project.project_id
  service  = each.key
  disable_on_destroy = false
}
