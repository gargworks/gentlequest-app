# Microservice Migration Readiness Analysis Template

This template is designed to guide the analysis of a single microservice to determine its readiness for migration. Each section should be filled out comprehensively to provide a clear picture of the service's current state and potential migration challenges.

---

## 1. Service Overview

*   **Service Name:** [Service Name Here]
*   **Description:** [Brief description of what the service does]
*   **Business Capability:** [What business function does this service enable or support?]
*   **Service Owner/Team:** [Who is responsible for this service?]
*   **Repository URL:** [Link to the source code repository]
*   **Documentation URL(s):** [Links to any existing documentation (e.g., Confluence, README)]

## 2. Codebase Analysis

*   **Primary Language(s):** [e.g., Java, Python, Node.js, Go, C#]
*   **Framework(s):** [e.g., Spring Boot, Express, Django, Flask, .NET Core, Gin]
*   **Runtime Version(s):** [e.g., Java 11, Python 3.9, Node.js 16, Go 1.18]
*   **Build Tool(s):** [e.g., Maven, Gradle, npm, yarn, make, dotnet build]
*   **Testing Framework(s):** [e.g., JUnit, Pytest, Jest, GoConvey]
*   **Code Coverage (if known):** [e.g., 75%]
*   **Last Major Update/Commit:** [Date]
*   **Code Quality/Linters:** [e.g., SonarQube, ESLint, Pylint, SpotBugs]

## 3. Dependency Analysis

### 3.1 Internal Service Dependencies

*   **Services Consumed:**
    *   [Service A]: [Communication Method (e.g., REST, gRPC, Kafka)]
    *   [Service B]: [Communication Method]
    *   ...
*   **Services Providing Data To:**
    *   [Service X]: [Communication Method]
    *   [Service Y]: [Communication Method]
    *   ...

### 3.2 External API Dependencies

*   **External APIs Consumed:**
    *   [API Name]: [Provider, Purpose, Authentication Method]
    *   [API Name]: [Provider, Purpose, Authentication Method]
    *   ...

### 3.3 Library Dependencies

*   **Key Third-Party Libraries:** [List major libraries and their versions, especially those with potential compatibility issues or licensing concerns]
    *   [Library A]: [Version]
    *   [Library B]: [Version]
    *   ...
*   **Deprecated/Vulnerable Libraries:** [Are there any known deprecated or vulnerable libraries that need updating?]

## 4. Data Persistence

*   **Database Type(s):** [e.g., PostgreSQL, MySQL, MongoDB, DynamoDB, Cassandra, Redis]
*   **Database Version(s):** [e.g., PostgreSQL 13.x]
*   **Schema Information:**
    *   **Schema Name(s):** [If applicable]
    *   **Key Tables/Collections:** [List critical tables/collections used by this service]
    *   **ORM/Driver Used:** [e.g., Hibernate, SQLAlchemy, Mongoose, jOOQ]
*   **Connection Methods:** [How does the service connect to the database? (e.g., JDBC, ODBC, native drivers)]
*   **Data Volume/Throughput:** [Estimate data size, typical read/write operations per second if available]
*   **Replication/High Availability:** [Is the database configured for replication or HA?]

## 5. Communication Patterns

*   **Inbound Communication:**
    *   **REST API:** [Base Path, Key Endpoints, Authentication (e.g., OAuth2, API Key)]
    *   **gRPC:** [Key Services/Methods, Authentication]
    *   **Message Queues/Event Streams:** [Queue/Topic names, Message Formats (e.g., JSON, Avro), Consumer Groups]
    *   **Other:** [e.g., WebSockets, File-based]
*   **Outbound Communication:**
    *   **REST API Calls:** [Services/APIs called, Authentication]
    *   **gRPC Calls:** [Services called, Authentication]
    *   **Message Queues/Event Streams:** [Queue/Topic names, Message Formats, Producer]
    *   **Other:**

## 6. Secrets Management

*   **How are secrets currently stored?** [e.g., Environment variables, plaintext in config files, vault solution (e.g., HashiCorp Vault, AWS Secrets Manager), Kubernetes Secrets]
*   **How are secrets accessed by the service?** [e.g., Direct env var access, library calls to vault, mounted files]
*   **Rotation Policy:** [Is there a rotation policy for these secrets? How often?]
*   **Compliance/Security Notes:** [Any specific compliance requirements or security concerns related to secrets?]

## 7. Containerization Feasibility

*   **Existing Dockerfile:** [Yes/No - If yes, provide path and details]
*   **Base Image:** [e.g., `openjdk:11-jre-slim`, `python:3.9-slim`, `alpine`]
*   **Build Process:** [How is the Docker image currently built? (e.g., `docker build`, Jenkins pipeline, GitHub Actions)]
*   **Container Orchestration (if applicable):** [e.g., Kubernetes, Docker Swarm, ECS]
*   **Resource Requirements (estimated):**
    *   **CPU:** [e.g., 0.5 core, 2 cores]
    *   **Memory:** [e.g., 512MB, 4GB]
*   **Port Exposure:** [Which ports does the container expose?]
*   **Volume Mounts:** [Are any persistent volumes required? If so, for what purpose?]
