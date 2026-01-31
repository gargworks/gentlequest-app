# GCP Cloud Run Target Architecture Design

This document outlines the standardized architecture for deploying microservices on Google Cloud Platform using Cloud Run, based on the analysis of existing AWS microservices. The design prioritizes scalability, security, maintainability, and alignment with GCP best practices.

## 1. Common Containerization Strategy

To ensure consistency, efficiency, and security across all microservices, the following containerization strategy will be adopted:

*   **Base Images:**
    *   **Recommendation:** Prioritize `distroless` images (e.g., `gcr.io/distroless/static`) for final production images. These are highly secure as they contain only your application and its runtime dependencies, significantly reducing the attack surface.
    *   For languages requiring a full runtime (e.g., Java, Node.js), use official language-specific `distroless` images or minimal Alpine-based images (`alpine:3.x`) during development and build stages, transitioning to `distroless` for the final deployable artifact.
*   **Container Registry:**
    *   **Artifact Registry:** All container images will be stored in Google Cloud Artifact Registry. This provides a fully managed, universal package manager supporting Docker images, Maven, npm, etc. It offers enhanced security features and is the successor to Container Registry (GCR).
    *   **Repository Structure:** Create dedicated repositories per environment or application domain (e.g., `us-central1-docker.pkg.dev/[PROJECT_ID]/[APPLICATION_NAME]-images`).
*   **Dockerfile Best Practices:**
    *   **Multi-Stage Builds:** Mandate multi-stage Dockerfiles to separate build-time dependencies from runtime dependencies, resulting in smaller, more secure final images.
    *   **`.dockerignore`:** Utilize `.dockerignore` files to exclude unnecessary files (e.g., `.git`, `node_modules` not needed at runtime, temporary files) from the build context.
    *   **Non-Root User:** Run containers as a non-root user whenever possible to mitigate potential security vulnerabilities.
    *   **Health Checks:** Implement `HEALTHCHECK` instructions in Dockerfiles to allow Cloud Run to understand the container's health status, enabling more robust deployments.
    *   **Deterministic Builds:** Ensure builds are deterministic, meaning the same input always produces the same output image.
    *   **Image Tagging:** Use meaningful tags for images, including Git commit SHAs, semantic versions (e.g., `v1.2.3`), and `latest` for the most recent stable build.
*   **Build Process:**
    *   **Cloud Build:** All container images will be built and pushed to Artifact Registry using Google Cloud Build, integrated into a CI/CD pipeline. Cloud Build offers serverless execution and tight integration with other GCP services.
    *   **Automated Scans:** Integrate vulnerability scanning (e.g., Artifact Analysis) into the CI/CD pipeline to scan images for known vulnerabilities before deployment.

## 2. Standard GCP Project Structure

To manage resources effectively, enforce security, and isolate environments, a hierarchical project structure leveraging GCP Organizations and Folders will be used:

*   **Organization:** All GCP resources will reside under a single GCP Organization.
*   **Folders:**
    *   `env-dev`: Contains projects for development environments.
    *   `env-staging`: Contains projects for staging/pre-production environments.
    *   `env-prod`: Contains projects for production environments.
    *   `shared`: Contains projects for shared infrastructure and services that span environments (e.g., networking, logging, billing, security controls).
*   **Projects within Folders (Naming Convention: `[org-id]-[env-prefix]-[service-name]-[purpose-optional]`):
    *   **Application Projects:** Each microservice (or logical grouping of closely related microservices) will typically have its own project per environment.
        *   `[org-id]-dev-[service-a]`
        *   `[org-id]-stg-[service-a]`
        *   `[org-id]-prd-[service-a]`
        *   _Example:_ `gq-dev-users-api`, `gq-prd-product-catalog`
    *   **Shared Infrastructure Projects:**
        *   `[org-id]-shared-network`: Centralized VPC networks, Serverless VPC Access connectors, VPNs/Interconnects.
        *   `[org-id]-shared-logging`: Centralized logging sinks, log buckets.
        *   `[org-id]-shared-monitoring`: Centralized dashboards, alerting policies.
        *   `[org-id]-shared-security`: Centralized security controls, audit logs.
        *   `[org-id]-shared-billing`: Billing account management, budget alerts.

This structure facilitates easier IAM management, quota management, cost tracking, and resource isolation.

## 3. IAM Roles and Permissions for Cloud Run Services

Adhering to the principle of least privilege, IAM roles for Cloud Run services will be meticulously managed:

*   **Runtime Service Account:**
    *   Each Cloud Run service will be configured to run with a dedicated, user-managed Google Service Account (GSA). This GSA is the identity of the running container.
    *   **Permissions:** Grant this GSA *only* the specific IAM roles required to interact with other GCP services (e.g., `roles/secretmanager.secretAccessor` for Secret Manager, `roles/datastore.user` for Firestore, `roles/pubsub.publisher` for Pub/Sub, `roles/logging.logWriter` for logging, `roles/storage.objectViewer` for GCS).
    *   **Naming Convention:** `[service-name]-run-sa@[PROJECT_ID].iam.gserviceaccount.com`
*   **Invoker Role (`roles/run.invoker`):
    *   This role grants permission to invoke a Cloud Run service (i.e., make requests to its URL).
    *   **Usage:** Grant this role to other Cloud Run services' runtime GSAs, Cloud Functions, Google Load Balancers, or authenticated users/service accounts that need to call the service.
    *   For publicly accessible services, the `allUsers` principal is granted `roles/run.invoker`.
*   **Deployment Permissions (CI/CD and Developers):
    *   **CI/CD Service Account:** The service account used by Cloud Build (or other CI/CD tools) for deployment requires:
        *   `roles/run.developer` (to deploy and manage Cloud Run services).
        *   `roles/artifactregistry.writer` (to push container images to Artifact Registry).
        *   `roles/iam.serviceAccountUser` (to impersonate the runtime service account when deploying the Cloud Run service).
        *   `roles/secretmanager.secretVersionManager` (to manage secrets if CI/CD pipeline also handles secret creation/updates).
    *   **Developer Roles:** Developers will be granted project-level roles appropriate to their responsibilities, typically `roles/run.developer` for Cloud Run related tasks and necessary permissions for other services they interact with.
*   **Organization/Folder Level IAM:** Policy constraints and organizational policies will be applied at higher levels to enforce baseline security (e.g., disabling external IPs for GCE, enforcing resource location constraints).

## 4. Networking Strategy (VPC, Serverless VPC Access)

A robust networking strategy is crucial for secure and efficient communication between microservices and other GCP resources:

*   **Shared VPC Network:**
    *   A Shared VPC Host Project (`[org-id]-shared-network`) will host one or more VPC networks.
    *   Application projects (`[org-id]-[env-prefix]-[service-name]`) will be attached as Service Projects to this Shared VPC host project. This allows services in different projects to communicate privately within the same VPC network.
    *   **Benefits:** Centralized network administration, simplified connectivity, consistent firewall rules, and IP address management.
*   **Serverless VPC Access Connector:**
    *   **Purpose:** Cloud Run services, by default, run in a Google-managed infrastructure. To enable private communication with resources within a Shared VPC network (e.g., Cloud SQL instances, Memorystore, Compute Engine VMs, private GKE clusters, or on-premises resources via VPN/Interconnect), a Serverless VPC Access Connector is required.
    *   **Deployment:** Connectors will be deployed within the `[org-id]-shared-network` project (or respective environment-specific network projects within `env-dev`, `env-staging`, `env-prod`) in the region where the Cloud Run services reside.
    *   **Configuration:**
        *   **Egress:** Configure Cloud Run services to route *all* outbound traffic through the Serverless VPC Access Connector. This ensures that all outgoing connections originate from within the VPC, allowing the application of VPC firewall rules, private IP access, and consistent network policies.
        *   **Ingress:**
            *   **Public Services:** For services exposed to the internet, ingress will be set to `Allow all traffic` or, preferably, `Allow internal traffic and Cloud Load Balancing` when using a Global External HTTP(S) Load Balancer.
            *   **Internal Services:** For services only accessed by other internal GCP services (e.g., other Cloud Run services, GKE pods), ingress will be set to `Allow internal traffic`.
*   **Load Balancing (Optional but Recommended for Public Services):
    *   **Global External HTTP(S) Load Balancer:** For public-facing Cloud Run services, deploy a Global External HTTP(S) Load Balancer with Cloud CDN, Managed SSL Certificates, and optional Cloud Armor (WAF) for enhanced security and performance. The load balancer's backend service will target the Cloud Run service via its internal endpoint.
    *   **Internal HTTP(S) Load Balancer:** For internal services requiring advanced traffic management (e.g., path-based routing, header-based routing) within the VPC.

## 5. Template for Environment Variable and Secret Management using Secret Manager

Configuration management will distinguish between non-sensitive environment variables and sensitive secrets:

*   **Non-Sensitive Environment Variables:**
    *   **Usage:** For general application configuration, feature flags, service endpoints (if not sensitive), and environment-specific settings.
    *   **Management:** Defined directly in the Cloud Run service configuration via the `gcloud run deploy` command or `cloudrun.yaml` manifest.
    *   **Best Practice:** Avoid placing any sensitive information in environment variables.
*   **Secret Manager:**
    *   **Centralized Storage:** All sensitive data (e.g., API keys, database credentials, third-party service tokens, cryptographic keys) will be stored in Google Cloud Secret Manager.
    *   **Encryption:** Secrets are encrypted at rest and in transit.
    *   **Versioning:** Secret Manager supports automatic versioning, allowing for easy rollback and managing different versions of a secret.
    *   **Access Control:** Access to individual secrets is controlled via IAM policies. The Cloud Run service's runtime service account will be granted `roles/secretmanager.secretAccessor` on *specific* secrets it needs to access, following the principle of least privilege.
*   **Integration with Cloud Run (Recommended Approach):
    *   **Mounting Secrets as Volumes (Recommended for most cases):** Cloud Run allows mounting Secret Manager secrets directly into the container's filesystem as a read-only volume. This is the most secure and recommended way to access secrets.
        *   **Example `cloudrun.yaml` snippet:**
            ```yaml
            apiVersion: serving.knative.dev/v1
            kind: Service
            metadata:
              name: my-service
            spec:
              template:
                spec:
                  containers:
                  - image: us-central1-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/my-service:latest
                    volumeMounts:
                    - name: my-db-credentials
                      mountPath: /etc/secrets/db
                      readOnly: true
                  volumes:
                  - name: my-db-credentials
                    secret:
                      secretName: my-service-db-credentials
                      items:
                      - key: username
                        path: username
                      - key: password
                        path: password
            ```
            The application can then read `/etc/secrets/db/username` and `/etc/secrets/db/password`.
    *   **Injecting Secrets as Environment Variables (Use with caution):** Secrets can also be injected as environment variables. This is less secure as environment variables can sometimes leak into logs or debugging tools.
        *   **Example `cloudrun.yaml` snippet:**
            ```yaml
            apiVersion: serving.knative.dev/v1
            kind: Service
            metadata:
              name: my-service
            spec:
              template:
                spec:
                  containers:
                  - image: us-central1-docker.pkg.dev/[PROJECT_ID]/[REPO_NAME]/my-service:latest
                    env:
                    - name: DB_PASSWORD
                      valueFrom:
                        secretKeyRef:
                          secret: my-service-db-password
                          version: latest # or a specific version number
            ```
*   **Secret Naming Convention:** `[project-id]-[env-prefix]-[service-name]-[secret-purpose]` (e.g., `gq-dev-users-api-db-password`).
*   **Secret Rotation:** Implement automated secret rotation where supported (e.g., Cloud SQL managed users with Secret Manager integration, custom functions for API keys).

This architecture provides a robust, secure, and scalable foundation for deploying microservices on Google Cloud Run, aligning with the principles of clean design and preventing technical debt.