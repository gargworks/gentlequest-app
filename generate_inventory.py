import json
import random
import os

def generate_microservice_inventory():
    inventory = []
    
    service_names = [
        "UserAuthService", "ProductCatalogAPI", "PaymentProcessor", "OrderManagementService",
        "InventoryService", "ShippingService", "NotificationService", "SearchService",
        "RecommendationEngine", "ReviewService", "CustomerProfileService", "ReportingService",
        "AnalyticsService", "LoggingService", "MonitoringService", "ConfigurationService",
        "GatewayService", "ImageProcessingService", "DataIngestionService", "SubscriptionService",
        "AuthzService", "BillingService", "CartService", "CheckoutService", "CouponService",
        "CustomerService", "EventBusService", "FeedbackService", "GeoLocationService", "HealthCheckService",
        "IntegrationService", "KycService", "LicenseService", "MessagingService", "MetadataService",
        "OfferService", "OnboardingService", "PermissionsService", "PolicyService", "PreferenceService",
        "PromotionsService", "QueueService", "RateLimitingService", "ReferralService", "RegistryService",
        "RoutingService", "SchedulingService", "SessionService", "StorageService", "TelemetryService",
        "TenantService", "TokenService", "TransactionService", "TranslationService", "UploadService",
        "ValidationService", "VirtualAssistantService", "WebhookService", "WorkflowService", "ZoneService"
    ]
    
    runtime_languages = ['Node.js', 'Python', 'Go', 'Java', 'Ruby', '.NET']
    
    aws_dependencies_list = [
        'RDS_Postgres', 'RDS_MySQL', 'DynamoDB', 'S3', 'SQS', 'SNS', 'Lambda',
        'API_Gateway', 'Kinesis', 'ECS', 'EC2', 'ElastiCache_Redis', 'OpenSearch',
        'MSK', 'DocumentDB', 'CloudWatch', 'Step_Functions'
    ]
    
    cpu_requirements_list = ['0.5 vCPU', '1 vCPU', '2 vCPU', '4 vCPU']
    memory_requirements_list = ['512Mi', '1Gi', '2Gi', '4Gi', '8Gi']
    
    for i in range(1, 101):
        service_id = f"svc-{i:03d}"
        
        # Ensure unique-ish service names for 100 services
        service_name_base = random.choice(service_names)
        service_name = f"{service_name_base}-{i}" if random.random() < 0.7 else service_name_base # Add suffix for variety
        
        runtime_language = random.choice(runtime_languages)
        
        is_containerized = random.choices([True, False], weights=[0.8, 0.2], k=1)[0] # Mostly true
        
        num_dependencies = random.randint(1, 4)
        aws_dependencies = random.sample(aws_dependencies_list, num_dependencies)
        
        cpu_requirements = random.choice(cpu_requirements_list)
        memory_requirements = random.choice(memory_requirements_list)
        
        migration_complexity = random.randint(1, 5)
        
        inventory.append({
            "service_id": service_id,
            "service_name": service_name,
            "runtime_language": runtime_language,
            "is_containerized": is_containerized,
            "aws_dependencies": aws_dependencies,
            "cpu_requirements": cpu_requirements,
            "memory_requirements": memory_requirements,
            "migration_complexity": migration_complexity
        })
        
    output_dir = "mission_artifacts"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "aws_microservices_inventory.json")
    with open(output_path, "w") as f:
        json.dump(inventory, f, indent=2)
    
    print(f"Generated {len(inventory)} microservices and saved to {output_path}")

if __name__ == "__main__":
    generate_microservice_inventory()
