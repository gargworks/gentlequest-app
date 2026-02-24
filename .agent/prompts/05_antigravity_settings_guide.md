# Antigravity Autonomous Settings Guide

To ensure Google Antigravity maintains a multi-hour session using its autonomous features, you must configure the agent's permissions and review policies to minimize manual interruptions. By default, the environment is designed to support sessions lasting up to 8 hours, which is essential for complex workflows. 

## 1. Configure "Always Proceed" Policies
To prevent the agent from stopping and waiting for your input after every task, you must adjust the Artifact Review Policy and Terminal Command Auto Execution settings. 
* **Artifact Review Policy**: Go to the "Agent" tab in settings and set this to "Always Proceed". This allows the agent to move directly from planning to execution without waiting for you to approve implementation plans.
* **Terminal Command Auto Execution**: Set this to "Turbo" (or "Always Proceed"). In this mode, the agent will automatically execute terminal commands unless they are on a specific "Deny list" you have configured. 

## 2. Use "Planning Mode" for Complex Tasks
For long-duration sessions, always ensure the agent is in Planning mode rather than Fast mode. 
* **Why it works**: In Planning mode, the agent builds a comprehensive multi-step task list and implementation plan before starting. This structured approach allows it to handle hours of work systematically without losing track of the final goal.
* **How to toggle**: Select "Planning" from the agent side panel chat or the Agent Manager view. 

## 3. Manage Resource Limits
Continuous multi-hour sessions can be affected by rate limits and quotas, particularly when using high-performance models such as Gemini 3 Pro. 
* **Upgrade for Throughput**: Google AI Pro or Ultra subscribers have higher rate limits, which are necessary for "dependable throughput" during bulk tasks or long drafts.
* **Allow Browser Automation**: Ensure the "Allow automation of browser actions" is enabled in your Browser Control settings so the agent can independently verify web-based tasks without timing out. 

## 4. Setting Global Behavior Rules
You can guide the agent's long-term behavior by adding Global Rules. These act as persistent instructions (e.g., "always document code" or "follow PEP 8") that the agent will follow throughout the entire session without needing repeated prompts. 
