provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

resource "google_project_service" "cloudrun_api" {
  project = var.gcp_project_id
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_run_service" "default" {
  name     = var.service_name
  location = var.gcp_region
  project  = var.gcp_project_id
  depends_on = [google_project_service.cloudrun_api]

  template {
    spec {
      containers {
        image = "gcr.io/${var.gcp_project_id}/${var.service_name}:${var.image_tag}"
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        ports {
          container_port = 8080
        }
      }
      service_account_name = google_service_account.cloud_run_sa.email
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "allow_unauthenticated" {
  location = google_cloud_run_service.default.location
  project  = google_cloud_run_service.default.project
  service  = google_cloud_run_service.default.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name} Cloud Run"
  project      = var.gcp_project_id
}

resource "google_project_iam_member" "cloud_run_sa_artifact_registry_reader" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_service" "artifact_registry_api" {
  project = var.gcp_project_id
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gcp_region
  repository_id = "${var.service_name}-docker-repo"
  description   = "Docker repository for ${var.service_name} microservice"
  format        = "DOCKER"
  project       = var.gcp_project_id
  depends_on    = [google_project_service.artifact_registry_api]
}
