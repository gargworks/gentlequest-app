import json
from collections import defaultdict

def generate_inventory_report(data):
    report = []
    # Group 1: Programming language and runtime version, Key frameworks
    lang_framework_counts = defaultdict(int)
    aws_service_counts = defaultdict(int)
    
    for service in data:
        lang_framework = service['language_framework']
        lang_framework_counts[lang_framework] += 1
        for aws_service in service['aws_dependencies']:
            aws_service_counts[aws_service] += 1

    report.append("## 1. Programming Language and Framework Distribution")
    report.append("| Language/Framework | Count |")
    report.append("|--------------------|-------|")
    for lf, count in sorted(lang_framework_counts.items()):
        report.append(f"| {lf.ljust(18)} | {str(count).ljust(5)} |")
    report.append("\n")

    report.append("## 2. Integrated AWS Services Distribution")
    report.append("| AWS Service | Count |")
    report.append("|-------------|-------|")
    for aws_s, count in sorted(aws_service_counts.items()):
        report.append(f"| {aws_s.ljust(11)} | {str(count).ljust(5)} |")
    report.append("\n")

    # Group 3: Group by common architectural patterns
    architectural_patterns = defaultdict(list)
    for service in data:
        lang_framework = service['language_framework']
        aws_services = ", ".join(sorted(service['aws_dependencies']))
        pattern_key = f"{lang_framework} with [ {aws_services} ]"
        architectural_patterns[pattern_key].append(service['service_name'])
    
    report.append("## 3. Services Grouped by Architectural Patterns")
    report.append("\n")
    for pattern, services in sorted(architectural_patterns.items()):
        report.append(f"### Pattern: {pattern}")
        report.append(f"  - Services ({len(services)}): {', '.join(sorted(services))}")
        report.append("\n")

    return '\n'.join(report)

if __name__ == '__main__':
    try:
        with open('aws_microservices.json', 'r') as f:
            microservices_data = json.load(f)
        
        report_content = generate_inventory_report(microservices_data)

        with open('analysis/microservices_inventory_report.md', 'w') as f:
            f.write(report_content)
        print("Microservices inventory report generated successfully at analysis/microservices_inventory_report.md")

    except FileNotFoundError:
        print("Error: aws_microservices.json not found. Please ensure it's in the current directory.")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from aws_microservices.json. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
