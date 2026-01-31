# Google Cloud Run Architecture: Tier 1 Stateless Microservice Template

This document outlines a high-level, templated architecture for a generic 'Tier 1' stateless microservice deployed on Google Cloud Run. This template is designed for services requiring robust performance, security, and integration with other GCP services.

## 1. Overview

This architecture leverages Google Cloud Run as the primary compute platform for stateless microservices. It emphasizes security best practices, efficient resource utilization, and clear separation of concerns.

## 2. Architecture Components

### 2.1. Container Registry (Artifact Registry)

*   **Purpose:** Securely store and manage Docker images for deployment to Cloud Run.
*   **Details:**
    *   Utilize Google Artifact Registry (preferred over Container Registry for new projects) for private Docker image storage.
    *   Images should be versioned (e.g., semantic versioning, Git SHA).
    *   Access control to the repository should be restricted via IAM roles (e.g., `Artifact Registry Reader` for Cloud Run service account, `Artifact Registry Writer` for CI/CD pipelines).
    *   Enable vulnerability scanning for all stored images.

### 2.2. Cloud Run Service Configuration

*   **Purpose:** Define the compute environment and operational parameters for the microservice.
*   **Details:**
    *   **CPU:** Typically 1-2 vCPUs for Tier 1 services. Adjust based on performance testing and workload analysis. For high-concurrency, short-lived requests, 1 vCPU might suffice; for compute-intensive tasks, 2 vCPUs may be necessary.
    *   **Memory:** 512MB - 2GB. Start with 1GB and optimize based on actual memory consumption. Avoid excessive memory allocation to minimize cost.
    *   **Concurrency:** Set to a reasonable value (e.g., 80-150 requests per container instance). This optimizes resource utilization. Services that block frequently (e.g., waiting for external API calls) might benefit from higher concurrency.
    *   **Min Instances:** Set to 0 for cost optimization during idle periods, or 1 for services requiring minimal cold start latency. For critical Tier 1 services, consider setting `min-instances` to 1 or more during peak hours or permanently if latency is paramount.
    *   **Max Instances:** Set a sensible maximum based on expected load and budget constraints (e.g., 10-100 instances). This prevents uncontrolled scaling.
    *   **Request Timeout:** Configure according to expected service response times (e.g., 30-300 seconds). Ensure this aligns with client-side timeouts.
    *   **Port:** The container must listen on the port specified by the `PORT` environment variable, which Cloud Run injects.
    *   **Environment Variables:** Use for non-sensitive configuration parameters (e.g., logging levels, feature flags).

### 2.3. IAM Service Account Roles

*   **Purpose:** Grant the Cloud Run service the minimal necessary permissions to interact with other GCP services.
*   **Details:**
    *   Each Cloud Run service should have its own dedicated, least-privileged IAM Service Account.
    *   **Essential Roles:**
        *   `Cloud Run Invoker` (on other Cloud Run services, if applicable)
        *   `Secret Manager Secret Accessor` (for accessing secrets)
        *   `Cloud Datastore User`, `BigQuery Data Editor`, `Cloud SQL Client`, etc., as needed for specific data stores.
        *   `Storage Object Viewer` or `Storage Object Creator` for interacting with Cloud Storage buckets.
        *   `Cloud Logging Log Writer` (often included in default service accounts but good to be explicit).
    *   **Avoid:** Granting overly permissive roles like `Editor` or `Owner`.
    *   Rotate service account keys periodically (if using user-managed keys, though GCP-managed keys are preferred).

### 2.4. VPC Connector for Networking

*   **Purpose:** Allow Cloud Run services to connect to resources within a Google Cloud Virtual Private Cloud (VPC) network, such as Cloud SQL, Memorystore, or internal services running on Compute Engine/GKE.
*   **Details:**
    *   Use a Serverless VPC Access Connector.
    *   The connector should be deployed in a subnet within the VPC. This subnet should have enough available IP addresses for the expected scale of the Cloud Run service instances.
    *   **Egress Settings:** Configure Cloud Run service to route *all* outbound traffic through the VPC Connector to enforce network policies and ensure all internal GCP resources are accessed securely. This prevents direct public internet access from the service, unless explicitly configured otherwise.
    *   Ensure appropriate firewall rules are in place within the VPC to allow traffic from the VPC Connector to target resources.

### 2.5. Secret Manager for Secrets

*   **Purpose:** Securely store and manage sensitive configuration data (e.g., API keys, database credentials, encryption keys).
*   **Details:**
    *   Store all sensitive information in Google Secret Manager.
    *   **Access:** Configure the Cloud Run service's IAM Service Account with the `Secret Manager Secret Accessor` role for specific secrets.
    *   Secrets can be injected into the Cloud Run service as environment variables or mounted as files during deployment.
    *   Enable automatic secret versioning and rotation.
    *   Access to Secret Manager should be logged via Cloud Audit Logs.

## 3. Assumptions

*   **Statelessness:** The microservice is designed to be fully stateless; no session data or persistent state is stored within the container instances themselves.
*   **Containerized:** The application is packaged as a Docker container, adhering to best practices (e.g., small base images, multi-stage builds).
*   **GCP Ecosystem:** The architecture assumes integration primarily within the Google Cloud Platform ecosystem.
*   **API-Driven:** The microservice typically exposes an HTTP(S) API.
*   **Observability:** Logging (Cloud Logging), monitoring (Cloud Monitoring), and tracing (Cloud Trace) are assumed to be implemented and integrated.
*   **CI/CD:** A Continuous Integration/Continuous Deployment pipeline is in place to build, test, and deploy container images to Artifact Registry and Cloud Run.
*   **Cost Management:** Basic cost optimization principles are considered (e.g., `min-instances=0`, appropriate CPU/memory).

## 4. Risks

*   **Cold Starts:** While `min-instances` can mitigate, services set to scale down to zero instances will experience cold start latency for the first request after an idle period.
*   **Resource Misconfiguration:** Incorrect CPU/memory/concurrency settings can lead to performance bottlenecks, excessive costs, or service instability.
*   **IAM Over-Privileging:** Granting too many permissions to the service account poses a significant security risk. Least privilege must be strictly enforced.
*   **VPC Connector Bottlenecks:** An undersized or improperly configured VPC Connector can become a bottleneck for outbound traffic, affecting performance and reliability.
*   **Secret Sprawl/Mismanagement:** If secrets are not properly managed in Secret Manager or are leaked through logs/environment variables, it can lead to security breaches.
*   **Vendor Lock-in:** While Cloud Run offers portability, aspects like Secret Manager and Artifact Registry are GCP-specific.
*   **Complexity of Internal Networking:** Managing VPCs, subnets, firewall rules, and VPC Connectors adds networking complexity.
*   **Data Locality/Compliance:** Ensuring data stays within specific regions or meets compliance requirements needs careful consideration beyond this template (e.g., data residency for databases).
*   **Denial of Service (DoS):** While Cloud Run handles some scaling, a service can still be overwhelmed or incur excessive costs if `max-instances` is too high or if not protected by API Gateways (e.g., Cloud Endpoints, Apigee) or rate limiting.