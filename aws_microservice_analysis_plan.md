# AWS Microservice Dependency and Configuration Analysis Plan

**Agent:** Developer
**Mission:** Rapidly analyze AWS microservice dependencies and configurations for migration to Google Cloud Run.
**Scope:** 100 microservices from AWS to GCP.
**Time Constraint:** 24-hour CODE RED simulation (implies rapid, high-level assessment initially, focusing on critical paths and common patterns).

## Objective
To identify the key technical characteristics, dependencies (internal, external, data, infrastructure), and configurations of existing AWS microservices to inform the migration strategy to Google Cloud Run. The goal is to identify common patterns, potential blockers, and critical information required for re-platforming.

## Methodology for Rapid Analysis (Simulated)

Given the "CODE RED" and "rapid" constraints, the approach prioritizes automated discovery and pattern identification over deep, individual service dives for all 100 services initially.

1.  **Inventory & Categorization:**
    *   **Action:** Assume access to an inventory of 100 microservice names. If not, generate a representative sample.
    *   **Information to Extract (hypothetical via AWS CLI/SDK scripts/tagging):**
        *   Service Name, Team/Owner
        *   Primary AWS Compute Service (e.g., AWS Lambda, ECS Fargate, EC2, EKS)
        *   Primary Programming Language/Runtime (e.g., Python, Node.js, Java, Go, .NET)
        *   Containerization Status (Dockerized, Serverless function)
        *   Associated AWS Tags (Environment, Project, Service)

2.  **Dependency Mapping Strategy:**

    *   **Data Dependencies:**
        *   **Action:** Identify database connections (RDS instances, DynamoDB tables), caching layers (ElastiCache), message queues (SQS, SNS), and object storage (S3 buckets).
        *   **How (Simulated):**
            *   Review IAM policies attached to compute roles: look for permissions like `rds:*`, `dynamodb:*`, `sqs:*`, `sns:*`, `s3:*`, `elasticache:*`.
            *   Scan for common environment variables (e.g., `DB_HOST`, `REDIS_URL`, `SQS_QUEUE_URL`).
            *   (If code access): Search for AWS SDK calls related to these services.

    *   **Internal Microservice Dependencies:**
        *   **Action:** Determine which microservices communicate with each other.
        *   **How (Simulated):**
            *   Analyze API Gateway configurations/routes.
            *   Examine Load Balancer target groups.
            *   Review service discovery mechanisms (e.g., ECS Service Discovery, Route 53 entries for internal services).
            *   (If code access): Look for internal API calls (e.g., specific internal DNS names, service mesh configurations).

    *   **External Service Dependencies:**
        *   **Action:** Identify calls to external APIs, SaaS products, or on-premise systems.
        *   **How (Simulated):**
            *   (If code access): Search for common external API client libraries or HTTP requests to external domains.
            *   Review environment variables for API keys or external service URLs.

    *   **Infrastructure Dependencies:**
        *   **Action:** Identify VPCs, subnets, security groups, IAM roles, secrets management (Secrets Manager, SSM Parameter Store), load balancers (ALB/NLB), Route 53.
        *   **How (Simulated):**
            *   For each identified compute resource, list associated VPC, subnets, security groups, and IAM role.
            *   Check IAM role policies for access to Secrets Manager/SSM Parameter Store.

3.  **Configuration Analysis Strategy:**

    *   **Environment Variables:**
        *   **Action:** Collect and categorize environment variables used by microservices.
        *   **How (Simulated):**
            *   For Lambda functions: `aws lambda get-function-configuration --function-name <name>`.
            *   For ECS tasks: `aws ecs describe-task-definition --task-definition <name>`.
            *   For EC2 instances: Inspect user data, configuration management tools (Ansible/Chef/Puppet - if used), or assumed SSH access for `env` command (not practical for rapid simulation).
            *   Focus on variables indicating database connections, API keys, service endpoints, logging configurations.

    *   **Build/Deployment Configuration:**
        *   **Action:** Identify how services are built and deployed.
        *   **How (Simulated):**
            *   Look for presence of `Dockerfile`s, `buildspec.yml` (CodeBuild), `serverless.yml` (Serverless Framework).
            *   Identify CI/CD pipelines (CodePipeline, Jenkins).

    *   **Resource-Specific Configurations:**
        *   **Action:** Extract specific configurations relevant to the primary AWS service.
        *   **How (Simulated):**
            *   **Lambda:** Memory, timeout, triggers, layers, VPC config.
            *   **ECS/EKS:** CPU/Memory limits, scaling policies, health checks, networking mode.
            *   **EC2:** Instance type, AMI, auto-scaling groups, attached volumes.

## Simulated Findings & Key Considerations for Cloud Run Migration (Examples based on common patterns)

*   **Common Compute Platforms:** A mix of Lambda (serverless functions), ECS Fargate (containerized microservices), and some legacy EC2 instances.
*   **Database Patterns:** Heavy reliance on AWS RDS (PostgreSQL/MySQL) and DynamoDB. Migration will require Cloud SQL and potentially Firestore or Bigtable.
*   **Messaging:** SQS and SNS are prevalent. Will need mapping to Pub/Sub.
*   **Storage:** S3 for static assets, logs, and data lakes. Direct mapping to Cloud Storage.
*   **Networking:** Services often reside in private VPCs. Cloud Run will require VPC Connector for private network access to Cloud SQL/other GCP services.
*   **IAM Roles:** Extensive use of fine-grained IAM roles for service-to-service communication and AWS resource access. These will need to be translated to GCP IAM service accounts and permissions.
*   **Configuration Management:** Environment variables are common; some use SSM Parameter Store. These need to be migrated to Cloud Run environment variables, Secret Manager, or config maps.
*   **Containerization:** Most ECS/EKS services are already containerized, simplifying the Cloud Run transition. Lambda functions will need to be containerized.
*   **CI/CD:** AWS CodePipeline/CodeBuild is common. Need to plan for Cloud Build or similar GCP-native CI/CD.
*   **Dependencies to watch for:**
    *   **Proprietary AWS services without direct GCP equivalents:** e.g., Kinesis (consider Pub/Sub, Dataflow), Cognito (consider Firebase Auth, Cloud Identity).
    *   **Complex networking/security group rules:** Need careful translation to GCP VPC, firewall rules, and Cloud Run ingress/egress settings.
    *   **Regional dependencies:** Ensure services are not hard-coded to specific AWS regions if multi-region GCP deployment is desired.

## Next Steps (Developer's perspective)

1.  Prioritize services based on dependency complexity and business criticality for phased migration.
2.  Collaborate with Architect to map identified AWS services/patterns to GCP Cloud Run and associated services.
3.  Collaborate with DevOps to identify reusable IaC patterns for common service types and CI/CD pipelines.
4.  Begin drafting Dockerfiles for non-containerized Lambda functions based on identified runtimes.
5.  Create a detailed inventory template for individual microservices based on this analysis plan.
