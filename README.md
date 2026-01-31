# CODE RED: AWS to GCP Microservices Migration Simulation

This repository contains the artifacts for a 'CODE RED' simulation to migrate 100 AWS microservices to Google Cloud Run within 24 hours.

## Mission Objectives

- **Analyze** existing AWS microservices.
- **Design** a target GCP Cloud Run architecture.
- **Develop** Infrastructure as Code (IaC).
- **Implement** CI/CD pipelines.
- **Define** migration waves and rollback plans.
- **Perform** post-migration validation.

## Directory Structure

- `/analysis`: Contains the in-depth analysis of the source AWS environment.
- `/infrastructure`: Holds the Terraform and/or Pulumi code for the target GCP environment.
- `/cicd`: CI/CD pipeline definitions (e.g., GitHub Actions, Jenkinsfiles).
- `/migration`: Plans for phased migration waves, cutover, and rollback.
- `/validation`: Scripts and reports for performance testing, monitoring configuration, and post-migration validation.
