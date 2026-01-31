import json
import random

def generate_microservices(count=100):
    services = []

    primary_language_frameworks = [
        'Python/Flask',
        'Node.js/Express',
        'Java/Spring Boot',
        'Go/Gin',
        'Ruby/Rails',
        'C#/ASP.NET Core',
        'PHP/Laravel',
        'Rust/Actix-web',
        'Python/Django',
        'Node.js/NestJS'
    ]

    aws_service_dependencies_options = [
        'RDS', 'S3', 'SQS', 'DynamoDB', 'Lambda', 'API Gateway', 'Cognito',
        'Kinesis', 'ECS', 'EKS', 'CloudWatch', 'SNS', 'Sagemaker', 'Redshift',
        'Elasticsearch', 'Step Functions', 'AppSync', 'DocumentDB', 'CloudFront',
        'Route53', 'VPC', 'EC2', 'SSM'
    ]

    inter_service_communication_options = [
        'REST API to Service X',
        'Message Queue consumption from Service Y',
        'Event Bridge events',
        'gRPC to Service Z',
        'Database direct access',
        'S3 event triggers',
        'SNS notifications',
        'GraphQL API',
        'Streaming Data (Kinesis)'
    ]

    containerization_statuses = [
        'Dockerized', 'Not Containerized', 'Fargate Compatible', 'EKS Deployed', 'ECS Deployed', 'Lambda Function'
    ]

    service_name_prefixes = [
        'User', 'Product', 'Order', 'Payment', 'Inventory', 'Auth', 'Notification', 'Analytics', 'Shipping', 'Search',
        'Review', 'Recommendation', 'Catalog', 'Customer', 'Pricing', 'Gateway', 'Logger', 'Metric', 'Config', 'Cache'
    ]
    service_name_suffixes = [
        'Service', 'API', 'Processor', 'Worker', 'Engine', 'Manager', 'Daemon', 'Handler', 'Module', 'System'
    ]

    for i in range(count):
        service_id = f"svc-{i:03d}"
        service_name = f"{random.choice(service_name_prefixes)}{random.choice(service_name_suffixes)}"

        num_dependencies = random.randint(1, 5)
        aws_dependencies = random.sample(aws_service_dependencies_options, num_dependencies)
        if 'Lambda' in aws_dependencies and random.random() < 0.3: # Occasionally add API Gateway if Lambda is present
            if 'API Gateway' not in aws_dependencies:
                aws_dependencies.append('API Gateway')
        if 'RDS' in aws_dependencies and random.random() < 0.2: # Occasionally add EC2 for traditional databases
            if 'EC2' not in aws_dependencies:
                aws_dependencies.append('EC2')

        num_communication_patterns = random.randint(1, 3)
        inter_service_comm = random.sample(inter_service_communication_options, num_communication_patterns)

        cpu_cores = round(random.uniform(0.1, 4.0), 2) # From 0.1 to 4.0 cores
        memory_gb = round(random.uniform(0.25, 16.0), 2) # From 0.25GB to 16GB

        container_status = random.choice(containerization_statuses)
        # A Lambda function is by definition not 'Dockerized' in the traditional sense, or Fargate/EKS/ECS Deployed
        if 'Lambda' in aws_dependencies and 'Lambda Function' not in container_status:
            container_status = 'Lambda Function'
        elif 'Lambda' not in aws_dependencies and container_status == 'Lambda Function':
            container_status = random.choice([s for s in containerization_statuses if s != 'Lambda Function'])

        service = {
            'service_id': service_id,
            'service_name': service_name,
            'primary_language_framework': random.choice(primary_language_frameworks),
            'aws_service_dependencies': sorted(list(set(aws_dependencies))), # Ensure unique and sorted
            'inter_service_communication': sorted(list(set(inter_service_comm))), # Ensure unique and sorted
            'estimated_resource_utilization': {
                'cpu_cores': cpu_cores,
                'memory_gb': memory_gb
            },
            'containerization_status': container_status
        }
        services.append(service)

    return services

if __name__ == '__main__':
    all_services = generate_microservices(100)
    with open('aws_microservices.json', 'w') as f:
        json.dump(all_services, f, indent=2)
    print("Generated aws_microservices.json with 100 services.")
