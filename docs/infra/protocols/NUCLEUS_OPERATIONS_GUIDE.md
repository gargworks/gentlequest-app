# Nucleus v0.5.0 Operations Guide
**Last Updated:** 2026-01-09
**Author:** Antigravity

---

## Quick Reference

| Feature | Tool/Command | Status |
|:---|:---|:---:|
| **Native Sync** | `brain_file_changes` | ✅ Live |
| **GCloud Status** | `brain_gcloud_status` | ✅ Live |
| **GCloud Services** | `brain_gcloud_services` | ✅ Live |
| **Cloud Build** | `gcloud builds submit` | ✅ Deployed |
| **Cloud Run** | [gentlequest-backend](https://gentlequest-backend-7an2ps6yna-uc.a.run.app) | ✅ Running |

---

## GentleQuest Dashboard (Quick Links)

| Resource | Link |
|:---|:---|
| **🌐 Live App** | https://gentlequest-backend-7an2ps6yna-uc.a.run.app |
| **✅ API Health** | https://gentlequest-backend-7an2ps6yna-uc.a.run.app/api/health |
| **📦 Latest Build** | [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds?project=gen-lang-client-0894185576) |
| **🚀 Cloud Run Console** | [Services](https://console.cloud.google.com/run?project=gen-lang-client-0894185576) |
| **🗄️ Cloud SQL Console** | [Databases](https://console.cloud.google.com/sql/instances?project=gen-lang-client-0894185576) |
| **📊 Project Dashboard** | [GCP Project](https://console.cloud.google.com/home/dashboard?project=gen-lang-client-0894185576) |
| **💰 Billing** | [Billing Overview](https://console.cloud.google.com/billing?project=gen-lang-client-0894185576) |

---

## 1. Project Configuration

### GCP Project Setup
```bash
# Set active project
gcloud config set project gen-lang-client-0894185576

# Verify configuration
gcloud config list

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Environment Info
| Property | Value |
|:---|:---|
| **Project ID** | `gen-lang-client-0894185576` |
| **Project Name** | `gentlequest-prod` |
| **Account** | `gargenterprises2019@gmail.com` |
| **Region** | `us-central1` |

---

## 2. Nucleus Native Sync (Phase 50)

### What It Does
Watches the `.brain/` folder for file changes and notifies connected agents in real-time.

### Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Windsurf   │────▶│   .brain/    │◀────│ Antigravity │
│   (IDE)     │     │   folder     │     │   (IDE)     │
└─────────────┘     └──────┬───────┘     └─────────────┘
                          │
                    ┌─────▼─────┐
                    │FileMonitor│
                    │ (watchdog)│
                    └─────┬─────┘
                          │
               ┌──────────▼──────────┐
               │ brain_file_changes  │
               │     (MCP Tool)      │
               └─────────────────────┘
```

### Files Created
| File | Purpose |
|:---|:---|
| [file_monitor.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/file_monitor.py) | FileMonitor class with watchdog |
| [pyproject.toml](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/pyproject.toml) | Added `watchdog>=3.0.0` dependency |

### How to Use
The FileMonitor starts automatically when the MCP server launches.
Agents can query for file changes:

```python
# Called by AI agents (not in terminal!)
brain_file_changes()
# Returns: {"status": "active", "event_count": 3, "events": [...]}
```

### Verification Test (Passed)
```bash
# Create test file while monitor runs
touch /path/to/.brain/test.txt

# Monitor detects:
# FileChangeEvent(event_type='created', path='.../test.txt', ...)
```

---

## 3. GCloud Integration (Phase 49)

### What It Does
Wraps the local `gcloud` CLI so AI agents can query infrastructure status.

### Files Created
| File | Purpose |
|:---|:---|
| [gcloud_ops.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/gcloud_ops.py) | GCloudOps class wrapping gcloud CLI |

### MCP Tools

#### `brain_gcloud_status`
Check authentication and project status.
```json
{
  "gcloud_available": true,
  "gcloud_path": "/opt/homebrew/bin/gcloud",
  "project": "gen-lang-client-0894185576",
  "account": "gargenterprises2019@gmail.com"
}
```

#### `brain_gcloud_services`
List Cloud Run services.
```json
{
  "success": true,
  "data": [
    {"name": "gentlequest-backend", "url": "https://..."}
  ]
}
```

---

## 4. Cloud Build Deployment

### Configuration File
[cloudbuild.yaml](file:///Users/lokeshgarg/ai-mvp-backend/cloudbuild.yaml)

### Deployment Command
```bash
cd ~/ai-mvp-backend
gcloud builds submit --config=cloudbuild.yaml
```

### What Happens
1. Creates archive of source (~307MB)
2. Uploads to GCS bucket
3. Cloud Build pulls Flutter image
4. Builds Docker container
5. Deploys to Cloud Run

### Build Logs
```bash
# List recent builds
gcloud builds list --limit=5

# View specific build log
gcloud builds log BUILD_ID
```

### Latest Build
| Property | Value |
|:---|:---|
| **Build ID** | `334437b9-1a12-4c46-ba61-f66533536ea8` |
| **Status** | SUCCESS |
| **Console URL** | [View in GCP Console](https://console.cloud.google.com/cloud-build/builds/334437b9-1a12-4c46-ba61-f66533536ea8?project=999376128638) |

---

## 5. Cloud Run Service

### Service Details
| Property | Value |
|:---|:---|
| **Service Name** | `gentlequest-backend` |
| **URL** | https://gentlequest-backend-7an2ps6yna-uc.a.run.app |
| **Region** | `us-central1` |

### Management Commands
```bash
# List services
gcloud run services list

# Describe service
gcloud run services describe gentlequest-backend --region=us-central1

# View logs
gcloud run services logs read gentlequest-backend --region=us-central1

# Delete service (careful!)
gcloud run services delete gentlequest-backend --region=us-central1
```

---

## 6. Workflow: Deploy GentleQuest

### Prerequisites
- [x] `gcloud` CLI installed
- [x] Authenticated: `gcloud auth login`
- [x] Project set: `gcloud config set project gen-lang-client-0894185576`
- [x] APIs enabled: `run.googleapis.com`, `cloudbuild.googleapis.com`

### Step-by-Step
```bash
# 1. Navigate to project
cd ~/ai-mvp-backend

# 2. Deploy (takes ~5-10 minutes)
gcloud builds submit --config=cloudbuild.yaml

# 3. Verify deployment
gcloud run services list

# 4. Test service
curl https://gentlequest-backend-7an2ps6yna-uc.a.run.app/api/health
```

---

## 7. Workflow: Nucleus Package Update

### Install Locally
```bash
# Using pip in a venv
python3 -m venv /tmp/nucleus_venv
source /tmp/nucleus_venv/bin/activate
pip install watchdog
pip install -e ./mcp-server-nucleus
```

### Verify Installation
```bash
python3 -c "from mcp_server_nucleus import brain_file_changes, brain_gcloud_status; print('OK')"
```

---

## 8. Troubleshooting

### gcloud: command not found
```bash
# Check if installed
which gcloud

# Common locations
/opt/homebrew/bin/gcloud
~/google-cloud-sdk/bin/gcloud
```

### Permission Denied on Cloud Build
```bash
# Grant Cloud Build role
gcloud projects add-iam-policy-binding gen-lang-client-0894185576 \
  --member="user:gargenterprises2019@gmail.com" \
  --role="roles/cloudbuild.builds.editor"
```

### API Not Enabled
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

## 9. Files Reference

### Nucleus Package
| File | Description |
|:---|:---|
| [pyproject.toml](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/pyproject.toml) | Package config (v0.5.0) |
| [__init__.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py) | Main module with MCP tools |
| [file_monitor.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/file_monitor.py) | File watching implementation |
| [gcloud_ops.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/gcloud_ops.py) | GCloud CLI wrapper |

### Infrastructure
| File | Description |
|:---|:---|
| [cloudbuild.yaml](file:///Users/lokeshgarg/ai-mvp-backend/cloudbuild.yaml) | Cloud Build config |
| [gcp_config.json](file:///Users/lokeshgarg/ai-mvp-backend/infra/gcp_config.json) | GCP configuration |

### Documentation
| File | Description |
|:---|:---|
| [NUCLEUS_PRODUCT_SPECS.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NUCLEUS_PRODUCT_SPECS.md) | Product specifications (The Bible) |
| [task.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/task.md) | Task tracking |
| [walkthrough.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/walkthrough.md) | Implementation walkthrough |

---

## 10. Version History

| Version | Date | Changes |
|:---|:---|:---|
| **0.5.0** | 2026-01-09 | Native Sync (File Watching), GCloudOps |
| **0.4.0** | 2026-01-08 | Dual Engine LLM, Commitment Ledger |

---

> **Document Maintained By:** Antigravity  
> **Last Verified:** 2026-01-09 02:22 IST

---

## 11. Troubleshooting

### 502 Bad Gateway on Cloud Run
If Gunicorn fails to start (Connection Refused):
1. Check logs for "Starting gunicorn".
2. If using `start.sh`, ensure no commands fail silently before `exec`.
3. Startup Probes might timeout if the container is slow (Cold Start > 60s).

### Slow Cloud Build Uploads
If build context is > 100MB:
1. Create `.gcloudignore` in project root.
2. Exclude `venv/`, `node_modules/`, `.brain/`, and backup folders.
3. This reduces upload time from ~2m to ~10s.
