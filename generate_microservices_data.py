import json
import random

def generate_microservice_data(count=100):
    services = []
    criticalities = ['Low', 'Medium', 'High', 'Critical']
    all_service_names = [f'service_{i:03d}' for i in range(1, count + 1)]
    
    for i in range(1, count + 1):
        service_name = f'service_{i:03d}'
        
        # Determine criticality
        criticality = random.choice(criticalities)
        
        # Generate dependencies (0 to 3 dependencies)
        num_dependencies = random.randint(0, 3)
        dependencies = []
        potential_dependencies = list(all_service_names)
        potential_dependencies.remove(service_name) # A service cannot depend on itself
        
        # Add some external dependencies as well
        external_deps = [
            'external_auth_api',
            'payment_gateway_api',
            'notification_service_ext',
            'data_warehouse',
            'cdn_provider'
        ]
        potential_dependencies.extend(external_deps)

        # Select unique dependencies
        if potential_dependencies:
            # Ensure we don't pick more dependencies than available potential_dependencies
            actual_num_deps = min(num_dependencies, len(potential_dependencies))
            dependencies = random.sample(potential_dependencies, actual_num_deps)

        # Determine complexity score
        complexity_score = random.randint(1, 5)
        
        services.append({
            'name': service_name,
            'criticality': criticality,
            'dependencies': dependencies,
            'complexity_score': complexity_score
        })
    
    return services

if __name__ == '__main__':
    data = generate_microservice_data(100)
    print(json.dumps(data, indent=2))
