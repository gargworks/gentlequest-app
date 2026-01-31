import json
import random

def generate_microservice_data(count=100):
    services = []

    languages = ['Python', 'Node.js', 'Java', 'Go', 'Ruby', 'PHP', 'C#', 'Rust']
    
    language_frameworks = {
        'Python': ['Flask', 'Django', 'FastAPI'],
        'Node.js': ['Express', 'NestJS', 'Koa'],
        'Java': ['Spring Boot', 'Quarkus', 'Micronaut'],
        'Go': ['Gin', 'Echo', 'Fiber'],
        'Ruby': ['Rails', 'Sinatra'],
        'PHP': ['Laravel', 'Symfony', 'CodeIgniter'],
        'C#': ['.NET', 'ASP.NET Core'],
        'Rust': ['Actix-web', 'Rocket']
    }

    all_dependencies = [
        'requests', 'numpy', 'pandas', 'boto3', 'celery', # Python-ish
        'axios', 'lodash', 'moment', 'express-validator', 'mongoose', # Node.js-ish
        'spring-web', 'hibernate', 'jackson', 'guava', # Java-ish
        'zap', 'gorm', 'gorilla/mux', # Go-ish
        'activerecord', 'devise', 'puma', # Ruby-ish
        'guzzle', 'doctrine', 'monolog', # PHP-ish
        'Newtonsoft.Json', 'Serilog', # C#-ish
        'tokio', 'serde', 'reqwest', # Rust-ish
        'uuid', 'log4j', 'jest', 'pytest', 'junit' # General
    ]

    aws_integrations_options = [
        'S3', 'DynamoDB', 'SQS', 'SNS', 'Lambda', 'RDS', 'ECS', 'EKS',
        'API Gateway', 'Cognito', 'Kinesis', 'CloudWatch', 'Route53',
        'VPC', 'EC2', 'EventBridge', 'AppSync', 'StepFunctions', 'Glue'
    ]

    cpu_options = ['128m', '256m', '512m', '1024m', '2048m', '4096m']
    memory_options = ['256Mi', '512Mi', '1024Mi', '2048Mi', '4096Mi', '8192Mi']

    for i in range(1, count + 1):
        service_id = f"service-{i:03d}"
        language = random.choice(languages)
        
        framework = "Custom"
        if language in language_frameworks:
            framework = random.choice(language_frameworks[language])
        
        num_dependencies = random.randint(1, 6)
        dependencies = random.sample(all_dependencies, min(num_dependencies, len(all_dependencies)))
        
        num_aws_integrations = random.randint(1, 5)
        aws_integrations = random.sample(aws_integrations_options, min(num_aws_integrations, len(aws_integrations_options)))

        resource_consumption = {
            'cpu': random.choice(cpu_options),
            'memory': random.choice(memory_options)
        }

        containerized = random.choice([True] * 7 + [False] * 3) # 70% chance of being containerized

        service = {
            'service_id': service_id,
            'language': language,
            'framework': framework,
            'dependencies': dependencies,
            'aws_integrations': aws_integrations,
            'resource_consumption': resource_consumption,
            'containerized': containerized
        }
        services.append(service)

    return services

mock_data = generate_microservice_data()
print(json.dumps(mock_data, indent=2))
