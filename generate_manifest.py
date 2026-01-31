import json
import random

def generate_manifest():
    manifest = []
    
    languages_frameworks = [
        "Python/Flask", "Python/Django", "Node.js/Express", "Node.js/NestJS",
        "Java/Spring Boot", "Go/Gin", "Go/Echo", ".NET Core/ASP.NET",
        "Ruby/Rails", "PHP/Laravel"
    ]
    
    aws_resource_types = [
        "ec2", "lambda", "rds_instances", "s3_buckets", "dynamodb_tables",
        "sqs_queues", "sns_topics", "api_gateway_endpoints", "eks_clusters", "ecs_services"
    ]
    
    containerization_statuses = [
        "Dockerized (ECS Fargate)", "Dockerized (EKS)", "Not Containerized (EC2 instances)",
        "Serverless (Lambda)", "Hybrid (EC2 + Lambda)", "Partially Containerized (Some tasks)"
    ]
    
    internal_dependencies_pool = [
        "auth-service", "user-profile-service", "order-processing-service",
        "notification-service", "payment-service", "catalog-service",
        "inventory-service", "shipping-service", "analytics-service", "logging-service"
    ]
    
    external_dependencies_pool = [
        "Stripe API", "Twilio API", "SendGrid", "Auth0", "AWS Cognito",
        "Google Maps API", "OpenAI API", "Elasticsearch (external)", "DataDog"
    ]

    notes_templates = [
        "Standard CRUD microservice. Well-documented API.",
        "Event-driven architecture, uses SQS/SNS extensively.",
        "Legacy application, requires manual migration steps.",
        "Compute-heavy, often scales vertically on EC2.",
        "Data-intensive, interacts with multiple databases.",
        "Newer service, developed with serverless principles.",
        "Integrates with external third-party APIs.",
        "Backend for a critical frontend application.",
        "Relatively isolated, few direct dependencies.",
        "High-throughput service, uses caching extensively."
    ]

    for i in range(1, 101):
        service_name = f"microservice-{i:03d}"
        
        language_framework = random.choice(languages_frameworks)
        
        aws_footprint = {}
        for resource_type in aws_resource_types:
            if resource_type in ["ec2", "rds_instances", "eks_clusters"]:
                aws_footprint[resource_type] = random.randint(0, 3) # Fewer large resources
            elif resource_type in ["lambda", "ecs_services"]:
                aws_footprint[resource_type] = random.randint(0, 10) # More functions/tasks
            else:
                aws_footprint[resource_type] = random.randint(0, 5) # General resources
        
        containerization_status = random.choice(containerization_statuses)
        
        num_internal_deps = random.randint(0, 3)
        internal_deps = random.sample(internal_dependencies_pool, num_internal_deps)
        
        num_external_deps = random.randint(0, 2)
        external_deps = random.sample(external_dependencies_pool, num_external_deps)
        
        migration_complexity_score = random.randint(1, 5)

        notes = random.choice(notes_templates)
        
        manifest.append({
            "service_name": service_name,
            "language_framework": language_framework,
            "aws_resource_footprint": aws_footprint,
            "containerization_status": containerization_status,
            "dependencies": {
                "internal": internal_deps,
                "external": external_deps
            },
            "migration_complexity_score": migration_complexity_score,
            "notes": notes
        })
        
    return manifest

if __name__ == "__main__":
    generated_manifest = generate_manifest()
    with open("microservices_manifest.json", "w") as f:
        json.dump(generated_manifest, f, indent=2)
    print("Generated microservices_manifest.json with 100 entries.")
