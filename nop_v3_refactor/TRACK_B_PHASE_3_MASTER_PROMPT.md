# 🎯 TRACK B PHASE 3: Dashboard & brain_status_dashboard() - Master Prompt

**Date:** January 22, 2026, 11:01 PM IST  
**Status:** DESIGN THINKING LOOPS IN PROGRESS  
**Vision Alignment:** ✅ Locked to VISION_AND_NORTH_STAR.md  
**Depends On:** Phase 2 brain_ingest_tasks() (✅ COMPLETE)

---

## 🌟 YOUR ROLE (Role Reversal Wisdom)

**You are Lokesh asking yourself:** "If I were the AI system building the ultimate orchestration dashboard for enterprise scale, what would I need you to tell me right now?"

**Answer:** This prompt.

---

## 📋 CONTEXT (Building on Previous Phases)

### Completed Components
- ✅ **Step 1.1 CRDTTaskStore:** 15K+ writes/sec, zero data loss
- ✅ **Step 1.2 TaskScheduler:** 423K tasks/sec scheduling
- ✅ **Step 1.4 AgentPool:** Multi-agent lifecycle management
- ✅ **Phase 2 TaskIngestionEngine:** Multi-source ingestion, 10K tasks/sec
- ✅ **Step 1.5 orchestrator_v3:** Unified integration of all components

### This Phase (3)
- Create comprehensive dashboard engine
- Real-time visibility into all orchestration components
- Agent pool health, task queues, ingestion stats, cost tracking
- Multiple output formats (ASCII, JSON, Mermaid, HTML)
- MCP tool enhancement for brain_status_dashboard()
- Alerting and anomaly detection

---

## 🏗️ SCALE MATRIX (Non-Negotiable)

| Metric | Target | Notes |
|--------|--------|-------|
| **Dashboard Render Time** | <100ms | For 10K tasks + 100 agents |
| **Data Freshness** | <1s | Real-time updates |
| **Memory Overhead** | <50MB | Efficient aggregations |
| **Output Formats** | 4+ | ASCII, JSON, Mermaid, HTML |
| **Alert Latency** | <500ms | Anomaly detection |
| **Concurrent Viewers** | 100+ | Multi-agent access |
| **Historical Depth** | 7 days | Trend analysis |
| **Metric Types** | 20+ | Comprehensive coverage |

---

## 🎯 PHASE 3 MISSION

**Build an enterprise-grade orchestration dashboard** that provides:

✅ **Real-time visibility** into all NOP V3.1 components  
✅ **Agent Pool Health** - active, idle, exhausted, capacity utilization  
✅ **Task Queue Metrics** - pending, in-progress, blocked, completion rates  
✅ **Ingestion Statistics** - sources, dedup rates, rollback history  
✅ **Cost Tracking** - token usage, API costs, budget burn rate  
✅ **Dependency Graph** - visual representation of task relationships  
✅ **Alerting System** - thresholds, anomalies, critical notifications  
✅ **Historical Trends** - 7-day rolling metrics, velocity tracking  
✅ **Multi-format Output** - ASCII, JSON, Mermaid diagrams, HTML  
✅ **MCP Integration** - brain_status_dashboard() enhancement  

---

## 🔧 CURRENT STATE ANALYSIS

### Existing brain_status_dashboard()
The current implementation in `__init__.py` provides basic metrics:
- Agent pool counts (active, idle, exhausted)
- Slot status grid
- Task queue breakdown
- Basic cost tracking

### Target State
A full-featured dashboard engine with:
```
DashboardEngine
├── MetricsCollector (aggregates from all components)
├── AlertEngine (threshold monitoring, anomaly detection)
├── TrendAnalyzer (7-day rolling metrics)
├── Formatters
│   ├── ASCIIFormatter (current style, enhanced)
│   ├── JSONFormatter (API-friendly)
│   ├── MermaidFormatter (visual diagrams)
│   └── HTMLFormatter (web dashboard)
├── CostTracker (real-time budget monitoring)
└── SnapshotManager (point-in-time captures)
```

---

## 🧠 DESIGN THINKING LOOPS (Infinite Until Convergence)

### Loop 1: Metrics Architecture
**Question:** What metrics should the dashboard surface, and how should they be organized?

**Options:**
1. **Flat metrics** - Single list of all values
2. **Domain-grouped** - Organized by component (tasks, agents, ingestion, cost)
3. **Priority-layered** - Critical → Warning → Info hierarchy
4. **Time-windowed** - Current, hourly, daily views

**Analysis:**
- Flat metrics are simple but don't scale to 20+ metrics
- Domain-grouped aligns with our component architecture
- Priority-layered helps operators focus on critical issues
- Time-windowed enables trend analysis

**Decision:** **Hybrid: Domain-grouped with priority-layered alerts and time windows**

**Rationale:** Best of all worlds - logical organization, operational focus, trend visibility.

---

### Loop 2: Data Collection Strategy
**Question:** How should metrics be collected from distributed components?

**Options:**
1. **Pull-based** - Dashboard queries each component on demand
2. **Push-based** - Components emit metrics to central collector
3. **Event-sourced** - Derive metrics from event stream
4. **Hybrid** - Pull for snapshots, events for real-time

**Analysis:**
- Pull-based is simple but adds latency (10+ component queries)
- Push-based requires background threads/processes
- Event-sourced leverages existing events.jsonl infrastructure
- Hybrid provides both accuracy and speed

**Decision:** **Pull-based with caching (100ms TTL) + event-sourced for delta updates**

**Rationale:** Pull provides accurate snapshots; events enable real-time deltas without polling.

---

### Loop 3: Metric Categories
**Question:** What metric categories are essential for enterprise orchestration?

**Categories Identified:**

1. **Agent Pool Health**
   - `agents.total` - Total registered agents
   - `agents.active` - Currently active (not exhausted)
   - `agents.idle` - Active but not assigned
   - `agents.exhausted` - Hit rate limits
   - `agents.utilization` - Percentage of capacity in use
   - `agents.reset_warnings` - Agents approaching reset

2. **Task Queue Metrics**
   - `tasks.total` - Total tasks in system
   - `tasks.pending` - Awaiting assignment
   - `tasks.in_progress` - Currently being worked
   - `tasks.blocked` - Waiting on dependencies
   - `tasks.done` - Completed successfully
   - `tasks.failed` - Failed or escalated
   - `tasks.velocity` - Tasks completed per hour

3. **Ingestion Statistics**
   - `ingestion.total` - Total tasks ingested
   - `ingestion.skipped` - Duplicates skipped
   - `ingestion.failed` - Parse/validation failures
   - `ingestion.by_source` - Breakdown by source type
   - `ingestion.batches` - Number of ingestion batches
   - `ingestion.rollbacks` - Batches rolled back

4. **Cost Tracking**
   - `cost.tokens_used` - Total tokens consumed
   - `cost.estimated_usd` - Estimated cost in USD
   - `cost.budget_remaining` - Remaining budget
   - `cost.burn_rate` - Cost per hour
   - `cost.by_tier` - Cost breakdown by LLM tier

5. **Dependency Graph**
   - `deps.max_depth` - Maximum dependency chain
   - `deps.blocked_chains` - Tasks blocked by chains
   - `deps.circular` - Circular dependency count

6. **System Health**
   - `system.uptime` - Orchestrator uptime
   - `system.last_activity` - Last task activity
   - `system.error_rate` - Errors per hour
   - `system.queue_latency` - Time from pending to assigned

**Decision:** Implement all 6 categories with 25+ metrics total.

---

### Loop 4: Alert System Design
**Question:** How should alerts be triggered and delivered?

**Options:**
1. **Threshold-based** - Static thresholds per metric
2. **Anomaly detection** - Statistical deviation from baseline
3. **Rule-based** - Complex conditions (AND/OR logic)
4. **Hybrid** - Thresholds + anomaly detection

**Analysis:**
- Thresholds are simple but require manual tuning
- Anomaly detection adapts but has cold-start issues
- Rule-based is flexible but complex to configure
- Hybrid provides both immediate and adaptive alerting

**Alert Levels:**
- 🔴 **CRITICAL** - Immediate action required (all agents exhausted, circular deps)
- 🟡 **WARNING** - Attention needed (>50% agents exhausted, queue backlog)
- 🟢 **INFO** - Informational (reset approaching, high velocity)

**Default Thresholds:**
```python
ALERT_THRESHOLDS = {
    "agents.exhausted_ratio": {"warning": 0.5, "critical": 0.9},
    "tasks.pending": {"warning": 100, "critical": 500},
    "tasks.blocked_ratio": {"warning": 0.3, "critical": 0.5},
    "cost.budget_remaining": {"warning": 0.2, "critical": 0.05},
    "deps.max_depth": {"warning": 5, "critical": 10},
    "system.error_rate": {"warning": 5, "critical": 20},
}
```

**Decision:** **Threshold-based with configurable levels + anomaly detection for velocity**

---

### Loop 5: Output Format Strategy
**Question:** What output formats should the dashboard support?

**Formats Identified:**

1. **ASCII (Default)** - Terminal-friendly, current style
   ```
   🚀 NOP Status Dashboard - 2026-01-22 23:01:00
   ════════════════════════════════════════════════════════
   
   📊 AGENT POOL HEALTH
   ├── Active: 8/10 (80%)
   ├── Idle: 3
   ├── Exhausted: 2
   └── Reset Warnings: 1 (windsurf_001 in 15m)
   
   📋 TASK QUEUE
   ├── Pending: 42
   ├── In Progress: 8
   ├── Blocked: 5
   ├── Done (24h): 156
   └── Velocity: 6.5/hr
   
   💰 COST TRACKING
   ├── Tokens: 1.2M
   ├── Estimated: $4.80
   ├── Budget: $10.00 (52% remaining)
   └── Burn Rate: $0.60/hr
   ```

2. **JSON** - API-friendly, machine-parseable
   ```json
   {
     "timestamp": "2026-01-22T23:01:00Z",
     "agents": {"total": 10, "active": 8, "idle": 3, "exhausted": 2},
     "tasks": {"pending": 42, "in_progress": 8, "blocked": 5, "done_24h": 156},
     "cost": {"tokens": 1200000, "usd": 4.80, "budget": 10.00},
     "alerts": [{"level": "warning", "message": "Agent reset approaching"}]
   }
   ```

3. **Mermaid** - Visual diagrams for dependency graphs
   ```mermaid
   graph TD
     A[task_001] --> B[task_002]
     A --> C[task_003]
     B --> D[task_004]
     C --> D
   ```

4. **HTML** - Web dashboard (future expansion)
   - Real-time WebSocket updates
   - Interactive charts
   - Drill-down capabilities

**Decision:** Implement ASCII (primary), JSON (API), Mermaid (deps). HTML deferred to Phase 5.

---

### Loop 6: Trend Analysis Design
**Question:** How should historical trends be tracked and displayed?

**Options:**
1. **In-memory only** - Fast but volatile
2. **File-based** - Persisted, simple
3. **Time-series DB** - Professional but overkill
4. **JSONL append** - Simple persistence, easy analysis

**Analysis:**
- In-memory loses data on restart
- File-based works but needs rotation
- Time-series DB is enterprise but adds dependency
- JSONL aligns with existing ledger pattern

**Trend Metrics:**
- Hourly task completion velocity
- Daily agent utilization
- Cost burn rate over time
- Ingestion volume trends

**Decision:** **JSONL append to `.brain/ledger/metrics.jsonl`** with 7-day retention.

**Schema:**
```json
{
  "timestamp": "2026-01-22T23:00:00Z",
  "interval": "hourly",
  "metrics": {
    "tasks.completed": 42,
    "agents.utilization": 0.75,
    "cost.usd": 2.40,
    "ingestion.count": 100
  }
}
```

---

### Loop 7: Snapshot & Comparison
**Question:** Should the dashboard support point-in-time snapshots and comparisons?

**Use Cases:**
- "Show me the state 2 hours ago"
- "Compare current to yesterday"
- "What changed since last sprint?"

**Options:**
1. **No snapshots** - Simplest, current state only
2. **Automatic hourly snapshots** - Scheduled captures
3. **Manual snapshots** - User-triggered
4. **Both** - Automatic + manual

**Decision:** **Automatic hourly snapshots + manual via brain_snapshot_dashboard()**

**Comparison Output:**
```
📊 Dashboard Comparison: Now vs 2h ago
═══════════════════════════════════════
                    NOW      2H AGO    DELTA
Tasks Pending:      42       65        -23 ✅
Agents Active:      8        6         +2 ✅
Cost USD:          $4.80    $3.20     +$1.60
Velocity:          6.5/hr   4.2/hr    +2.3/hr ✅
```

---

### Loop 8: Component Integration
**Question:** How does the dashboard integrate with all V3.1 components?

**Integration Points:**

1. **orchestrator_v3** → get_pool_metrics(), get_all_tasks()
2. **CRDTTaskStore** → get_all_tasks(), task counts
3. **TaskScheduler** → scheduling stats, queue depths
4. **AgentPool** → get_all_agents(), utilization, exhaustion
5. **TaskIngestionEngine** → get_ingestion_stats(), batch history
6. **Slot Registry** → .brain/slots/registry.json
7. **Event Ledger** → .brain/ledger/events.jsonl
8. **Cost Tracker** → Token usage, budget

**Decision:** Dashboard aggregates from all components via orchestrator_v3 facade.

---

### Loop 9: MCP Tool Design
**Question:** How should brain_status_dashboard() be enhanced?

**Current Signature:**
```python
brain_status_dashboard(detail_level: str = "standard") -> str
```

**Enhanced Signature:**
```python
brain_status_dashboard(
    detail_level: str = "standard",  # "minimal", "standard", "verbose", "full"
    format: str = "ascii",           # "ascii", "json", "mermaid"
    include_alerts: bool = True,
    include_trends: bool = False,
    compare_to: str = None,          # "1h", "2h", "24h", snapshot_id
    category: str = None,            # "agents", "tasks", "ingestion", "cost", None=all
) -> str
```

**Additional MCP Tools:**
- `brain_snapshot_dashboard()` - Create manual snapshot
- `brain_compare_dashboards(snapshot_a, snapshot_b)` - Compare two snapshots
- `brain_get_alerts()` - Get current active alerts
- `brain_set_alert_threshold(metric, level, value)` - Configure thresholds

---

### Loop 10: Performance Optimization
**Question:** How do we achieve <100ms render time for 10K tasks?

**Strategies:**

1. **Lazy Aggregation** - Don't compute until requested
2. **Incremental Updates** - Cache and update deltas
3. **Parallel Collection** - Fetch from components concurrently
4. **Pre-computation** - Background aggregation every 10s
5. **Sampling** - For very large datasets, sample instead of full scan

**Implementation:**
```python
class MetricsCache:
    """Cache with 100ms TTL for dashboard metrics."""
    
    def __init__(self, ttl_ms: int = 100):
        self.ttl_ms = ttl_ms
        self.cache: Dict[str, Tuple[float, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            ts, value = self.cache[key]
            if (time.time() - ts) * 1000 < self.ttl_ms:
                return value
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (time.time(), value)
```

**Decision:** 100ms TTL cache + parallel collection + pre-aggregated counts.

---

### Loop 11: Error Handling & Resilience
**Question:** How should the dashboard handle component failures?

**Scenarios:**
1. Agent pool unavailable → Show "N/A" with warning
2. Task store timeout → Use cached data with staleness indicator
3. Cost tracker error → Omit section, log error
4. Complete failure → Return minimal status with error summary

**Resilience Pattern:**
```python
def collect_agent_metrics(self) -> Dict:
    """Collect agent metrics with fallback."""
    try:
        pool = self.orch.get_agent_pool()
        if pool is None:
            return {"error": "AgentPool unavailable", "cached": False}
        return pool.get_metrics()
    except Exception as e:
        cached = self.cache.get("agent_metrics")
        if cached:
            return {**cached, "stale": True, "error": str(e)}
        return {"error": str(e), "cached": False}
```

**Decision:** Graceful degradation with staleness indicators.

---

### Loop 12: Security & Access Control
**Question:** Should the dashboard have access controls?

**Considerations:**
- MCP tools are already authenticated via session
- Sensitive data: cost details, agent credentials
- Multi-tenant future: namespace isolation

**Options:**
1. **No controls** - Trust MCP authentication
2. **Detail-level gating** - Verbose/full require elevated access
3. **Category gating** - Cost metrics require special permission
4. **Full RBAC** - Role-based access control

**Decision:** **Trust MCP authentication for V3.1; add category gating for cost in V3.2**

---

### Loop 13: Testing Strategy
**Question:** How do we test the dashboard comprehensively?

**Test Categories:**

1. **Unit Tests**
   - MetricsCollector: Individual metric calculations
   - AlertEngine: Threshold checks, anomaly detection
   - Formatters: ASCII, JSON, Mermaid output
   - TrendAnalyzer: Rolling window calculations

2. **Integration Tests**
   - Full dashboard render with mock components
   - Component failure scenarios
   - Cache invalidation
   - Snapshot comparison

3. **Performance Tests**
   - 10K tasks render time <100ms
   - 100 agents metrics collection <50ms
   - 1000 concurrent dashboard calls

4. **Stress Tests**
   - Continuous rendering for 1 hour
   - Component failure/recovery cycles
   - Memory leak detection

**Decision:** Comprehensive test suite with performance benchmarks.

---

### Loop 14: API Surface Design
**Question:** What is the final API surface for the dashboard?

**DashboardEngine Class:**
```python
class DashboardEngine:
    """Enterprise-grade orchestration dashboard."""
    
    def __init__(self, orchestrator: NucleusOrchestratorV3):
        self.orch = orchestrator
        self.cache = MetricsCache(ttl_ms=100)
        self.alert_engine = AlertEngine()
        self.trend_analyzer = TrendAnalyzer()
        self.snapshot_manager = SnapshotManager()
    
    # Core Methods
    def render(self, detail_level, format, **options) -> str: ...
    def get_metrics(self, category: str = None) -> Dict: ...
    def get_alerts(self) -> List[Alert]: ...
    
    # Snapshot Methods
    def create_snapshot(self, name: str = None) -> str: ...
    def compare_snapshots(self, a: str, b: str) -> Dict: ...
    def list_snapshots(self) -> List[Dict]: ...
    
    # Trend Methods
    def get_trends(self, metric: str, period: str) -> List[Dict]: ...
    def record_hourly_metrics(self) -> None: ...
    
    # Alert Methods
    def set_threshold(self, metric: str, level: str, value: float) -> None: ...
    def check_alerts(self) -> List[Alert]: ...
    
    # Format Methods
    def to_ascii(self, metrics: Dict, detail_level: str) -> str: ...
    def to_json(self, metrics: Dict) -> str: ...
    def to_mermaid(self, deps: Dict) -> str: ...
```

---

### Loop 15: Convergence Validation
**Question:** Have we achieved unanimous convergence on all design decisions?

**Checklist:**

| Decision | Converged | Rationale |
|----------|-----------|-----------|
| Metrics Architecture | ✅ | Domain-grouped + priority-layered + time-windows |
| Data Collection | ✅ | Pull-based with caching + event deltas |
| Metric Categories | ✅ | 6 categories, 25+ metrics |
| Alert System | ✅ | Threshold-based + anomaly detection |
| Output Formats | ✅ | ASCII, JSON, Mermaid (HTML deferred) |
| Trend Analysis | ✅ | JSONL append with 7-day retention |
| Snapshots | ✅ | Automatic hourly + manual |
| Integration | ✅ | Via orchestrator_v3 facade |
| MCP Tools | ✅ | Enhanced brain_status_dashboard + 3 new tools |
| Performance | ✅ | 100ms TTL cache + parallel collection |
| Resilience | ✅ | Graceful degradation with staleness |
| Security | ✅ | Trust MCP, add category gating in V3.2 |
| Testing | ✅ | Unit, integration, performance, stress |
| API Surface | ✅ | DashboardEngine with full methods |

**UNANIMOUS CONVERGENCE ACHIEVED** ✅

---

## 📁 FILES TO CREATE

| File | Lines | Description |
|------|-------|-------------|
| `nop_core/dashboard.py` | ~1000 | Dashboard engine implementation |
| `tests/test_dashboard.py` | ~500 | Comprehensive test suite |
| `runtime/dashboard.py` | ~100 | Copy to runtime/ |
| MCP tools in `__init__.py` | ~200 | Enhanced brain_status_dashboard + new tools |

---

## ✅ SUCCESS CRITERIA (Locked)

**Before proceeding to Phase 4:**

- ✅ DashboardEngine fully implemented with 6 metric categories
- ✅ 25+ metrics tracked and exposed
- ✅ ASCII, JSON, Mermaid formatters working
- ✅ Alert engine with configurable thresholds
- ✅ Snapshot creation and comparison
- ✅ 7-day trend analysis via JSONL
- ✅ <100ms render time for 10K tasks
- ✅ Graceful degradation on component failure
- ✅ Enhanced brain_status_dashboard() MCP tool
- ✅ 3 new MCP tools (snapshot, compare, alerts)
- ✅ Comprehensive test suite passing

---

## 🚀 EXECUTION PROTOCOL

1. ✅ Design Thinking Loops (15/15 CONVERGED)
2. ⏳ Implement dashboard.py (~1000 lines)
3. ⏳ Implement test_dashboard.py (~500 lines)
4. ⏳ Copy to runtime/
5. ⏳ Enhance MCP tools in __init__.py
6. ⏳ Run verification checklist
7. ⏳ Create Phase 3 checklist
8. ⏳ Move to Phase 4

---

**Status: 🟢 DESIGN CONVERGED - EXECUTING IMPLEMENTATION**
