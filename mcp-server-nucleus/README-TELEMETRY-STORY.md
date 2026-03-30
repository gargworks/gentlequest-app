# Nucleus MCP Server

TODO: full README content. This file currently just documents telemetry for development.

## Telemetry & Reliability

Nucleus ships with a **batteries-included** observability stack so you can see how your agents behave in the real world without wiring anything by hand.

- **Phase B – Deep traces & metrics pipeline**  
  - OpenTelemetry collector with OTLP (gRPC + HTTP), Prometheus, and Jaeger wired together.  
  - Anonymous usage metrics (`nucleus.anon.*`) flow from the CLI → SDK → collector → Prometheus → Grafana.  
  - One command starts the full stack locally for verification:

    ```bash
    npm run telemetry:dash
    npm run telemetry:local:demo -- morning-brief
    ```

- **Phase C – Dashboards and daily brief**  
  - Prebuilt Grafana dashboards show total commands, error rate, latency percentiles, and OS / Python distribution.  
  - A daily brief script turns raw metrics into a human-readable report:

    ```bash
    npm run telemetry:brief
    ```

  - You get a single snapshot with top commands, error analysis, latency, and quick links to Grafana, Prometheus, and Jaeger.

- **Phase D – Alerts, trends, and anomalies**  
  - Grafana alert rules watch error rate, traffic drops, and statistical anomalies (3σ Z-score) on command and error rates.  
  - Alerts can fan out to Slack and email via simple environment variable configuration.  
  - A “Telemetry Trends” dashboard and the brief script both include period-over-period comparisons (day vs day, week vs week) so you can see growth and regressions at a glance.

- **Privacy by design**  
  - Anonymous only: command names, categories, durations, error types, OS and Python version.  
  - No prompts, responses, file paths, or org content are ever sent.

This gives Nucleus a **production-grade** feedback loop out of the box: you can ship agents, see how they behave, and get paged when something drifts, without bolting on a separate observability project.
