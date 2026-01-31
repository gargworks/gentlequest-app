import json
import random
from datetime import datetime, timedelta

def generate_mock_report(num_services=100):
    service_name_bases = [
        "auth", "user-profile", "product-catalog", "order-processing",
        "payment-gateway", "notification", "reporting", "inventory",
        "search", "recommendation", "data-ingestion", "analytics",
        "fraud-detection", "logging", "api-gateway", "billing",
        "customer-support", "email", "sms", "realtime-updates",
        "config-management", "workflow", "audit-log", "asset-management",
        "content-delivery", "cache", "event-bus-handler", "background-worker",
        "data-transformation", "ml-inference", "document-storage", "metadata",
        "geo-location", "scheduling", "monitoring", "alerting",
        "security-scanning", "compliance-reporting", "data-backup",
        "dr-orchestrator", "network-management", "resource-tagging",
        "cost-optimization", "developer-portal", "health-check"
    ]

    languages = {
        "Node.js": ["16.x", "18.x", "20.x"],
        "Python": ["3.8", "3.9", "3.10", "3.11"],
        "Java": ["11", "17", "21"],
        "Go": ["1.19", "1.20", "1.21"],
        "Ruby": ["2.7", "3.0", "3.1"],
        ".NET": ["6.0", "7.0", "8.0"]
    }
    frameworks = {
        "Node.js": ["Express", "NestJS", "Hapi", "Koa"],
        "Python": ["FastAPI", "Django", "Flask", "Sanic"],
        "Java": ["Spring Boot", "Quarkus", "Micronaut"],
        "Go": ["Gin", "Echo", "Fiber"],
        "Ruby": ["Rails", "Sinatra"],
        ".NET": ["ASP.NET Core"]
    }

    aws_compute = ["Lambda", "EC2", "ECS (Fargate)", "EKS", "App Runner"]
    aws_storage = ["DynamoDB", "S3", "RDS (PostgreSQL)", "RDS (MySQL)", "ElastiCache (Redis)", "DocumentDB", "Aurora PostgreSQL", "Aurora MySQL"]
    aws_messaging = ["SQS", "SNS", "Kinesis Data Streams", "Amazon MQ"]
    aws_other_resources = [
        "API Gateway", "CloudWatch", "IAM", "CloudFormation", "EventBridge",
        "Secrets Manager", "Parameter Store", "VPC", "Route 53", "ALB",
        "Cognito", "Glue", "Step Functions", "AppSync", "KMS", "WAF", "GuardDuty"
    ]

    sdk_usage_options = [
        "S3", "DynamoDB", "Lambda", "SQS", "SNS", "CloudWatch", "EC2", "Kinesis",
        "SecretsManager", "SSM", "RDS", "Cognito", "StepFunctions", "KMS", "API Gateway"
    ]

    config_secrets_pool = [
        "DB_CONNECTION_STRING", "API_KEY_EXTERNAL_SERVICE", "QUEUE_URL_MESSAGES",
        "S3_BUCKET_NAME_CONFIG", "JWT_SECRET", "AUTH_CLIENT_ID", "WEBHOOK_SECRET",
        "SMTP_PASSWORD", "STRIPE_SECRET_KEY", "TWILIO_AUTH_TOKEN", "REDIS_PASSWORD",
        "ENCRYPTION_KEY", "DATADOG_API_KEY", "NEW_RELIC_LICENSE_KEY", "GITHUB_TOKEN",
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "SLACK_WEBHOOK_URL", "DATADOG_APP_KEY"
    ]

    resource_profiles = [
        {"cpu": "0.125 vCPU", "memory": "128MB RAM"},
        {"cpu": "0.25 vCPU", "memory": "256MB RAM"},
        {"cpu": "0.5 vCPU", "memory": "512MB RAM"},
        {"cpu": "1 vCPU", "memory": "1GB RAM"},
        {"cpu": "2 vCPU", "memory": "2GB RAM"},
        {"cpu": "0.4 vCPU", "memory": "2GB RAM"}, # e.g. Lambda specific profiles
        {"cpu": "0.8 vCPU", "memory": "4GB RAM"}
    ]
    scaling_policies = ["auto_scaling_group", "lambda_provisioned_concurrency", "ecs_service_scaling", "manual", "k8s_hpa"]
    owners = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta", "Team Epsilon"]

    report = []
    service_names_generated = set()

    for i in range(num_services):
        service_id = f"service-{i + 1:03d}-{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))}"
        base_name = random.choice(service_name_bases)
        service_name = f"{base_name}-service-{random.randint(100, 999)}"
        while service_name in service_names_generated:
            service_name = f"{base_name}-service-{random.randint(100, 999)}"
        service_names_generated.add(service_name)

        description = f"Handles {service_name.replace('-', ' ')} related operations."

        # Dependencies
        num_dependent_ms = random.randint(0, 3)
        dependent_microservices = random.sample(list(service_names_generated - {service_name}), min(num_dependent_ms, len(service_names_generated) - 1))
        num_dependent_dbs = random.randint(1, 3)
        dependent_databases = random.sample([db.split('(')[0].strip() for db in aws_storage if 'RDS' in db or 'DynamoDB' in db or 'ElastiCache' in db or 'DocumentDB' in db], min(num_dependent_dbs, len(aws_storage)))
        num_external_apis = random.randint(0, 2)
        external_apis = random.sample([f"ExternalAPI{j}" for j in range(1, 6)], k=num_external_apis)

        # Runtime
        lang = random.choice(list(languages.keys()))
        version = random.choice(languages[lang])
        framework = random.choice(frameworks[lang]) if frameworks[lang] else "N/A"

        # AWS Resources
        compute_resource = random.choice(aws_compute)
        storage_resources = random.sample(aws_storage, k=random.randint(0, 2))
        messaging_resources = random.sample(aws_messaging, k=random.randint(0, 1))
        other_aws_resources = random.sample(aws_other_resources, k=random.randint(1, 3))

        # SDK Usage
        num_sdk_usage = random.randint(1, 4)
        sdk_used = random.sample(sdk_usage_options, k=num_sdk_usage)

        # Configuration Secrets
        num_secrets = random.randint(2, 5)
        secrets = random.sample(config_secrets_pool, k=num_secrets)

        # Resource Requirements
        resource_req = random.choice(resource_profiles)
        scaling_policy = random.choice(scaling_policies)

        owner = random.choice(owners)
        last_updated_date = datetime.now() - timedelta(days=random.randint(0, 365))

        service_entry = {
            "service_id": service_id,
            "service_name": service_name,
            "description": description,
            "dependencies": {
                "microservices": dependent_microservices,
                "databases": dependent_databases,
                "external_apis": external_apis
            },
            "runtime": {
                "language": lang,
                "version": version,
                "framework": framework
            },
            "aws_resources": {
                "compute": compute_resource,
                "storage": storage_resources,
                "messaging": messaging_resources,
                "other": other_aws_resources
            },
            "sdk_usage": sdk_used,
            "configuration_secrets": secrets,
            "resource_requirements": {
                "cpu": resource_req["cpu"],
                "memory": resource_req["memory"],
                "scaling_policy": scaling_policy
            },
            "owner": owner,
            "last_updated": last_updated_date.isoformat(timespec='seconds') + 'Z'
        }
        report.append(service_entry)

    return {"mission_id": "mission-1769274988", "microservices": report}

if __name__ == "__main__":
    mock_data = generate_mock_report(num_services=100)
    with open("aws_microservices_report.json", "w") as f:
        json.dump(mock_data, f, indent=2)
    print("Generated aws_microservices_report.json with 100 microservices.")
