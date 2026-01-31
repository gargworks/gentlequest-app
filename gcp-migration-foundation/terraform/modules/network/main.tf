resource "google_compute_network" "vpc_network" {
  project                 = var.project_id
  name                    = var.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnets" {
  for_each      = var.subnets
  project       = var.project_id
  name          = each.value.subnet_name
  ip_cidr_range = each.value.ip_cidr_range
  region        = each.value.region
  network       = google_compute_network.vpc_network.self_link
}

resource "google_compute_firewall" "allow_internal_ssh" {
  project     = var.project_id
  name        = "${var.network_name}-allow-internal-ssh"
  network     = google_compute_network.vpc_network.name
  description = "Allow internal SSH traffic"
  direction   = "INGRESS"
  source_ranges = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "allow_egress_all" {
  project     = var.project_id
  name        = "${var.network_name}-allow-egress-all"
  network     = google_compute_network.vpc_network.name
  description = "Allow all egress traffic"
  direction   = "EGRESS"

  destination_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }
}
