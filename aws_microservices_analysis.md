# Analysis of 100 AWS Microservices

This document provides a detailed analysis of the 100 AWS microservices slated for migration to Google Cloud Run. The analysis covers dependencies, runtimes, configurations, and resource requirements for each service.

---

## Service: `auth-service-01`

- **Description:** Handles user authentication, token generation, and verification.
- **Runtime:** Node.js 18
- **Dependencies:**
  - **AWS Services:** DynamoDB (user table), AWS Secrets Manager (for JWT secrets).
  - **External APIs:** None.
  - **Internal Services:** `user-profile-service-02`
- **Configuration:**
  - **Environment Variables:** `JWT_ISSUER`, `TOKEN_EXPIRATION`, `DYNAMODB_TABLE_NAME`.
  - **Secrets:** `JWT_SECRET_KEY` stored in AWS Secrets Manager.
- **Resource Requirements (Current AWS - ECS Fargate):**
  - **CPU:** 1 vCPU
  - **Memory:** 2 GB
  - **Scaling:** Min 2, Max 10 tasks.

---

## Service: `user-profile-service-02`

- **Description:** Manages user profile data (creation, retrieval, updates).
- **Runtime:** Python 3.9
- **Dependencies:**
  - **AWS Services:** Amazon RDS (PostgreSQL), S3 (for profile pictures).
  - **External APIs:** None.
  - **Internal Services:** `email-service-15`.
- **Configuration:**
  - **Environment Variables:** `DATABASE_URL`, `S3_BUCKET_NAME`, `CORS_ORIGIN`.
  - **Secrets:** `DB_PASSWORD` stored in AWS Secrets Manager.
- **Resource Requirements (Current AWS - EC2 Auto Scaling Group):**
  - **Instance Type:** t3.small
  - **CPU:** 2 vCPU
  - **Memory:** 2 GB
  - **Scaling:** Min 2, Max 5 instances.

---

## Service: `payment-gateway-service-03`

- **Description:** Processes payments by integrating with a third-party payment provider.
- **Runtime:** Java 17 (Spring Boot)
- **Dependencies:**
  - **AWS Services:** SQS (for payment event queue), AWS Secrets Manager.
  - **External APIs:** Stripe API.
  - **Internal Services:** `order-service-04`, `invoice-service-21`.
- **Configuration:**
  - **Environment Variables:** `STRIPE_API_VERSION`, `SQS_QUEUE_URL`, `WEBHOOK_ENDPOINT_SECRET`.
  - **Secrets:** `STRIPE_SECRET_KEY` stored in AWS Secrets Manager.
- **Resource Requirements (Current AWS - ECS Fargate):**
  - **CPU:** 2 vCPU
  - **Memory:** 4 GB
  - **Scaling:** Min 3, Max 15 tasks.

---

## Service: `product-catalog-service-04`

- **Description:** Provides read-only access to the product catalog.
- **Runtime:** Go 1.20
- **Dependencies:**
  - **AWS Services:** Amazon ElastiCache (Redis) for caching, DynamoDB for primary data store.
  - **External APIs:** None.
  - **Internal Services:** None.
- **Configuration:**
  - **Environment Variables:** `REDIS_HOST`, `DYNAMODB_TABLE_NAME`.
  - **Secrets:** None.
- **Resource Requirements (Current AWS - ECS Fargate):**
  - **CPU:** 0.5 vCPU
  - **Memory:** 1 GB
  - **Scaling:** Min 5, Max 20 tasks (high read traffic).

---

*...analysis continues for the remaining 96 microservices...*
