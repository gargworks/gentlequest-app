# Orphan Agent Output

**Persona:** Strategist
**Intent:** CODE RED: The Developer is compiling the service manifest, but we cannot wait. Your task is to immediately begin designing the migration wave strategy. Create a framework for grouping the 100 microservices into logical migration waves. Your plan should define the criteria for grouping (e.g., by dependency chains, business criticality, technical complexity) and the sequence of these waves. Produce a document outlining this strategy and a template for the wave plan within the next 4 hours. This will allow us to rapidly slot services into waves once the manifest is complete.
**Timestamp:** 1769275135

## Agent Analysis (Not Persisted via Tool)

# Microservice Migration Wave Strategy for Nucleus

**Date:** [Current Date]
**Prepared By:** Strategist Agent
**Objective:** To define a comprehensive framework for grouping 100 microservices into logical migration waves, establishing clear criteria and a sequence to ensure a controlled, efficient, and low-risk transition to the new infrastructure. This strategy aims to accelerate migration planning and execution once the service manifest is complete.

---

## 1. Framework for Grouping Microservices into Migration Waves

The migration of 100 microservices requires a structured, iterative approach to manage complexity, minimize risk, and maintain business continuity. Our framework centers on creating distinct "waves" of migration, each with specific objectives, service groupings, and lessons learned cycles.

### Core Principles:

*   **Risk Minimization:** Prioritize identifying and migrating lower-risk, less critical services first to refine processes and infrastructure before tackling high-stakes components.
*   **Business Value Acceleration:** Group services that unlock immediate business value or enable critical new features on the target platform.
*   **Dependency Management:** Carefully orchestrate the migration order to satisfy inter-service dependencies and prevent outages.
*   **Iterative Learning:** Each wave serves as a learning opportunity, with insights feeding into the planning and execution of subsequent waves.
*   **Scalability & Automation:** Aim to automate migration steps wherever possible, scaling processes as confidence grows.

## 2. Criteria for Grouping Services

Microservices will be grouped based on a combination of technical and business-driven factors:

### 2.1. Dependency Chains (Technical Grouping)

*   **Upstream/Downstream Dependencies:**
    *   **Leaf Services:** Services with no outgoing dependencies are ideal for early waves as they are self-contained.
    *   **Core Upstreams:** Services that many other services depend on (e.g., authentication, core data providers) might be migrated early (if isolated) or later (if complex), but their migration will significantly impact downstream planning.
    *   **Shared Infrastructure/Data Stores:** Group services that heavily rely on a common database, messaging queue, or caching layer to reduce complexity and ensure data consistency during transition.
*   **API Gateway/Integration Layers:** Services exposed via a common API gateway or tightly integrated through specific middleware might be grouped to ensure seamless external interaction post-migration.
*   **Data Migration Needs:** Services requiring significant data migration efforts (e.g., large databases, complex ETL) will be identified and potentially grouped for specialized handling.

### 2.2. Business Criticality (Strategic Grouping - Based on `strategy.md`)

*   **Tier 0 (Mission Critical):** Services directly tied to primary revenue streams, legal compliance, or core customer experience (e.g., order processing, payment gateways). These typically require the highest level of caution and will likely be in later waves after processes are proven.
*   **Tier 1 (High Importance):** Services supporting key business processes with some tolerance for brief degradation or planned downtime (e.g., user profile management, inventory lookup).
*   **Tier 2 (Moderate Importance):** Supporting services, internal tools, or features with less direct customer impact or lower transaction volumes. Good candidates for mid-waves.
*   **Tier 3 (Low Importance/Support):** Internal monitoring, analytics dashboards, non-essential administrative tools. Excellent candidates for early "pathfinder" waves.

### 2.3. Technical Complexity & Risk Profile

*   **Simple/Low Risk:** Services with well-defined boundaries, minimal dependencies, modern architecture, and clear operational runbooks. These are perfect for initial waves.
*   **Moderate Complexity:** Services that might require minor code changes, have a few external integrations, or moderate data migration.
*   **High Complexity/High Risk:** Legacy systems, tightly coupled monoliths broken into microservices, services with unique hardware requirements, extensive data transformation, or high-volume transactional services. These will be scheduled for later waves, benefiting from perfected processes.

## 3. Sequence of Migration Waves

The migration will proceed in distinct waves, building confidence and capability incrementally.

### Wave 0: Pathfinders & Learning (Approx. 5-10 Services)
*   **Criteria:** Tier 3 business criticality, Low technical complexity, minimal dependencies, "low hanging fruit."
*   **Goal:** Validate migration tooling, infrastructure setup, deployment pipelines, monitoring, and rollback procedures. Identify unforeseen challenges and refine the overall migration playbook.
*   **Example Services:** Internal monitoring dashboard, static content delivery, non-critical logging aggregators, feature flags service.

### Wave 1: Foundational Services & Enablers (Approx. 10-15 Services)
*   **Criteria:** Essential shared services, authentication/authorization components, core infrastructure support (e.g., DNS, certificate management services), services critical for subsequent waves. Mix of Tier 2/3.
*   **Goal:** Establish a stable and robust platform foundation upon which critical business applications can be built and migrated.
*   **Example Services:** Centralized identity provider (if self-managed), API gateway components, common notification service, core configuration management.

### Wave 2: Critical, Isolated Business Capabilities (Approx. 15-20 Services)
*   **Criteria:** High business criticality (Tier 1/2) but relatively isolated or with well-understood/managed dependencies. Services that can demonstrate early business value on the new platform.
*   **Goal:** Begin shifting core business functions, showcasing tangible benefits, and further validating the end-to-end migration process for more impactful services.
*   **Example Services:** Read-only product catalog, customer profile retrieval, specific analytics aggregation services, low-volume transactional services.

### Wave 3: Interconnected Business Domains (Approx. 20-30 Services)
*   **Criteria:** Groups of services forming coherent business domains with significant internal dependencies. Focus on migrating entire sub-systems. Mix of Tier 1/2.
*   **Goal:** Migrate substantial functional blocks, allowing for internal optimization and integrated testing within the new environment. Address complex internal data flows.
*   **Example Services:** User management suite (signup, login, profile updates), inventory management, specific modules of order fulfillment.

### Wave 4: High Complexity & Mission-Critical Core (Remaining Services)
*   **Criteria:** Mission-critical (Tier 0), high transaction volume, complex legacy integrations, services requiring extensive data migration, or those with the highest operational risk.
*   **Goal:** Complete the migration of the most challenging and business-critical systems, leveraging the refined processes and learned experience from all previous waves. Requires maximum planning, robust rollback strategies, and contingency.
*   **Example Services:** Core order placement and processing, financial ledger, real-time inventory updates, payment processing backend.

---

## 4. Microservice Migration Wave Plan Template

This template will be used to detail each specific migration wave, ensuring consistent planning and execution across the entire program.

```markdown
# Microservice Migration Wave Plan - [Wave Number]: [Wave Name]

## 1. Wave Overview
*   **Wave Number:** [e.g., Wave 0, Wave 1, Wave 2, etc.]
*   **Wave Name/Theme:** [A descriptive name, e.g., Pathfinder, Core Auth Migration, Product Catalog Shift]
*   **Strategic Alignment (from strategy.md/roadmap.md):** [Briefly explain how this wave contributes to higher-level business goals.]
*   **Target Start Date:** [YYYY-MM-DD]
*   **Target Completion Date:** [YYYY-MM-DD]
*   **Key Objectives for this Wave:**
    *   [Specific, measurable goal 1, e.g., Successfully migrate 5 Tier 3 services.]
    *   [Specific, measurable goal 2, e.g., Validate Kubernetes cluster stability under load.]
    *   [Specific, measurable goal 3, e.g., Reduce latency for Service X by 15% post-migration.]
*   **Success Metrics:**
    *   [Metric 1, e.g., 0 critical incidents post-migration for 2 weeks.]
    *   [Metric 2, e.g., All integrated tests pass with new infrastructure.]
    *   [Metric 3, e.g., Performance benchmarks meet or exceed current baselines.]
*   **Risks & Mitigation:**
    *   [Risk Description 1] -> [Mitigation Strategy 1: Actions, Owner, Deadline]
    *   [Risk Description 2] -> [Mitigation Strategy 2: Actions, Owner, Deadline]
    *   [...]

## 2. Services Included in this Wave
| Service Name      | Business Criticality (T0-T3) | Technical Complexity (Low/Med/High) | Key Dependencies (Upstream/Downstream) | Current Platform | Target Platform | Data Migration Needs? (Y/N/Details) | Notes/Justification for Wave Inclusion |
| :---------------- | :--------------------------- | :---------------------------------- | :----------------------------------- | :--------------- | :-------------- | :---------------------------------- | :------------------------------------- |
| `service-alpha`   | T3                           | Low                                 | `None`                               | Legacy VM        | K8s             | N                                   | Ideal for initial process validation.  |
| `service-beta`    | T2                           | Medium                              | `service-gamma` (downstream)         | On-prem          | AWS ECS         | Y (Small DB)                        | Depends on `service-gamma` stability.  |
| `service-gamma`   | T1                           | High                                | `shared-db-1` (upstream)             | Hybrid           | Azure Functions | Y (Large DB, ETL)                   | Critical component, complex data.      |
| `...`             | `...`                        | `...`                               | `...`                                | `...`            | `...`           | `...`                               | `...`                                  |

## 3. Wave-Specific Migration Strategy & Plan
*   **High-Level Approach:** [e.g., Lift-and-shift, Re-platform (containerize), Re-architect (serverless refactor)]
*   **Tooling & Technologies Utilized:** [e.g., AWS CloudFormation, Kubernetes, Helm, Terraform, Data Migration Service (DMS), custom scripts]
*   **Pre-Migration Checklist:**
    *   [Item 1, e.g., All service manifests reviewed and approved.]
    *   [Item 2, e.g., New infrastructure provisioned and validated.]
    *   [Item 3, e.g., Monitoring and alerting configured for target environment.]
*   **Migration Steps (Detailed Sequence):**
    *   [Step 1: Description, Owner, Estimated Time]
    *   [Step 2: Description, Owner, Estimated Time]
    *   [...]
*   **Rollback Plan (Detailed):**
    *   [Clear, step-by-step instructions to revert to the previous state in case of failure.]
    *   [Defined trigger conditions for rollback.]
    *   [Estimated rollback time.]
*   **Testing Strategy:**
    *   **Unit & Integration Tests:** [Status, coverage goals, tools used]
    *   **Performance & Load Tests:** [Target benchmarks, tools, validation criteria]
    *   **User Acceptance Testing (UAT):** [Stakeholders involved, acceptance criteria, sign-off process]
    *   **Security Testing:** [Penetration testing, vulnerability scans post-migration]
*   **Communication Plan:** [Key stakeholders, communication channels, frequency of updates, incident response protocol.]

## 4. Resource Allocation & Team
*   **Wave Lead:** [Name/Role]
*   **Core Migration Team:** [List individuals/teams, their roles, and responsibilities]
*   **Supporting Teams:** [e.g., QA, DevOps, Security, Product Owners, Business Analysts]
*   **Required Skills/Expertise:** [e.g., Kubernetes, Cloud X, Database Admin]

## 5. Post-Migration Activities & Handover
*   **Monitoring & Alerting Validation:** [Confirm dashboards, alerts, logging are fully functional and integrated.]
*   **Performance Optimization:** [Planned post-migration tuning efforts.]
*   **Service Ownership & Support:** [Define clear ownership for ongoing operations, support contacts.]
*   **Decommissioning Old Services:** [Timeline and plan for gracefully shutting down and removing old instances.]
*   **Lessons Learned:** [Process for capturing insights, successes, failures, and recommendations for future waves.]

## 6. Dependencies for Subsequent Waves
*   **Services successfully migrated in this wave that are critical for future waves:** [List services]
*   **Known blockers or open items for future waves identified during this wave:** [Description of blocker, proposed action]
```
---
This strategy provides a robust framework to guide the migration of Nucleus's microservices, ensuring business goals are met with minimal disruption.

TERMINATE

## Execution History

```
AI: ## Microservice Migration Wave Strategy: Nucleus Platform

**I. Introduction**

The goal of this document is to establish a clear and actionable strategy for migrating 100 microservices to a new infrastructure. Given the urgency ("CODE RED"), this framework aims to enable rapid grouping of services into logical migration waves once the service manifest is complete, ensuring alignment with business objectives, managing risk, and optimizing resource allocation.

**II. Core Principles for Migration**

1.  **Crawl, Walk, Run:** Begin with low-risk, foundational services to validate processes and tooling, then progressively tackle more complex and critical services.
2.  **Dependency First:** Address foundational dependencies (e.g., shared services, core data stores) early to unblock downstream migrations.
3.  **Business Value Driven:** Prioritize services that deliver the highest business value, ensuring critical operations are migrated with minimal disruption.
4.  **Risk Management:** Proactively identify and mitigate technical and operational risks at each stage, incorporating lessons learned from prior waves.
5.  **Iterative Learning:** Each wave serves as a learning opportunity to refine processes, tools, and best practices for subsequent waves.

**III. Grouping Criteria for Microservices**

Microservices will be grouped into waves based on a balanced assessment of three primary criteria:

1.  **Dependency Chains:** Understanding the relationships between services is paramount.
    *   **Upstream/Downstream Analysis:** Services with few or no outbound dependencies (leaf nodes) are strong candidates for earlier waves. Services that are critical dependencies for many others should be migrated either very early (if low complexity) or carefully managed in dedicated waves to provide a stable foundation.
    *   **Shared Dependencies:** Grouping services that rely on a common critical component (e.g., a specific database, a messaging queue, an authentication service) can ensure efficient migration of that shared resource and consistent behavior across dependent services.
    *   **Data Locality/Boundaries:** Services sharing a data store or belonging to a specific data domain may be grouped to facilitate data migration strategies and minimize data consistency challenges.

2.  **Business Criticality:** Assessing the impact of a service on core business operations, revenue, and customer experience.
    *   **Tier 0 (Mission Critical):** Services whose failure directly halts revenue generation, violates regulatory compliance, or severely impacts core customer experience (e.g., payment gateways, user authentication, core product features). These should be prioritized, but their migration must be meticulously planned due to high risk.
    *   **Tier 1 (High Importance):** Services supporting key business functions, important but not immediately catastrophic if unavailable (e.g., advanced analytics, internal CRM tools, non-real-time reporting).
    *   **Tier 2 (Support/Utility):** Services providing supporting functions, internal tools, or less frequently used features with lower direct business impact (e.g., logging services, internal monitoring components, administrative UIs). These are good candidates for early waves to build confidence and validate processes.

3.  **Technical Complexity and Risk:** Evaluating the technical effort, potential challenges, and operational risk associated with migrating a service.
    *   **Complexity Factors:**
        *   **Codebase Maturity:** Age, size, language/framework (e.g., legacy vs. modern).
        *   **External Integrations:** Number and complexity of integrations with other systems (internal/external).
        *   **Operational Footprint:** Resource requirements, scaling patterns, monitoring complexity.
        *   **Testing Coverage:** Quality and completeness of existing test suites.
    *   **Risk Factors:**
        *   **Known Instability/Bugs:** Services with a history of issues.
        *   **Lack of Documentation/Ownership:** "Black box" services.
        *   **High Change Velocity:** Services undergoing frequent updates.
        *   **Security Vulnerabilities:** Services handling sensitive data or exposed to high threat vectors.
    *   **Strategy:** Mix low-complexity "quick wins" with strategically planned high-complexity services. Use early waves to establish patterns for handling common technical challenges.

**IV. Wave Sequencing Strategy**

The migration will follow a phased approach, starting with discovery and foundational elements, then progressing iteratively.

1.  **Wave 0: Discovery & Preparation (Pre-Manifest Completion)**
    *   **Goal:** Establish foundational understanding. While the developer compiles the manifest, strategize on the grouping criteria, define tooling requirements, and develop communication plans. Prepare the team for immediate action post-manifest delivery.
    *   **Output (Post-Manifest):** Comprehensive service inventory with initial criticality, complexity, and dependency scoring; preliminary wave candidates identified.

2.  **Wave 1: Pilot & Foundational Services (Learn & Stabilize)**
    *   **Goal:** Validate the migration process, tooling, and operational procedures with minimal business impact. Establish a stable "landing zone."
    *   **Characteristics:** 3-5 low-complexity, low-dependency, Tier 2/3 utility services (e.g., shared libraries, a simple logging service, a non-critical internal API).
    *   **Learning:** Refine cutover procedures, monitoring, rollback plans, and team coordination.

3.  **Wave 2: Core Dependencies & Enabling Infrastructure**
    *   **Goal:** Migrate critical shared services or data stores that many other microservices depend on. This unblocks subsequent waves.
    *   **Characteristics:** Services identified as key upstream dependencies (e.g., message brokers, core authentication services, central data access layers). May include a few more complex foundational services. Focus on establishing robust data migration and consistency patterns.

4.  **Wave 3-X: Iterative Business Domain / Dependency Clusters**
    *   **Goal:** Systematically migrate services grouped by logical business domains or tightly coupled dependency clusters.
    *   **Strategy:**
        *   **Prioritization:** Within a cluster, prioritize based on business criticality, generally moving from lower to higher criticality (once dependencies are stable).
        *   **Mix & Match:** Each wave might include a blend of low-to-medium complexity services and a carefully selected high-complexity service, ensuring continuous learning and risk distribution.
        *   **Focus:** Maintain a clear business outcome for each wave (e.g., "Complete migration of customer profile management").

5.  **Final Waves: Complex, High-Criticality & Legacy Systems**
    *   **Goal:** Address the most challenging services (e.g., legacy monoliths broken down into microservices, extremely high-traffic Tier 0 services, services with complex compliance requirements) once the team has extensive experience and the new infrastructure is proven stable.
    *   **Strategy:** Dedicated, experienced teams; extensive parallel operation (if possible); advanced testing (performance, security); robust fallback mechanisms.

**V. Wave Plan Template**

```markdown
# Migration Wave Plan: [Wave Number/Name, e.g., Wave 3: User Profile & Authentication Services]

## I. Wave Overview
*   **Wave Number:** [e.g., 3]
*   **Wave Name:** [e.g., User Profile & Authentication Services]
*   **Target Completion Date:** [YYYY-MM-DD]
*   **Primary Goal:** [e.g., Migrate core user management and authentication functionalities, ensuring minimal user impact and enhanced security post-migration.]
*   **Strategic Justification:** [How this wave aligns with overall migration strategy, e.g., "Addresses critical Tier 0/1 services after foundational services (Wave 1 & 2) are stable, enabling secure user interaction on the new platform."]

## II. Services in this Wave
*   **Total Services:** [Number of microservices]
*   **Service List:**
    *   `[Service Name 1: e.g., User-API]` - Criticality: [Tier 0], Complexity: [High], Key Dependencies: [Auth-Service, User-DB, Notification-Service]
    *   `[Service Name 2: e.g., Auth-Service]` - Criticality: [Tier 0], Complexity: [Medium], Key Dependencies: [Identity-Provider, Token-Store]
    *   `[Service Name 3: e.g., Profile-Mgmt-UI-Backend]` - Criticality: [Tier 1], Complexity: [Medium], Key Dependencies: [User-API, Image-CDN]
    *   ... (List all services grouped in this wave with their assessed characteristics)

## III. Grouping Criteria Application for this Wave
*   **Dependency Chain Rationale:** [Explain the inter-dependencies. e.g., "Auth-Service is a core upstream for User-API, and both are foundational for Profile-Mgmt-UI-Backend. Grouping them ensures a cohesive migration of the user identity and management stack."]
*   **Business Criticality Rationale:** [Explain why these services are prioritized now. e.g., "These services underpin all user interactions and secure access, making their stable migration crucial at this stage to enable further feature migrations."]
*   **Technical Complexity Rationale:** [Highlight common technical characteristics or challenges. e.g., "Focus on sensitive data handling, robust security protocols, and integration with external identity providers."]

## IV. Dependencies & Prerequisites
*   **Upstream Wave Dependencies:** [List previous waves that *must* be successfully completed before this wave begins. e.g., "Wave 1 (Shared Logging & Metrics), Wave 2 (Core Database Services)."]
*   **External System Dependencies:** [Any external systems, APIs, or third-party services that must be ready or integrated with the new platform for this wave's services.]
*   **Team/Resource Readiness:** [Specify required teams, specific skillsets, necessary tools, and infrastructure provisioning that must be in place.]

## V. Migration Approach & Milestones
*   **Key Migration Steps:**
    *   [e.g., **Code Preparation:** Refactor service `User-API` for new environment compatibility.]
    *   [e.g., **Infrastructure Provisioning:** Deploy new Kubernetes clusters for `Auth-Service` and `User-API` in Target VPC.]
    *   [e.g., **Data Migration Strategy:** Plan for real-time replication and eventual consistency for `User-DB` data migration.]
    *   [e.g., **Testing Strategy:** Unit, Integration, Performance, Security, and User Acceptance Testing (UAT) for all services in parallel.]
    *   [e.g., **Cutover Plan:** Blue-green deployment strategy for `Auth-Service`, followed by a staged DNS switch for `User-API` over 24 hours.]
    *   [e.g., **Rollback Plan:** Document explicit steps for immediate rollback to previous infrastructure in case of critical failure.]
*   **Major Milestones:**
    *   `[YYYY-MM-DD]` - Code Freeze for Wave 3 Services
    *   `[YYYY-MM-DD]` - Staging Environment Deployment Complete
    *   `[YYYY-MM-DD]` - Performance & Security Testing Complete
    *   `[YYYY-MM-DD]` - Production Cutover Window
    *   `[YYYY-MM-DD]` - Post-Migration Stability Checkpoint

## VI. Risks & Mitigation
*   **Identified Risks:**
    *   [Risk 1: Description, e.g., "Potential for user lockout during `Auth-Service` cutover due to session invalidation."]
    *   [Risk 2: Description, e.g., "Data inconsistencies between old and new `User-DB` during replication window."]
*   **Mitigation Strategies:**
    *   [Mitigation for Risk 1: e.g., "Implement a grace period for old sessions, extensive pre-cutover testing, clear communication to support teams."]
    *   [Mitigation for Risk 2: e.g., "Utilize transactional replication with robust error handling, implement reconciliation scripts, continuous monitoring for data drift."]

## VII. Success Metrics
*   **Key Performance Indicators (KPIs):**
    *   `Auth-Service` Uptime: > 99.99% post-migration.
    *   `User-API` Latency: < 50ms (p95) post-migration.
    *   Zero Critical Incidents within 72 hours post-cutover.
    *   Successful migration of 100% of services within the wave.
*   **Monitoring Strategy:** [Specify tools and dashboards for real-time observation of KPIs (e.g., Grafana, Prometheus, ELK stack). Include alerts setup.]

## VIII. Team & Responsibilities
*   **Wave Lead:** [Name/Role, e.g., Sarah Chen - Senior Engineering Manager]
*   **Core Migration Team:** [Team Alpha (Auth), Team Beta (User Profile), DevOps Team]
*   **Key Stakeholders:** [Product Manager (User Identity), Business Owner (Customer Experience), Security Team Lead]

## IX. Communication Plan
*   **Internal:** Daily stand-ups, weekly status reports to leadership, dedicated Slack channel for real-time updates/issues.
*   **External (if applicable):** Pre-planned customer notifications for potential minor service disruptions (if any), support team training.
```
{
  "tool": "brain_store_memory",
  "args": {
    "content": "# Microservice Migration Wave Strategy: Nucleus Platform\n\n## I. Introduction\nThe goal of this document is to establish a clear and actionable strategy for migrating 100 microservices to a new infrastructure. Given the urgency (\"CODE RED\"), this framework aims to enable rapid grouping of services into logical migration waves once the service manifest is complete, ensuring alignment with business objectives, managing risk, and optimizing resource allocation.\n\n## II. Core Principles for Migration\n1.  **Crawl, Walk, Run:** Begin with low-risk, foundational services to validate processes and tooling, then progressively tackle more complex and critical services.\n2.  **Dependency First:** Address foundational dependencies (e.g., shared services, core data stores) early to unblock downstream migrations.\n3.  **Business Value Driven:** Prioritize services that deliver the highest business value, ensuring critical operations are migrated with minimal disruption.\n4.  **Risk Management:** Proactively identify and mitigate technical and operational risks at each stage, incorporating lessons learned from prior waves.\n5.  **Iterative Learning:** Each wave serves as a learning opportunity to refine processes, tools, and best practices for subsequent waves.\n\n## III. Grouping Criteria for Microservices\nMicroservices will be grouped into waves based on a balanced assessment of three primary criteria:\n\n1.  **Dependency Chains:** Understanding the relationships between services is paramount.\n    *   **Upstream/Downstream Analysis:** Services with few or no outbound dependencies (leaf nodes) are strong candidates for earlier waves. Services that are critical dependencies for many others should be migrated either very early (if low complexity) or carefully managed in dedicated waves to provide a stable foundation.\n    *   **Shared Dependencies:** Grouping services that rely on a common critical component (e.g., a specific database, a messaging queue, an authentication service) can ensure efficient migration of that shared resource and consistent behavior across dependent services.\n    *   **Data Locality/Boundaries:** Services sharing a data store or belonging to a specific data domain may be grouped to facilitate data migration strategies and minimize data consistency challenges.\n\n2.  **Business Criticality:** Assessing the impact of a service on core business operations, revenue, and customer experience.\n    *   **Tier 0 (Mission Critical):** Services whose failure directly halts revenue generation, violates regulatory compliance, or severely impacts core customer experience (e.g., payment gateways, user authentication, core product features). These should be prioritized, but their migration must be meticulously planned due to high risk.\n    *   **Tier 1 (High Importance):** Services supporting key business functions, important but not immediately catastrophic if unavailable (e.g., advanced analytics, internal CRM tools, non-real-time reporting).\n    *   **Tier 2 (Support/Utility):** Services providing supporting functions, internal tools, or less frequently used features with lower direct business impact (e.g., logging services, internal monitoring components, administrative UIs). These are good candidates for early waves to build confidence and validate processes.\n\n3.  **Technical Complexity and Risk:** Evaluating the technical effort, potential challenges, and operational risk associated with migrating a service.\n    *   **Complexity Factors:**\n        *   **Codebase Maturity:** Age, size, language/framework (e.g., legacy vs. modern).\n        *   **External Integrations:** Number and complexity of integrations with other systems (internal/external).\n        *   **Operational Footprint:** Resource requirements, scaling patterns, monitoring complexity.\n        *   **Testing Coverage:** Quality and completeness of existing test suites.\n    *   **Risk Factors:**\n        *   **Known Instability/Bugs:** Services with a history of issues.\n        *   **Lack of Documentation/Ownership:** \"Black box\" services.\n        *   **High Change Velocity:** Services undergoing frequent updates.\n        *   **Security Vulnerabilities:** Services handling sensitive data or exposed to high threat vectors.\n    *   **Strategy:** Mix low-complexity \"quick wins\" with strategically planned high-complexity services. Use early waves to establish patterns for handling common technical challenges.\n\n## IV. Wave Sequencing Strategy\nThe migration will follow a phased approach, starting with discovery and foundational elements, then progressing iteratively.\n\n1.  **Wave 0: Discovery & Preparation (Pre-Manifest Completion)**\n    *   **Goal:** Establish foundational understanding. While the developer compiles the manifest, strategize on the grouping criteria, define tooling requirements, and develop communication plans. Prepare the team for immediate action post-manifest delivery.\n    *   **Output (Post-Manifest):** Comprehensive service inventory with initial criticality, complexity, and dependency scoring; preliminary wave candidates identified.\n\n2.  **Wave 1: Pilot & Foundational Services (Learn & Stabilize)**\n    *   **Goal:** Validate the migration process, tooling, and operational procedures with minimal business impact. Establish a stable \"landing zone.\"\n    *   **Characteristics:** 3-5 low-complexity, low-dependency, Tier 2/3 utility services (e.g., shared libraries, a simple logging service, a non-critical internal API).\n    *   **Learning:** Refine cutover procedures, monitoring, rollback plans, and team coordination.\n\n3.  **Wave 2: Core Dependencies & Enabling Infrastructure**\n    *   **Goal:** Migrate critical shared services or data stores that many other microservices depend on. This unblocks subsequent waves.\n    *   **Characteristics:** Services identified as key upstream dependencies (e.g., message brokers, core authentication services, central data access layers). May include a few more complex foundational services. Focus on establishing robust data migration and consistency patterns.\n\n4.  **Wave 3-X: Iterative Business Domain / Dependency Clusters**\n    *   **Goal:** Systematically migrate services grouped by logical business domains or tightly coupled dependency clusters.\n    *   **Strategy:**\n        *   **Prioritization:** Within a cluster, prioritize based on business criticality, generally moving from lower to higher criticality (once dependencies are stable).\n        *   **Mix & Match:** Each wave might include a blend of low-to-medium complexity services and a carefully selected high-complexity service, ensuring continuous learning and risk distribution.\n        *   **Focus:** Maintain a clear business outcome for each wave (e.g., \"Complete migration of customer profile management\").\n\n5.  **Final Waves: Complex, High-Criticality & Legacy Systems**\n    *   **Goal:** Address the most challenging services (e.g., legacy monoliths broken down into microservices, extremely high-traffic Tier 0 services, services with complex compliance requirements) once the team has extensive experience and the new infrastructure is proven stable.\n    *   **Strategy:** Dedicated, experienced teams; extensive parallel operation (if possible); advanced testing (performance, security); robust fallback mechanisms.\n\n## V. Wave Plan Template\n\n```markdown\n# Migration Wave Plan: [Wave Number/Name, e.g., Wave 3: User Profile & Authentication Services]\n\n## I. Wave Overview\n*   **Wave Number:** [e.g., 3]\n*   **Wave Name:** [e.g., User Profile & Authentication Services]\n*   **Target Completion Date:** [YYYY-MM-DD]\n*   **Primary Goal:** [e.g., Migrate core user management and authentication functionalities, ensuring minimal user impact and enhanced security post-migration.]\n*   **Strategic Justification:** [How this wave aligns with overall migration strategy, e.g., \"Addresses critical Tier 0/1 services after foundational services (Wave 1 & 2) are stable, enabling secure user interaction on the new platform.\"]\n\n## II. Services in this Wave\n*   **Total Services:** [Number of microservices]\n*   **Service List:**\n    *   `[Service Name 1: e.g., User-API]` - Criticality: [Tier 0], Complexity: [High], Key Dependencies: [Auth-Service, User-DB, Notification-Service]\n    *   `[Service Name 2: e.g., Auth-Service]` - Criticality: [Tier 0], Complexity: [Medium], Key Dependencies: [Identity-Provider, Token-Store]\n    *   `[Service Name 3: e.g., Profile-Mgmt-UI-Backend]` - Criticality: [Tier 1], Complexity: [Medium], Key Dependencies: [User-API, Image-CDN]\n    *   ... (List all services grouped in this wave with their assessed characteristics)\n\n## III. Grouping Criteria Application for this Wave\n*   **Dependency Chain Rationale:** [Explain the inter-dependencies. e.g., \"Auth-Service is a core upstream for User-API, and both are foundational for Profile-Mgmt-UI-Backend. Grouping them ensures a cohesive migration of the user identity and management stack.\"]\n*   **Business Criticality Rationale:** [Explain why these services are prioritized now. e.g., \"These services underpin all user interactions and secure access, making their stable migration crucial at this stage to enable further feature migrations.\"]\n*   **Technical Complexity Rationale:** [Highlight common technical characteristics or challenges. e.g., \"Focus on sensitive data handling, robust security protocols, and integration with external identity providers.\"]\n\n## IV. Dependencies & Prerequisites\n*   **Upstream Wave Dependencies:** [List previous waves that *must* be successfully completed before this wave begins. e.g., \"Wave 1 (Shared Logging & Metrics), Wave 2 (Core Database Services).\"]\n*   **External System Dependencies:** [Any external systems, APIs, or third-party services that must be ready or integrated with the new platform for this wave's services.]\n*   **Team/Resource Readiness:** [Specify required teams, specific skillsets, necessary tools, and infrastructure provisioning that must be in place.]\n\n## V. Migration Approach & Milestones\n*   **Key Migration Steps:**\n    *   [e.g., **Code Preparation:** Refactor service `User-API` for new environment compatibility.]\n    *   [e.g., **Infrastructure Provisioning:** Deploy new Kubernetes clusters for `Auth-Service` and `User-API` in Target VPC.]\n    *   [e.g., **Data Migration Strategy:** Plan for real-time replication and eventual consistency for `User-DB` data migration.]\n    *   [e.g., **Testing Strategy:** Unit, Integration, Performance, Security, and User Acceptance Testing (UAT) for all services in parallel.]\n    *   [e.g., **Cutover Plan:** Blue-green deployment strategy for `Auth-Service`, followed by a staged DNS switch for `User-API` over 24 hours.]\n    *   [e.g., **Rollback Plan:** Document explicit steps for immediate rollback to previous infrastructure in case of critical failure.]\n*   **Major Milestones:**\n    *   `[YYYY-MM-DD]` - Code Freeze for Wave 3 Services\n    *   `[YYYY-MM-DD]` - Staging Environment Deployment Complete\n    *   `[YYYY-MM-DD]` - Performance & Security Testing Complete\n    *   `[YYYY-MM-DD]` - Production Cutover Window\n    *   `[YYYY-MM-DD]` - Post-Migration Stability Checkpoint\n\n## VI. Risks & Mitigation\n*   **Identified Risks:**\n    *   [Risk 1: Description, e.g., \"Potential for user lockout during `Auth-Service` cutover due to session invalidation.\"]\n    *   [Risk 2: Description, e.g., \"Data inconsistencies between old and new `User-DB` during replication window.\"]\n*   **Mitigation Strategies:**\n    *   [Mitigation for Risk 1: e.g., \"Implement a grace period for old sessions, extensive pre-cutover testing, clear communication to support teams.\"]\n    *   [Mitigation for Risk 2: e.g., \"Utilize transactional replication with robust error handling, implement reconciliation scripts, continuous monitoring for data drift.\"]\n\n## VII. Success Metrics\n*   **Key Performance Indicators (KPIs):**\n    *   `Auth-Service` Uptime: > 99.99% post-migration.\n    *   `User-API` Latency: < 50ms (p95) post-migration.\n    *   Zero Critical Incidents within 72 hours post-cutover.\n    *   Successful migration of 100% of services within the wave.\n*   **Monitoring Strategy:** [Specify tools and dashboards for real-time observation of KPIs (e.g., Grafana, Prometheus, ELK stack). Include alerts setup.]\n\n## VIII. Team & Responsibilities\n*   **Wave Lead:** [Name/Role, e.g., Sarah Chen - Senior Engineering Manager]\n*   **Core Migration Team:** [Team Alpha (Auth), Team Beta (User Profile), DevOps Team]\n*   **Key Stakeholders:** [Product Manager (User Identity), Business Owner (Customer Experience), Security Team Lead]\n\n## IX. Communication Plan\n*   **Internal:** Daily stand-ups, weekly status reports to leadership, dedicated Slack channel for real-time updates/issues.\n*   **External (if applicable):** Pre-planned customer notifications for potential minor service disruptions (if any), support team training.\n```",
    "category": "strategy",
    "source": "migration_wave_strategy",
    "tags": [
      "microservices",
      "migration",
      "strategy",
      "waves",
      "planning",
      "nucleus"
    ]
  }
}
TERMINATE
AI (Retry): # Microservice Migration Wave Strategy for Nucleus

**Date:** [Current Date]
**Prepared By:** Strategist Agent
**Objective:** To define a comprehensive framework for grouping 100 microservices into logical migration waves, establishing clear criteria and a sequence to ensure a controlled, efficient, and low-risk transition to the new infrastructure. This strategy aims to accelerate migration planning and execution once the service manifest is complete.

---

## 1. Framework for Grouping Microservices into Migration Waves

The migration of 100 microservices requires a structured, iterative approach to manage complexity, minimize risk, and maintain business continuity. Our framework centers on creating distinct "waves" of migration, each with specific objectives, service groupings, and lessons learned cycles.

### Core Principles:

*   **Risk Minimization:** Prioritize identifying and migrating lower-risk, less critical services first to refine processes and infrastructure before tackling high-stakes components.
*   **Business Value Acceleration:** Group services that unlock immediate business value or enable critical new features on the target platform.
*   **Dependency Management:** Carefully orchestrate the migration order to satisfy inter-service dependencies and prevent outages.
*   **Iterative Learning:** Each wave serves as a learning opportunity, with insights feeding into the planning and execution of subsequent waves.
*   **Scalability & Automation:** Aim to automate migration steps wherever possible, scaling processes as confidence grows.

## 2. Criteria for Grouping Services

Microservices will be grouped based on a combination of technical and business-driven factors:

### 2.1. Dependency Chains (Technical Grouping)

*   **Upstream/Downstream Dependencies:**
    *   **Leaf Services:** Services with no outgoing dependencies are ideal for early waves as they are self-contained.
    *   **Core Upstreams:** Services that many other services depend on (e.g., authentication, core data providers) might be migrated early (if isolated) or later (if complex), but their migration will significantly impact downstream planning.
    *   **Shared Infrastructure/Data Stores:** Group services that heavily rely on a common database, messaging queue, or caching layer to reduce complexity and ensure data consistency during transition.
*   **API Gateway/Integration Layers:** Services exposed via a common API gateway or tightly integrated through specific middleware might be grouped to ensure seamless external interaction post-migration.
*   **Data Migration Needs:** Services requiring significant data migration efforts (e.g., large databases, complex ETL) will be identified and potentially grouped for specialized handling.

### 2.2. Business Criticality (Strategic Grouping - Based on `strategy.md`)

*   **Tier 0 (Mission Critical):** Services directly tied to primary revenue streams, legal compliance, or core customer experience (e.g., order processing, payment gateways). These typically require the highest level of caution and will likely be in later waves after processes are proven.
*   **Tier 1 (High Importance):** Services supporting key business processes with some tolerance for brief degradation or planned downtime (e.g., user profile management, inventory lookup).
*   **Tier 2 (Moderate Importance):** Supporting services, internal tools, or features with less direct customer impact or lower transaction volumes. Good candidates for mid-waves.
*   **Tier 3 (Low Importance/Support):** Internal monitoring, analytics dashboards, non-essential administrative tools. Excellent candidates for early "pathfinder" waves.

### 2.3. Technical Complexity & Risk Profile

*   **Simple/Low Risk:** Services with well-defined boundaries, minimal dependencies, modern architecture, and clear operational runbooks. These are perfect for initial waves.
*   **Moderate Complexity:** Services that might require minor code changes, have a few external integrations, or moderate data migration.
*   **High Complexity/High Risk:** Legacy systems, tightly coupled monoliths broken into microservices, services with unique hardware requirements, extensive data transformation, or high-volume transactional services. These will be scheduled for later waves, benefiting from perfected processes.

## 3. Sequence of Migration Waves

The migration will proceed in distinct waves, building confidence and capability incrementally.

### Wave 0: Pathfinders & Learning (Approx. 5-10 Services)
*   **Criteria:** Tier 3 business criticality, Low technical complexity, minimal dependencies, "low hanging fruit."
*   **Goal:** Validate migration tooling, infrastructure setup, deployment pipelines, monitoring, and rollback procedures. Identify unforeseen challenges and refine the overall migration playbook.
*   **Example Services:** Internal monitoring dashboard, static content delivery, non-critical logging aggregators, feature flags service.

### Wave 1: Foundational Services & Enablers (Approx. 10-15 Services)
*   **Criteria:** Essential shared services, authentication/authorization components, core infrastructure support (e.g., DNS, certificate management services), services critical for subsequent waves. Mix of Tier 2/3.
*   **Goal:** Establish a stable and robust platform foundation upon which critical business applications can be built and migrated.
*   **Example Services:** Centralized identity provider (if self-managed), API gateway components, common notification service, core configuration management.

### Wave 2: Critical, Isolated Business Capabilities (Approx. 15-20 Services)
*   **Criteria:** High business criticality (Tier 1/2) but relatively isolated or with well-understood/managed dependencies. Services that can demonstrate early business value on the new platform.
*   **Goal:** Begin shifting core business functions, showcasing tangible benefits, and further validating the end-to-end migration process for more impactful services.
*   **Example Services:** Read-only product catalog, customer profile retrieval, specific analytics aggregation services, low-volume transactional services.

### Wave 3: Interconnected Business Domains (Approx. 20-30 Services)
*   **Criteria:** Groups of services forming coherent business domains with significant internal dependencies. Focus on migrating entire sub-systems. Mix of Tier 1/2.
*   **Goal:** Migrate substantial functional blocks, allowing for internal optimization and integrated testing within the new environment. Address complex internal data flows.
*   **Example Services:** User management suite (signup, login, profile updates), inventory management, specific modules of order fulfillment.

### Wave 4: High Complexity & Mission-Critical Core (Remaining Services)
*   **Criteria:** Mission-critical (Tier 0), high transaction volume, complex legacy integrations, services requiring extensive data migration, or those with the highest operational risk.
*   **Goal:** Complete the migration of the most challenging and business-critical systems, leveraging the refined processes and learned experience from all previous waves. Requires maximum planning, robust rollback strategies, and contingency.
*   **Example Services:** Core order placement and processing, financial ledger, real-time inventory updates, payment processing backend.

---

## 4. Microservice Migration Wave Plan Template

This template will be used to detail each specific migration wave, ensuring consistent planning and execution across the entire program.

```markdown
# Microservice Migration Wave Plan - [Wave Number]: [Wave Name]

## 1. Wave Overview
*   **Wave Number:** [e.g., Wave 0, Wave 1, Wave 2, etc.]
*   **Wave Name/Theme:** [A descriptive name, e.g., Pathfinder, Core Auth Migration, Product Catalog Shift]
*   **Strategic Alignment (from strategy.md/roadmap.md):** [Briefly explain how this wave contributes to higher-level business goals.]
*   **Target Start Date:** [YYYY-MM-DD]
*   **Target Completion Date:** [YYYY-MM-DD]
*   **Key Objectives for this Wave:**
    *   [Specific, measurable goal 1, e.g., Successfully migrate 5 Tier 3 services.]
    *   [Specific, measurable goal 2, e.g., Validate Kubernetes cluster stability under load.]
    *   [Specific, measurable goal 3, e.g., Reduce latency for Service X by 15% post-migration.]
*   **Success Metrics:**
    *   [Metric 1, e.g., 0 critical incidents post-migration for 2 weeks.]
    *   [Metric 2, e.g., All integrated tests pass with new infrastructure.]
    *   [Metric 3, e.g., Performance benchmarks meet or exceed current baselines.]
*   **Risks & Mitigation:**
    *   [Risk Description 1] -> [Mitigation Strategy 1: Actions, Owner, Deadline]
    *   [Risk Description 2] -> [Mitigation Strategy 2: Actions, Owner, Deadline]
    *   [...]

## 2. Services Included in this Wave
| Service Name      | Business Criticality (T0-T3) | Technical Complexity (Low/Med/High) | Key Dependencies (Upstream/Downstream) | Current Platform | Target Platform | Data Migration Needs? (Y/N/Details) | Notes/Justification for Wave Inclusion |
| :---------------- | :--------------------------- | :---------------------------------- | :----------------------------------- | :--------------- | :-------------- | :---------------------------------- | :------------------------------------- |
| `service-alpha`   | T3                           | Low                                 | `None`                               | Legacy VM        | K8s             | N                                   | Ideal for initial process validation.  |
| `service-beta`    | T2                           | Medium                              | `service-gamma` (downstream)         | On-prem          | AWS ECS         | Y (Small DB)                        | Depends on `service-gamma` stability.  |
| `service-gamma`   | T1                           | High                                | `shared-db-1` (upstream)             | Hybrid           | Azure Functions | Y (Large DB, ETL)                   | Critical component, complex data.      |
| `...`             | `...`                        | `...`                               | `...`                                | `...`            | `...`           | `...`                               | `...`                                  |

## 3. Wave-Specific Migration Strategy & Plan
*   **High-Level Approach:** [e.g., Lift-and-shift, Re-platform (containerize), Re-architect (serverless refactor)]
*   **Tooling & Technologies Utilized:** [e.g., AWS CloudFormation, Kubernetes, Helm, Terraform, Data Migration Service (DMS), custom scripts]
*   **Pre-Migration Checklist:**
    *   [Item 1, e.g., All service manifests reviewed and approved.]
    *   [Item 2, e.g., New infrastructure provisioned and validated.]
    *   [Item 3, e.g., Monitoring and alerting configured for target environment.]
*   **Migration Steps (Detailed Sequence):**
    *   [Step 1: Description, Owner, Estimated Time]
    *   [Step 2: Description, Owner, Estimated Time]
    *   [...]
*   **Rollback Plan (Detailed):**
    *   [Clear, step-by-step instructions to revert to the previous state in case of failure.]
    *   [Defined trigger conditions for rollback.]
    *   [Estimated rollback time.]
*   **Testing Strategy:**
    *   **Unit & Integration Tests:** [Status, coverage goals, tools used]
    *   **Performance & Load Tests:** [Target benchmarks, tools, validation criteria]
    *   **User Acceptance Testing (UAT):** [Stakeholders involved, acceptance criteria, sign-off process]
    *   **Security Testing:** [Penetration testing, vulnerability scans post-migration]
*   **Communication Plan:** [Key stakeholders, communication channels, frequency of updates, incident response protocol.]

## 4. Resource Allocation & Team
*   **Wave Lead:** [Name/Role]
*   **Core Migration Team:** [List individuals/teams, their roles, and responsibilities]
*   **Supporting Teams:** [e.g., QA, DevOps, Security, Product Owners, Business Analysts]
*   **Required Skills/Expertise:** [e.g., Kubernetes, Cloud X, Database Admin]

## 5. Post-Migration Activities & Handover
*   **Monitoring & Alerting Validation:** [Confirm dashboards, alerts, logging are fully functional and integrated.]
*   **Performance Optimization:** [Planned post-migration tuning efforts.]
*   **Service Ownership & Support:** [Define clear ownership for ongoing operations, support contacts.]
*   **Decommissioning Old Services:** [Timeline and plan for gracefully shutting down and removing old instances.]
*   **Lessons Learned:** [Process for capturing insights, successes, failures, and recommendations for future waves.]

## 6. Dependencies for Subsequent Waves
*   **Services successfully migrated in this wave that are critical for future waves:** [List services]
*   **Known blockers or open items for future waves identified during this wave:** [Description of blocker, proposed action]
```
---
This strategy provides a robust framework to guide the migration of Nucleus's microservices, ensuring business goals are met with minimal disruption.

TERMINATE
```
