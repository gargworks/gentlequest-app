import json
import random
import os

# Configuration
NUM_SERVICES = 100
MISSION_ID = 'mission-1769274839'
OUTPUT_DIR = f'{MISSION_ID}'
OUTPUT_FILE = f'{OUTPUT_DIR}/planning_manifest.json'

LANGUAGES = ['python', 'java', 'nodejs', 'go']
AWS_DEPS = {
    'python': ['s3', 'sqs', 'dynamodb'],
    'java': ['rds', 's3', 'kafka'],
    'nodejs': ['apigateway', 'lambda', 's3'],
    'go': ['ec2', 's3', 'eks']
}
PATTERNS = ['rest-api', 'worker', 'web-frontend', 'data-processor']


def generate_services(count):
    services = []
    for i in range(1, count + 1):
        lang = random.choice(LANGUAGES)
        service = {
            'service_id': f'service-{i:03d}',
            'language': lang,
            'pattern': random.choice(PATTERNS),
            'aws_dependencies': random.sample(AWS_DEPS[lang], k=random.randint(1, len(AWS_DEPS[lang]))),
            'cpu': random.choice([1, 2]),
            'memory_gb': random.choice([1, 2, 4])
        }
        services.append(service)
    return services

def group_services(services):
    groups = {}
    for service in services:
        # Group by language and primary dependency for simplicity
        primary_dep = service['aws_dependencies'][0] if service['aws_dependencies'] else 'none'
        group_key = f"{service['language']}-{service['pattern']}"

        if group_key not in groups:
            groups[group_key] = {
                'migration_strategy': {
                    'type': 'lift-and-shift-containerize',
                    'dockerfile_template': f'template-{service["language"]}.Dockerfile',
                    'terraform_module': 'generic-cloud-run',
                    'notes': f'Standard containerization for {service["language"]} {service["pattern"]} services.'
                },
                'services': []
            }

        # Map AWS deps to potential GCP equivalents
        gcp_equivalents = {
            's3': 'Cloud Storage',
            'sqs': 'Pub/Sub',
            'rds': 'Cloud SQL',
            'dynamodb': 'Firestore/Bigtable',
            'lambda': 'Cloud Functions',
            'kafka': 'Pub/Sub',
            'ec2': 'Compute Engine',
            'eks': 'GKE',
            'apigateway': 'API Gateway/Apigee'
        }
        service['gcp_equivalents'] = {dep: gcp_equivalents.get(dep, 'TBD') for dep in service['aws_dependencies']}

        groups[group_key]['services'].append(service)
    return groups

def main():
    print(f'Simulating service data for {NUM_SERVICES} services...')
    services = generate_services(NUM_SERVICES)
    
    print('Grouping services and defining migration workstreams...')
    workstreams = group_services(services)
    
    manifest = {
        'mission_id': MISSION_ID,
        'simulation': True,
        'total_services': len(services),
        'workstreams': workstreams
    }
    
    # Ensure directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f'Writing planning manifest to {OUTPUT_FILE}...')
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print('Manifest generation complete.')

if __name__ == '__main__':
    main()
