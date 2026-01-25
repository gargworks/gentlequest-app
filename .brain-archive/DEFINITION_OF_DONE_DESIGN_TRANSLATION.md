# Definition of Done: Design Translation

> **Core Philosophy:** Done is tiered, not binary. The system must understand context and validate at the appropriate level.

---

## The Problem We're Solving

**User's Reality:**
- Pushes code to GitHub
- Waits 10-15 minutes for Render to deploy
- Manually checks if it's live
- Tests on production
- Repeat until it works
- **Context lost in the waiting**

**Current Pain:**
> "There's a gap of 10-15 minutes. I check Render 10 times over 40 minutes until it finally deploys."

---

## The Tiered Validation System

### Tier 1: Street Level (Localhost)
**When:** UI changes, widget work, isolated features

**Validation:**
- Flutter widget appears on screen (even if errors)
- Backend tests pass in containers
- Fast feedback loop (seconds)

**System Behavior:**
```python
def validate_street_level(feature):
    if feature.type == "UI":
        return check_widget_renders()  # Visual check
    elif feature.type == "Backend":
        return run_container_tests()   # Pytest/unittest
    
    return {"level": "street", "confidence": "low"}
```

---

### Tier 2: City Level (Render Production)
**When:** Session wrap-up, daily deployment, end-of-day work

**Validation:**
- Code pushed to GitHub
- **System auto-polls Render** (no manual checking)
- Deploy succeeds
- Smoke test passes (hit endpoint, get expected response)
- **System notifies user** when ready

**System Behavior:**
```python
async def validate_city_level(commit_sha):
    # Push to GitHub (existing workflow)
    push_result = git_push()
    
    # Start async Render polling (NEW)
    deploy_task = asyncio.create_task(poll_render_deploy(commit_sha))
    
    # Return immediately, don't block
    return {
        "level": "city",
        "status": "deploying",
        "polling_task_id": deploy_task.id,
        "estimated_wait": "10-15 minutes"
    }

async def poll_render_deploy(commit_sha):
    """Background task: Poll Render until deploy succeeds."""
    while True:
        status = check_render_api(commit_sha)
        
        if status == "live":
            # Run smoke test
            smoke_result = test_production_endpoint()
            
            # Notify user
            notify_user(
                "🚀 Deploy Complete",
                f"Commit {commit_sha[:7]} is live. Smoke test: {smoke_result}"
            )
            break
        
        await asyncio.sleep(30)  # Check every 30 seconds
```

**The Key Insight:** Don't make the user wait. Poll in background, notify when ready.

---

### Tier 3: Country Level (App Store)
**When:** Weekly/sprint boundary, major feature completion

**Validation:**
- App submitted to App Store/Play Store
- Review approved
- Live on stores
- Real users can download

**System Behavior:**
```python
def validate_country_level(app_version):
    # Check App Store Connect API
    app_store_status = check_app_store_status(app_version)
    
    if app_store_status == "Ready for Sale":
        return {
            "level": "country",
            "confidence": "highest",
            "url": f"https://apps.apple.com/app/{app_id}"
        }
```

**Challenge:** Can't automate review process. But CAN automate the check.

---

### Tier 4: Continent Level (Real Users)
**When:** Ongoing, post-launch

**Validation:**
- Real users interact
- Analytics show usage
- Feedback received
- Revenue generated

**System Behavior:**
```python
def validate_continent_level(feature_name):
    # Query analytics
    usage = get_feature_usage(feature_name, days=7)
    feedback = get_user_feedback(feature_name)
    
    return {
        "level": "continent",
        "users": usage.unique_users,
        "interactions": usage.total_interactions,
        "feedback": feedback.summary,
        "status": "ultimate_validation"
    }
```

**The Reality:** Both products at zero users. This tier doesn't exist yet. But the system should be ready.

---

## Automatic Tier Detection

### How the System Knows Which Tier to Use

```python
def detect_validation_tier(task):
    """Automatically determine appropriate validation level."""
    
    # Check file types changed
    files_changed = task.get_changed_files()
    
    # UI-only changes → Street level (localhost)
    if all(is_ui_file(f) for f in files_changed):
        return "street"
    
    # Backend with tests → Street level (container tests)
    if has_tests(task):
        return "street"
    
    # Session wrap-up OR task tagged "deploy" → City level (Render)
    if task.is_session_end or "deploy" in task.tags:
        return "city"
    
    # Explicitly tagged for app store → Country level
    if "app_store" in task.tags:
        return "country"
    
    # Default: City level (production validation)
    return "city"
```

---

## Session Wrap-Up Logic

### The Pattern: Expand → Contract → Wrap

**User's Words:**
> "Whatever we started in the session should wrap up in the session itself. But don't rush me."

**System Implementation:**

```python
class SessionManager:
    def __init__(self):
        self.active_tasks = []
        self.lit_pathways = {}
        
    def detect_session_phase(self):
        """Is user expanding or contracting?"""
        if len(self.active_tasks) > 3:
            return "expanding"  # Exploring, diverging
        elif len(self.active_tasks) == 1:
            return "contracting"  # Focusing, wrapping up
        return "stable"
    
    def should_suggest_wrap(self):
        """Only suggest wrap if clear tangible progress made."""
        if self.detect_session_phase() == "contracting":
            if all(task.has_tangible_progress() for task in self.active_tasks):
                return True
        return False
    
    def wrap_session(self):
        """Wrap session without rushing."""
        for task in self.active_tasks:
            # Save neural pathway (which files open, decisions made)
            self.lit_pathways[task.id] = capture_pathway(task)
            
            # Validate at appropriate tier
            tier = detect_validation_tier(task)
            result = validate(task, tier)
            
            # Save validation result
            task.validation = result
        
        # Don't say "Should we wrap up?"
        # Just say: "Session snapshot saved. [Summary of progress]"
        return session_summary(self.active_tasks)
```

---

## The Render Polling Solution (Critical)

### Problem:
> "I check Render 10 times over 40 minutes. The polling feature doesn't work properly."

### Solution:
**Background Render poller that actually works.**

```python
class RenderPoller:
    def __init__(self, render_api_key):
        self.api = RenderAPI(render_api_key)
        self.active_polls = {}
    
    async def start_poll(self, service_id, commit_sha):
        """Start polling for a deploy."""
        poll_id = f"{service_id}_{commit_sha}"
        
        task = asyncio.create_task(
            self._poll_loop(service_id, commit_sha)
        )
        self.active_polls[poll_id] = task
        
        return poll_id
    
    async def _poll_loop(self, service_id, commit_sha):
        """Poll Render API every 30 seconds until deploy succeeds."""
        attempts = 0
        max_attempts = 40  # 20 minutes max
        
        while attempts < max_attempts:
            try:
                deploy = self.api.get_latest_deploy(service_id)
                
                if deploy.commit == commit_sha:
                    if deploy.status == "live":
                        # SUCCESS: Deploy is live
                        await self._on_deploy_success(service_id, deploy)
                        break
                    elif deploy.status == "build_failed":
                        # FAILURE: Build failed
                        await self._on_deploy_failure(service_id, deploy)
                        break
                
                # Still deploying, wait and retry
                await asyncio.sleep(30)
                attempts += 1
                
            except Exception as e:
                logger.error(f"Render poll error: {e}")
                await asyncio.sleep(30)
                attempts += 1
    
    async def _on_deploy_success(self, service_id, deploy):
        """Deploy succeeded. Run smoke test and notify."""
        # Get the deployed URL
        url = self.api.get_service_url(service_id)
        
        # Run smoke test
        smoke_result = await self._smoke_test(url)
        
        # Notify user
        notify_user(
            title="🚀 Deploy Complete",
            message=f"Service is live at {url}",
            actions=[
                {"label": "Test Now", "url": url},
                {"label": "View Logs", "url": deploy.logs_url}
            ],
            result=smoke_result
        )
    
    async def _smoke_test(self, url):
        """Hit production endpoint to verify it's responsive."""
        try:
            response = await http_get(f"{url}/api/health")
            if response.status == 200:
                return {"status": "passed", "message": "Health check OK"}
            else:
                return {"status": "warning", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
```

---

## Feature Map (Combat Amnesia)

### Problem:
> "Many times I lose account of what features you have developed and how to test it out."

### Solution:
**Living feature inventory.**

```python
class FeatureMap:
    def __init__(self, brain_path):
        self.path = brain_path / "features.json"
        self.features = self._load()
    
    def add_feature(self, name, description, test_steps, deployed_at):
        """Register a new feature."""
        feature = {
            "id": generate_id(),
            "name": name,
            "description": description,
            "how_to_test": test_steps,
            "deployed_at": deployed_at,
            "status": "live",
            "last_validated": None,
            "tier": "city"  # Default to production
        }
        self.features.append(feature)
        self._save()
    
    def list_features(self, status=None):
        """Get all features, optionally filtered by status."""
        if status:
            return [f for f in self.features if f["status"] == status]
        return self.features
    
    def get_test_instructions(self, feature_name):
        """Show user how to test a specific feature."""
        feature = next(f for f in self.features if f["name"] == feature_name)
        return {
            "feature": feature["name"],
            "description": feature["description"],
            "steps": feature["how_to_test"],
            "url": f"https://gentlequest.onrender.com"  # Or from config
        }
```

---

## What "Tangible Progress" Means

### User's Words:
> "Something tangible should happen. Not just a lot of tools and food, but we can have substantial progress even if it's less than 1%."

**Translation:**
- Tangible = Can see it, click it, test it
- Doesn't have to be complete
- But must be measurable

**System Check:**
```python
def has_tangible_progress(task):
    """Did this task produce something testable?"""
    return any([
        task.has_deployed_url(),      # Can click and test
        task.has_screenshot(),         # Can see visual proof
        task.has_passing_tests(),      # Can verify logic
        task.has_documented_thinking() # Can understand decisions
    ])
```

---

## Technical Architecture

### Components Needed:

1. **Render Poller Service**
   - Background async task
   - Polls Render API every 30 seconds
   - Notifies on success/failure

2. **Tier Detector**
   - Analyzes changed files
   - Detects appropriate validation level
   - Auto-selects tier

3. **Feature Map**
   - JSON storage in `.brain/features.json`
   - Add/update/list features
   - Provide test instructions

4. **Session Manager**
   - Track expansion/contraction
   - Save neural pathways
   - Wrap sessions gracefully

5. **Notification System**
   - Send alerts when deploys complete
   - Show validation results
   - Provide clickable URLs

---

## Next: Design Translations for Parts 3 & 4
