import boto3
import json
import os
import logging
import time
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCHEMA_FILE = "service_analysis_report_schema.json"
OUTPUT_DIR = "service_analysis_reports"
DISCOVERED_SERVICES_FILE = os.path.join(OUTPUT_DIR, "discovered_services.json")

# Load the schema for reference
try:
    with open(SCHEMA_FILE, 'r') as f:
        report_schema = json.load(f)
except FileNotFoundError:
    logging.error(f"Schema file {SCHEMA_FILE} not found. Please ensure it exists.")
    exit(1)

def get_aws_regions():
    """Fetches all available AWS regions."""
    ec2 = boto3.client('ec2', region_name='us-east-1')
    regions = [region['RegionName'] for region in ec2.describe_regions(AllRegions=True)['Regions'] if region['OptInStatus'] == 'not-opted-in' or region['OptInStatus'] == 'opt-in-not-required']
    return regions

def get_account_id():
    """Gets the AWS account ID."""
    try:
        sts_client = boto3.client('sts')
        return sts_client.get_caller_identity()['Account']
    except Exception as e:
        logging.error(f"Could not get AWS account ID: {e}")
        return "UNKNOWN_ACCOUNT_ID"

def discover_lambda_functions(region):
    """Discovers Lambda functions in a given region."""
    lambda_client = boto3.client('lambda', region_name=region)
    functions = []
    try:
        paginator = lambda_client.get_paginator('list_functions')
        for page in paginator.paginate():
            functions.extend(page['Functions'])
        logging.info(f"Discovered {len(functions)} Lambda functions in {region}.")
    except Exception as e:
        logging.error(f"Error discovering Lambda functions in {region}: {e}")
    return functions

def discover_ecs_services(region):
    """Discovers ECS services in a given region."""
    ecs_client = boto3.client('ecs', region_name=region)
    clusters = []
    all_services = []
    try:
        paginator = ecs_client.get_paginator('list_clusters')
        for page in paginator.paginate():
            clusters.extend(page['clusterArns'])

        for cluster_arn in clusters:
            cluster_name = cluster_arn.split('/')[-1]
            service_arns = []
            paginator = ecs_client.get_paginator('list_services')
            for page in paginator.paginate(cluster=cluster_name):
                service_arns.extend(page['serviceArns'])
            
            if service_arns:
                for i in range(0, len(service_arns), 10):
                    batch = service_arns[i:i+10]
                    response = ecs_client.describe_services(cluster=cluster_name, services=batch)
                    for svc in response['services']:
                        svc['clusterName'] = cluster_name # Add cluster name for context
                        all_services.append(svc)
                logging.info(f"Discovered {len(service_arns)} ECS services in cluster {cluster_name} in {region}.")
    except Exception as e:
        logging.error(f"Error discovering ECS services in {region}: {e}")
    return all_services

def discover_rds_instances(region):
    """Discovers RDS instances in a given region."""
    rds_client = boto3.client('rds', region_name=region)
    instances = []
    try:
        paginator = rds_client.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            instances.extend(page['DBInstances'])
        logging.info(f"Discovered {len(instances)} RDS instances in {region}.")
    except Exception as e:
        logging.error(f"Error discovering RDS instances in {region}: {e}")
    return instances

def discover_dynamodb_tables(region):
    """Discovers DynamoDB tables in a given region."""
    dynamodb_client = boto3.client('dynamodb', region_name=region)
    table_names = []
    tables = []
    try:
        paginator = dynamodb_client.get_paginator('list_tables')
        for page in paginator.paginate():
            table_names.extend(page['TableNames'])
        
        for table_name in table_names:
            try:
                tables.append(dynamodb_client.describe_table(TableName=table_name)['Table'])
            except Exception as e:
                logging.warning(f"Could not describe DynamoDB table {table_name} in {region}: {e}")
        logging.info(f"Discovered {len(tables)} DynamoDB tables in {region}.")
    except Exception as e:
        logging.error(f"Error discovering DynamoDB tables in {region}: {e}")
    return tables

def discover_s3_buckets():
    """Discovers S3 buckets (S3 is global, so only need to call once)."""
    s3_client = boto3.client('s3', region_name='us-east-1')
    buckets = []
    try:
        response = s3_client.list_buckets()
        buckets.extend(response['Buckets'])
        logging.info(f"Discovered {len(buckets)} S3 buckets.")
    except Exception as e:
        logging.error(f"Error discovering S3 buckets: {e}")
    return buckets

def discover_sqs_queues(region):
    """Discovers SQS queues in a given region."""
    sqs_client = boto3.client('sqs', region_name=region)
    queue_urls = []
    queues = []
    try:
        paginator = sqs_client.get_paginator('list_queues')
        for page in paginator.paginate():
            queue_urls.extend(page.get('QueueUrls', []))

        for url in queue_urls:
            try:
                attributes = sqs_client.get_queue_attributes(QueueUrl=url, AttributeNames=['All'])['Attributes']
                queues.append({'QueueUrl': url, 'Attributes': attributes})
            except Exception as e:
                logging.warning(f"Could not get attributes for SQS queue {url} in {region}: {e}")
        logging.info(f"Discovered {len(queues)} SQS queues in {region}.")
    except Exception as e:
        logging.error(f"Error discovering SQS queues in {region}: {e}")
    return queues

def discover_sns_topics(region):
    """Discovers SNS topics in a given region."""
    sns_client = boto3.client('sns', region_name=region)
    topics = []
    try:
        paginator = sns_client.get_paginator('list_topics')
        for page in paginator.paginate():
            topics.extend(page['Topics'])
        logging.info(f"Discovered {len(topics)} SNS topics in {region}.")
    except Exception as e:
        logging.error(f"Error discovering SNS topics in {region}: {e}")
    return topics

def get_cloudwatch_metrics_placeholder(service_type, service_name, region):
    """Generates placeholder CloudWatch metrics based on service type."""
    metrics = {
        "metrics_period": "last 7 days",
        "cpu_utilization": {"average_percent": round(random.uniform(5, 70), 2), "peak_percent": round(random.uniform(70, 95), 2)},
        "memory_utilization": {"average_mb": round(random.uniform(100, 2000), 2), "peak_mb": round(random.uniform(2000, 4000), 2)}
    }

    if service_type == "Lambda":
        metrics["lambda_specific_metrics"] = {
            "invocations_average_per_minute": random.randint(100, 5000),
            "errors_average_per_minute": random.randint(0, 50),
            "duration_average_ms": random.randint(50, 500),
            "throttles_average_per_minute": random.randint(0, 10)
        }
    elif service_type == "DynamoDB Table":
        metrics["dynamodb_specific_metrics"] = {
            "read_capacity_consumed_average": random.randint(10, 1000),
            "write_capacity_consumed_average": random.randint(10, 1000),
            "throttled_read_events_average": random.randint(0, 5),
            "throttled_write_events_average": random.randint(0, 5)
        }
    elif service_type == "RDS Instance":
        metrics["rds_specific_metrics"] = {
            "db_connections_average": random.randint(5, 100),
            "free_storage_space_average_gb": round(random.uniform(10, 500), 2),
            "disk_queue_depth_average": round(random.uniform(0.1, 5.0), 2)
        }
    # Add more service-specific metrics as needed
    return metrics

def get_network_details_from_vpc_info(vpc_id, subnet_ids, security_group_ids):
    """Extracts structured network details."""
    return {
        "vpc_id": vpc_id,
        "subnet_ids": subnet_ids,
        "security_group_ids": security_group_ids,
        "is_publicly_accessible": bool(random.getrandbits(1)) # Placeholder
    }

def get_tags(resource_arn):
    """Fetches tags for a given resource ARN."""
    # This is a generic tag fetching function, but tag APIs vary by service.
    # For simplicity, we'll return a placeholder here or try a generic tag API if available (Resource Groups Tagging API).
    # For real implementation, this would need to be service-specific or use AWS Resource Groups Tagging API.
    return {"Project": "GentleQuest", "Environment": "Prod"}

def analyze_lambda_function(function_arn, region, raw_data, aws_account_id):
    """Extracts detailed information for a Lambda function."""
    config = {
        "environment_variables": raw_data.get('Environment', {}).get('Variables', {}),
        "iam_role_arn": raw_data.get('Role', 'N/A'),
        "tags": raw_data.get('Tags', {}),
        "logging_configuration": {
            "enabled": True, # Assume enabled by default for Lambda
            "log_group_name": f"/aws/lambda/{raw_data['FunctionName']}",
            "log_level": "INFO" # Placeholder
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name=Lambda-{raw_data['FunctionName']}"
    }

    # Network settings for Lambda (VPC configuration)
    vpc_config = raw_data.get('VpcConfig', {})
    if vpc_config and vpc_config.get('VpcId'):
        config['network_settings'] = get_network_details_from_vpc_info(
            vpc_config.get('VpcId'),
            vpc_config.get('SubnetIds', []),
            vpc_config.get('SecurityGroupIds', [])
        )
    else:
        config['network_settings'] = {
            "vpc_id": None, "subnet_ids": [], "security_group_ids": [], "is_publicly_accessible": True
        }

    return {
        "service_name": raw_data['FunctionName'],
        "service_id": function_arn,
        "description": f"AWS Lambda function {raw_data['FunctionName']}",
        "owner_team": "Unknown", # Requires external lookup or tag info
        "aws_region": region,
        "aws_account_id": aws_account_id,
        "service_type": "Lambda",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("Lambda", raw_data['FunctionName'], region),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": [],
            "unique_requirements": [],
            "compliance_requirements": [],
            "data_residency_requirements": "N/A",
            "manual_intervention_needed": False,
            "notes": "Initial assessment: Serverless, generally easy to migrate/replicate."
        }
    }

def analyze_ecs_service(service_arn, region, raw_data, aws_account_id):
    """Extracts detailed information for an ECS service."""
    config = {
        "environment_variables": {}, # Environment variables are usually in Task Definitions
        "iam_role_arn": raw_data.get('roleArn', 'N/A'),
        "tags": raw_data.get('tags', {}), # ECS service tags
        "logging_configuration": {
            "enabled": True, # Placeholder
            "log_group_name": f"/ecs/{raw_data['serviceName']}", # Placeholder
            "log_level": "INFO"
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name=ECS-{raw_data['serviceName']}"
    }

    # Network settings for ECS service (awsvpc networking mode)
    network_config = raw_data.get('networkConfiguration', {}).get('awsvpcConfiguration', {})
    if network_config:
        config['network_settings'] = get_network_details_from_vpc_info(
            None, # VPC ID needs to be inferred from subnets or cluster
            network_config.get('subnets', []),
            network_config.get('securityGroups', [])
        )
    else:
        config['network_settings'] = {"vpc_id": None, "subnet_ids": [], "security_group_ids": [], "is_publicly_accessible": False}

    return {
        "service_name": raw_data['serviceName'],
        "service_id": service_arn,
        "description": f"AWS ECS Service {raw_data['serviceName']} in cluster {raw_data.get('clusterName')}",
        "owner_team": "Unknown",
        "aws_region": region,
        "aws_account_id": aws_account_id,
        "service_type": "ECS Service",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("ECS Service", raw_data['serviceName'], region),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": [],
            "unique_requirements": [],
            "compliance_requirements": [],
            "data_residency_requirements": "N/A",
            "manual_intervention_needed": False,
            "notes": "Initial assessment: Containerized, potentially portable with minimal changes."
        }
    }

def analyze_rds_instance(instance_arn, region, raw_data, aws_account_id):
    """Extracts detailed information for an RDS instance."""
    config = {
        "environment_variables": {},
        "iam_role_arn": raw_data.get('AssociatedRoles', [{}])[0].get('RoleArn', 'N/A') if raw_data.get('AssociatedRoles') else 'N/A',
        "tags": {tag['Key']: tag['Value'] for tag in raw_data.get('TagList', [])},
        "logging_configuration": {
            "enabled": True,
            "log_group_name": f"/aws/rds/instance/{raw_data['DBInstanceIdentifier']}",
            "log_level": "INFO" # Placeholder
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name=RDS-{raw_data['DBInstanceIdentifier']}"
    }

    # Network settings for RDS
    vpc_security_groups = raw_data.get('VpcSecurityGroups', [])
    subnet_group = raw_data.get('DBSubnetGroup', {})
    config['network_settings'] = {
        "vpc_id": raw_data.get('DbiResourceId', '').split(':')[-1].split('/')[0] if 'DbiResourceId' in raw_data else None, # Infer VPC ID
        "subnet_ids": [sg['SubnetIdentifier'] for sg in subnet_group.get('Subnets', [])],
        "security_group_ids": [sg['VpcSecurityGroupId'] for sg in vpc_security_groups],
        "is_publicly_accessible": raw_data.get('PubliclyAccessible', False)
    }

    return {
        "service_name": raw_data['DBInstanceIdentifier'],
        "service_id": instance_arn,
        "description": f"AWS RDS Instance ({raw_data['Engine']}) {raw_data['DBInstanceIdentifier']}",
        "owner_team": "Unknown",
        "aws_region": region,
        "aws_account_id": aws_account_id,
        "service_type": "RDS Instance",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("RDS Instance", raw_data['DBInstanceIdentifier'], region),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": ["Database compatibility", "Data migration complexity"] if raw_data['Engine'] not in ['aurora-postgresql', 'aurora-mysql'] else [],
            "unique_requirements": ["High availability", "Specific database version"] if raw_data.get('MultiAZ') else [],
            "compliance_requirements": [],
            "data_residency_requirements": "Required in region",
            "manual_intervention_needed": True,
            "notes": f"Initial assessment: Database migration can be complex, especially for {raw_data['Engine']}.
                       Multi-AZ: {raw_data.get('MultiAZ')}. Encryption: {raw_data.get('StorageEncrypted')}."
        }
    }

def analyze_dynamodb_table(table_arn, region, raw_data, aws_account_id):
    """Extracts detailed information for a DynamoDB table."""
    config = {
        "environment_variables": {},
        "iam_role_arn": "N/A", # DynamoDB tables don't directly have an IAM role like compute services
        "tags": {tag['Key']: tag['Value'] for tag in raw_data.get('Tags', [])},
        "logging_configuration": {
            "enabled": True, # Via CloudWatch Logs for DynamoDB Contributor Insights/Streams
            "log_group_name": f"/aws/dynamodb/{raw_data['TableName']}", # Placeholder
            "log_level": "INFO"
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name=DynamoDB-{raw_data['TableName']}"
    }
    # DynamoDB tables are not VPC-attached like EC2/Lambda, so no direct network_settings
    config['network_settings'] = {"vpc_id": None, "subnet_ids": [], "security_group_ids": [], "is_publicly_accessible": False}

    return {
        "service_name": raw_data['TableName'],
        "service_id": table_arn,
        "description": f"AWS DynamoDB Table {raw_data['TableName']}",
        "owner_team": "Unknown",
        "aws_region": region,
        "aws_account_id": aws_account_id,
        "service_type": "DynamoDB Table",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("DynamoDB Table", raw_data['TableName'], region),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": ["NoSQL data model differences", "Global tables replication"] if raw_data.get('Replicas') else [],
            "unique_requirements": ["Low latency access", "High throughput bursts"] if raw_data.get('BillingModeSummary', {}).get('BillingMode') == 'PAY_PER_REQUEST' else [],
            "compliance_requirements": [],
            "data_residency_requirements": "Required in region for local tables",
            "manual_intervention_needed": False,
            "notes": f"Initial assessment: Managed NoSQL service. Migration to other NoSQL DBs might require schema changes."
        }
    }

def analyze_s3_bucket(bucket_name, raw_data, aws_account_id):
    """Extracts detailed information for an S3 bucket."""
    # S3 buckets are global resources, but have a region associated with them for data storage.
    s3_client = boto3.client('s3', region_name='us-east-1') # Need a client to get bucket location
    bucket_location = 'us-east-1' # Default
    try:
        bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint'] or 'us-east-1'
    except Exception as e:
        logging.warning(f"Could not get location for S3 bucket {bucket_name}: {e}")

    config = {
        "environment_variables": {},
        "iam_role_arn": "N/A",
        "tags": {}, # S3 bucket tags require specific API calls
        "logging_configuration": {
            "enabled": bool(random.getrandbits(1)),
            "log_group_name": f"s3-access-logs-{bucket_name}", # Placeholder
            "log_level": "INFO"
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{bucket_location}.console.aws.amazon.com/cloudwatch/home?region={bucket_location}#dashboards:name=S3-{bucket_name}"
    }
    config['network_settings'] = {"vpc_id": None, "subnet_ids": [], "security_group_ids": [], "is_publicly_accessible": True}

    return {
        "service_name": bucket_name,
        "service_id": f"arn:aws:s3:::{bucket_name}",
        "description": f"AWS S3 Bucket {bucket_name}",
        "owner_team": "Unknown",
        "aws_region": bucket_location,
        "aws_account_id": aws_account_id,
        "service_type": "S3 Bucket",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("S3 Bucket", bucket_name, bucket_location),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": ["Large data volume", "Cross-region replication"] if raw_data.get('VersioningConfiguration', {}).get('Status') == 'Enabled' else [],
            "unique_requirements": ["Static website hosting", "Object versioning"] if raw_data.get('WebsiteConfiguration') or raw_data.get('VersioningConfiguration') else [],
            "compliance_requirements": [],
            "data_residency_requirements": f"Data stored in {bucket_location}",
            "manual_intervention_needed": False,
            "notes": "Initial assessment: Highly scalable object storage. Data transfer costs can be a factor for migration."
        }
    }

def analyze_sqs_queue(queue_url, region, raw_data, aws_account_id):
    """Extracts detailed information for an SQS queue."""
    attributes = raw_data['Attributes']
    queue_name = queue_url.split('/')[-1]
    config = {
        "environment_variables": {},
        "iam_role_arn": "N/A", # SQS policies control access, not IAM role directly tied to queue
        "tags": {},
        "logging_configuration": {
            "enabled": bool(random.getrandbits(1)),
            "log_group_name": f"/aws/sqs/{queue_name}", # Placeholder for SQS logging
            "log_level": "INFO"
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name=SQS-{queue_name}"
    }
    config['network_settings'] = {"vpc_id": None, "subnet_ids": [], "security_group_ids": [], "is_publicly_accessible": True if 'QueueArn' in attributes and 'sqs-queue-dlq' not in attributes['QueueArn'] else False}

    return {
        "service_name": queue_name,
        "service_id": attributes.get('QueueArn', 'N/A'),
        "description": f"AWS SQS Queue {queue_name}",
        "owner_team": "Unknown",
        "aws_region": region,
        "aws_account_id": aws_account_id,
        "service_type": "SQS Queue",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("SQS Queue", queue_name, region),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": ["Message format compatibility"] if attributes.get('FifoQueue') == 'true' else [],
            "unique_requirements": ["Strict message ordering"] if attributes.get('FifoQueue') == 'true' else [],
            "compliance_requirements": [],
            "data_residency_requirements": "Required in region",
            "manual_intervention_needed": False,
            "notes": "Initial assessment: Managed message queuing service. Migration mostly involves producer/consumer changes."
        }
    }

def analyze_sns_topic(topic_arn, region, raw_data, aws_account_id):
    """Extracts detailed information for an SNS topic."""
    topic_name = topic_arn.split(':')[-1]
    config = {
        "environment_variables": {},
        "iam_role_arn": "N/A", # SNS policies control access
        "tags": {},
        "logging_configuration": {
            "enabled": bool(random.getrandbits(1)),
            "log_group_name": f"/aws/sns/{topic_name}", # Placeholder for SNS logging
            "log_level": "INFO"
        },
        "alarms_enabled": bool(random.getrandbits(1)),
        "monitoring_dashboard_url": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name=SNS-{topic_name}"
    }
    config['network_settings'] = {"vpc_id": None, "subnet_ids": [], "security_group_ids": [], "is_publicly_accessible": True}

    return {
        "service_name": topic_name,
        "service_id": topic_arn,
        "description": f"AWS SNS Topic {topic_name}",
        "owner_team": "Unknown",
        "aws_region": region,
        "aws_account_id": aws_account_id,
        "service_type": "SNS Topic",
        "inbound_dependencies": [], # Placeholder
        "outbound_dependencies": [], # Placeholder
        "resource_utilization": get_cloudwatch_metrics_placeholder("SNS Topic", topic_name, region),
        "configuration": config,
        "migration_analysis": {
            "potential_blockers": [],
            "unique_requirements": ["Fanout messaging"] if raw_data.get('SubscriptionsPending') else [],
            "compliance_requirements": [],
            "data_residency_requirements": "Required in region",
            "manual_intervention_needed": False,
            "notes": "Initial assessment: Managed pub/sub service. Migration involves updating publishers and subscribers."
        }
    }

def perform_detailed_analysis(discovered_services_list, aws_account_id):
    """Performs detailed analysis for each discovered service and generates reports."""
    reports = []
    total_services = len(discovered_services_list)
    logging.info(f"Starting detailed analysis for {total_services} discovered services.")

    for i, service_data in enumerate(discovered_services_list):
        service_type = service_data['service_type']
        service_name = service_data['service_name']
        service_id = service_data['service_id']
        region = service_data['aws_region']
        raw_data = service_data['raw_data']

        logging.info(f"({i+1}/{total_services}) Analyzing {service_type}: {service_name} in {region}")

        report = None
        try:
            if service_type == "Lambda":
                report = analyze_lambda_function(service_id, region, raw_data, aws_account_id)
            elif service_type == "ECS Service":
                report = analyze_ecs_service(service_id, region, raw_data, aws_account_id)
            elif service_type == "RDS Instance":
                report = analyze_rds_instance(service_id, region, raw_data, aws_account_id)
            elif service_type == "DynamoDB Table":
                report = analyze_dynamodb_table(service_id, region, raw_data, aws_account_id)
            elif service_type == "S3 Bucket":
                report = analyze_s3_bucket(service_name, raw_data, aws_account_id)
            elif service_type == "SQS Queue":
                report = analyze_sqs_queue(service_id, region, raw_data, aws_account_id)
            elif service_type == "SNS Topic":
                report = analyze_sns_topic(service_id, region, raw_data, aws_account_id)
            else:
                logging.warning(f"Unsupported service type for detailed analysis: {service_type}. Skipping {service_name}.")
                continue
            
            reports.append(report)

            # Save individual report
            report_filename = os.path.join(OUTPUT_DIR, f"{service_type.replace(' ', '_').lower()}_{service_name.replace('/', '_')}.json")
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2)
            logging.info(f"Generated report for {service_name} at {report_filename}")

        except Exception as e:
            logging.error(f"Error analyzing {service_type} {service_name} in {region}: {e}")

    return reports

def main():
    aws_account_id = get_account_id()
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Phase 1: Service Discovery
    logging.info("Phase 1: Starting service discovery...")
    all_discovered_services = []
    regions = get_aws_regions()
    logging.info(f"Scanning AWS account {aws_account_id} across {len(regions)} regions.")

    # S3 is global, handle once from a default region
    s3_buckets = discover_s3_buckets()
    for bucket in s3_buckets:
        all_discovered_services.append({
            'service_type': 'S3 Bucket',
            'service_name': bucket['Name'],
            'service_id': f"arn:aws:s3:::{bucket['Name']}",
            'aws_region': 'global', 
            'aws_account_id': aws_account_id,
            'raw_data': bucket 
        })

    for region in regions:
        logging.info(f"Starting discovery in region: {region}")

        lambda_functions = discover_lambda_functions(region)
        for func in lambda_functions:
            all_discovered_services.append({
                'service_type': 'Lambda',
                'service_name': func['FunctionName'],
                'service_id': func['FunctionArn'],
                'aws_region': region,
                'aws_account_id': aws_account_id,
                'raw_data': func
            })

        ecs_services = discover_ecs_services(region)
        for service in ecs_services:
            all_discovered_services.append({
                'service_type': 'ECS Service',
                'service_name': service['serviceName'],
                'service_id': service['serviceArn'],
                'aws_region': region,
                'aws_account_id': aws_account_id,
                'raw_data': service
            })
        
        rds_instances = discover_rds_instances(region)
        for instance in rds_instances:
            all_discovered_services.append({
                'service_type': 'RDS Instance',
                'service_name': instance['DBInstanceIdentifier'],
                'service_id': instance['DBInstanceArn'],
                'aws_region': region,
                'aws_account_id': aws_account_id,
                'raw_data': instance
            })

        dynamodb_tables = discover_dynamodb_tables(region)
        for table in dynamodb_tables:
            all_discovered_services.append({
                'service_type': 'DynamoDB Table',
                'service_name': table['TableName'],
                'service_id': table['TableArn'],
                'aws_region': region,
                'aws_account_id': aws_account_id,
                'raw_data': table
            })

        sqs_queues = discover_sqs_queues(region)
        for queue in sqs_queues:
            queue_arn = queue['Attributes'].get('QueueArn')
            if queue_arn:
                all_discovered_services.append({
                    'service_type': 'SQS Queue',
                    'service_name': queue['QueueUrl'].split('/')[-1],
                    'service_id': queue_arn,
                    'aws_region': region,
                    'aws_account_id': aws_account_id,
                    'raw_data': queue
                })
            else:
                logging.warning(f"SQS Queue {queue['QueueUrl']} in {region} missing ARN attribute, skipping.")
        
        sns_topics = discover_sns_topics(region)
        for topic in sns_topics:
            all_discovered_services.append({
                'service_type': 'SNS Topic',
                'service_name': topic['TopicArn'].split(':')[-1],
                'service_id': topic['TopicArn'],
                'aws_region': region,
                'aws_account_id': aws_account_id,
                'raw_data': topic
            })
    
    logging.info(f"Total unique services discovered: {len(all_discovered_services)}")

    # Save the initial discovery results for further processing
    with open(DISCOVERED_SERVICES_FILE, 'w') as f:
        json.dump(all_discovered_services, f, indent=2)
    logging.info(f"Initial service discovery data saved to {DISCOVERED_SERVICES_FILE}")

    # Phase 2: Detailed Analysis and Report Generation
    logging.info("Phase 2: Starting detailed analysis and report generation...")
    final_reports = perform_detailed_analysis(all_discovered_services, aws_account_id)
    logging.info(f"Generated {len(final_reports)} detailed service analysis reports.")

    # Optionally, save all reports into a single summary file
    summary_report_path = os.path.join(OUTPUT_DIR, "summary_service_analysis_reports.json")
    with open(summary_report_path, 'w') as f:
        json.dump(final_reports, f, indent=2)
    logging.info(f"All detailed analysis reports summarized in {summary_report_path}")

if __name__ == "__main__":
    main()
