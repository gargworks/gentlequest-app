import json
import random
import os

def generate_microservice_definition():
    languages = ["Python", "Node.js", "Java", "Go", "C#"]
    frameworks = {
        "Python": ["Flask", "Django", "FastAPI"],
        "Node.js": ["Express", "NestJS", "Serverless Framework"],
        "Java": ["Spring Boot", "Quarkus", "Micronaut"],
        "Go": ["Gin", "Echo", "Gorilla Mux"],
        "C#": [".NET Core", "ASP.NET"]
    }
    aws_services = [
        "Lambda", "API Gateway", "DynamoDB", "S3", "SQS", "SNS", "RDS",
        "EC2", "ECS", "EKS", "Kinesis", "CloudWatch", "CloudTrail",
        "Step Functions", "Cognito", "Fargate", "AppSync", "EventBridge"
    ]
    resource_consumptions = ["Low", "Medium", "High", "Very High"]

    primary_language = random.choice(languages)
    framework = random.choice(frameworks[primary_language])
    num_aws_services = random.randint(1, 5)
    selected_aws_services = random.sample(aws_services, num_aws_services)
    is_stateful = random.choice([True, False])
    resource_consumption = random.choice(resource_consumptions)

    # Generate a unique-ish service name
    service_name_parts = [
        random.choice(["user", "product", "order", "inventory", "payment", "notification", "analytics", "search"]),
        random.choice(["service", "api", "processor", "worker", "gateway", "manager"])
    ]
    service_name = f"{'_'.join(service_name_parts)}_{random.randint(100, 999)}"

    # Dependencies on other services (simulated)
    num_dependencies = random.randint(0, 3)
    dependencies = []
    if num_dependencies > 0:
        # For simplicity, let's just pick random names that look like other services
        possible_dependency_prefixes = ["auth", "data", "log", "billing", "shipping"]
        for _ in range(num_dependencies):
            dependencies.append(f"{random.choice(possible_dependency_prefixes)}_service_{random.randint(100, 999)}")


    return {
        "service_name": service_name,
        "primary_language": primary_language,
        "framework": framework,
        "aws_services_used": selected_aws_services,
        "resource_consumption": resource_consumption,
        "dependencies_on_services": dependencies,
        "is_stateful": is_stateful
    }

def main():
    microservices = [generate_microservice_definition() for _ in range(100)]

    output_dir = "mission_artifacts"
    output_file = os.path.join(output_dir, "aws_microservice_analysis.json")

    os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(microservices, f, indent=4)

    print(f"Generated {len(microservices)} microservice definitions and saved to {output_file}")

if __name__ == "__main__":
    main()
