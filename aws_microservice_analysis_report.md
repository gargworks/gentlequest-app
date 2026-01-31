# AWS Microservice Analysis Report (CODE RED Simulation)

This report details the analysis of 10 representative AWS microservices, critical for planning the GCP migration. The analysis focuses on language, AWS dependencies, containerization, configuration/secret management, and statefulness.

## Analysis Summary

| Service Name        | Language/Framework  | AWS Dependencies                             | Containerization Status      | Config/Secret Management         | Statefulness Analysis         |
|---------------------|---------------------|----------------------------------------------|------------------------------|----------------------------------|-------------------------------|
| `UserService`       | Node.js/Express     | RDS (PostgreSQL), SQS, CloudWatch            | Dockerfile exists (ECR: `user-svc:v1.2`) | Env vars, AWS Secrets Manager    | Stateful (external DB)        |
| `ProductService`    | Python/Flask        | DynamoDB, S3, SNS                            | Dockerfile exists (ECR: `prod-svc:v1.0`) | Env vars, Parameter Store        | Stateful (external DB)        |
| `OrderService`      | Java/Spring Boot    | RDS (MySQL), SQS, ElastiCache (Redis)        | Dockerfile exists (ECR: `order-svc:v2.1`) | Env vars, AWS Secrets Manager    | Stateful (external DB)        |
| `PaymentGateway`    | Go/Gin              | SQS, DynamoDB, Lambda                        | Dockerfile exists (ECR: `payment-gw:v1.5`) | Env vars, Parameter Store        | Stateless                     |
| `NotificationService` | Python/FastAPI      | SES, SQS, DynamoDB                           | Dockerfile exists (ECR: `notif-svc:v1.1`) | Env vars, AWS Secrets Manager    | Stateful (external DB)        |
| `AuthService`       | Node.js/NestJS      | DynamoDB, Cognito, SNS                       | Dockerfile exists (ECR: `auth-svc:v2.0`) | Env vars, AWS Secrets Manager    | Stateful (external DB)        |
| `InventoryService`  | Java/Quarkus        | RDS (PostgreSQL), SQS, S3                    | Dockerfile exists (ECR: `inv-svc:v1.3`) | Env vars, Parameter Store        | Stateful (external DB)        |
| `AnalyticsService`  | Python/Pandas       | S3, Kinesis Firehose, Redshift (via Lambda)  | Dockerfile exists (ECR: `analytics-svc:v1.0`) | Env vars                         | Stateless (data processing)   |
| `ReportingService`  | Node.js/Express     | RDS (PostgreSQL), S3, CloudWatch             | Dockerfile exists (ECR: `report-svc:v1.1`) | Env vars, AWS Secrets Manager    | Stateful (external DB)        |
| `GatewayProxy`      | Envoy (custom build) | ALB, Route 53, WAF                           | Dockerfile exists (ECR: `gateway-proxy:v0.9`) | Env vars                         | Stateless                     |