# CI/CD Integration Guide for E2E Tests

## GitHub Actions Workflow

### Basic E2E Test Workflow

Create `.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Cache Playwright
      uses: actions/cache@v3
      with:
        path: ~/.cache/ms-playwright
        key: ${{ runner.os }}-playwright-${{ hashFiles('test/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-playwright-
          
    - name: Install dependencies
      run: |
        python3 -m pip install --upgrade pip
        pip install -r test/requirements.txt
        
    - name: Install Playwright browsers
      run: python3 -m playwright install chromium
      
    - name: Run E2E tests
      run: |
        cd test
        python3 focused_e2e_test.py
        
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: e2e-results
        path: |
          test/*.json
          test/screenshots/
        retention-days: 30
        
    - name: Upload screenshots to PR
      uses: actions/upload-artifact@v3
      if: failure() && github.event_name == 'pull_request'
      with:
        name: pr-screenshots
        path: test/screenshots/
        retention-days: 7
        
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          try {
            const results = JSON.parse(fs.readFileSync('test/focused_e2e_results.json', 'utf8'));
            const comment = `
            ## 🧪 E2E Test Results
            
            **Pass Rate:** ${results.pass_rate.toFixed(1)}%
            **Passed:** ${results.passed}/${results.total}
            **Failed:** ${results.failed}
            **Partial:** ${results.partial}
            
            [📊 View Detailed Report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
          } catch (error) {
            console.log('Could not read test results');
          }
```

### Advanced Workflow with Parallel Tests

```yaml
name: E2E Tests (Parallel)

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  e2e-matrix:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        test-suite: [focused, flutter, comprehensive]
        
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python3 -m pip install --upgrade pip
        pip install -r test/requirements.txt
        python3 -m playwright install chromium
        
    - name: Run ${{ matrix.test-suite }} tests
      run: |
        cd test
        python3 ${{ matrix.test-suite }}_e2e_test.py
        
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: e2e-${{ matrix.test-suite }}-results
        path: |
          test/*_e2e_results.json
          test/screenshots/
```

## Render Integration

### Automatic Testing on Deploy

Create `render-webhook.yaml`:

```yaml
services:
  - type: web
    name: gentlequest-e2e-tests
    env: python
    plan: free
    buildCommand: "pip install -r test/requirements.txt && python3 -m playwright install chromium"
    startCommand: "python3 test/focused_e2e_test.py"
    envVars:
      - key: TARGET_URL
        value: https://gentlequest.onrender.com
      - key: HEADLESS
        value: true
```

### Post-Deploy Hook

Add to your main app's `render.yaml`:

```yaml
services:
  - type: web
    name: gentlequest
    # ... your existing config
    
    # Add post-deploy hook
    hooks:
      - type: postDeploy
        command: "curl -X POST https://api.render.com/v1/services/${RENDER_SERVICE_ID}/jobs -H \"Authorization: Bearer $RENDER_API_KEY\" -d '{\"command\": \"cd /app && python3 test/focused_e2e_test.py\"}'"
```

## Docker Integration

### E2E Test Dockerfile

```dockerfile
# test/Dockerfile.e2e
FROM python:3.11-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy test files
COPY test/ ./test/
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r test/requirements.txt
RUN python3 -m playwright install chromium

# Run tests
CMD ["python3", "test/focused_e2e_test.py"]
```

### Docker Compose for Local Testing

```yaml
# docker-compose.e2e.yml
version: '3.8'

services:
  e2e-tests:
    build:
      context: .
      dockerfile: test/Dockerfile.e2e
    environment:
      - TARGET_URL=http://web:8000
      - HEADLESS=true
    depends_on:
      - web
    volumes:
      - ./test/screenshots:/app/test/screenshots
      
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=testing
```

## Monitoring and Alerting

### Slack Integration

```yaml
# Add to GitHub Actions
    - name: Notify Slack on Failure
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        channel: '#testing'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        text: |
          🚨 E2E Tests Failed!
          Repository: ${{ github.repository }}
          Branch: ${{ github.ref }}
          Commit: ${{ github.sha }}
          Run: ${{ github.run_id }}
```

### Email Notifications

```yaml
    - name: Send email report
      if: always()
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.gmail.com
        server_port: 587
        username: ${{ secrets.EMAIL_USERNAME }}
        password: ${{ secrets.EMAIL_PASSWORD }}
        subject: "E2E Test Results - ${{ job.status }}"
        body: |
          E2E tests completed with status: ${{ job.status }}
          
          View details: https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}
        to: ${{ secrets.NOTIFICATION_EMAIL }}
        from: "E2E Tests <tests@gentlequest.app>"
```

## Performance Monitoring

### Lighthouse CI Integration

```yaml
    - name: Run Lighthouse CI
      run: |
        npm install -g @lhci/cli@0.12.x
        lhci autorun
      env:
        LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

### Performance Budget

Create `lighthouserc.js`:

```javascript
module.exports = {
  ci: {
    collect: {
      url: ['https://gentlequest.onrender.com'],
      numberOfRuns: 3
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', {minScore: 0.8}],
        'categories:accessibility': ['error', {minScore: 0.9}],
        'categories:best-practices': ['warn', {minScore: 0.8}],
        'categories:seo': ['warn', {minScore: 0.8}]
      }
    },
    upload: {
      target: 'temporary-public-storage'
    }
  }
};
```

## Visual Regression Testing

### Percy Integration

```python
# Add to test files
import percy

percy_runner = percy.Runner(loader=percy.ResourceLoader(
    root_dir='test/screenshots',
    base_url='https://gentlequest.onrender.com'
))

async def take_screenshot_with_percy(page, name):
    await page.screenshot(path=f"test/screenshots/{name}.png")
    percy_runner.snapshot(name, widths=[375, 768, 1280])
```

### BackstopJS Configuration

```json
{
  "id": "gentlequest_e2e",
  "viewports": [
    {
      "label": "mobile",
      "width": 375,
      "height": 667
    },
    {
      "label": "tablet",
      "width": 768,
      "height": 1024
    },
    {
      "label": "desktop",
      "width": 1280,
      "height": 800
    }
  ],
  "scenarios": [
    {
      "label": "Homepage",
      "url": "https://gentlequest.onrender.com",
      "delay": 1000
    }
  ],
  "paths": {
    "bitmaps_reference": "test/backstop/reference",
    "bitmaps_test": "test/backstop/test",
    "html_report": "test/backstop/report"
  }
}
```

## Environment Configuration

### Environment Variables

```bash
# .env.test
TARGET_URL=https://gentlequest.onrender.com
HEADLESS=true
TIMEOUT=30000
RETRY_COUNT=3
PARALLEL_WORKERS=2
SLACK_WEBHOOK=${SLACK_WEBHOOK}
NOTIFICATION_EMAIL=${NOTIFICATION_EMAIL}
```

### Multi-Environment Testing

```python
# test/config.py
import os

class TestConfig:
    ENVIRONMENTS = {
        'development': {
            'base_url': 'http://localhost:5000',
            'headless': False,
            'timeout': 10000
        },
        'staging': {
            'base_url': 'https://staging.gentlequest.app',
            'headless': True,
            'timeout': 20000
        },
        'production': {
            'base_url': 'https://gentlequest.onrender.com',
            'headless': True,
            'timeout': 30000
        }
    }
    
    @classmethod
    def get_config(cls, env=None):
        env = env or os.getenv('TEST_ENV', 'production')
        return cls.ENVIRONMENTS[env]
```

## Security Considerations

### Secrets Management

```yaml
# GitHub Actions secrets
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- SLACK_WEBHOOK
- NOTIFICATION_EMAIL
- LHCI_GITHUB_APP_TOKEN
```

### Test Data Security

```python
# Use test-specific data
TEST_USER = {
    'email': 'test@example.com',
    'password': 'test-password-123'
}

# Sanitize screenshots
async def sanitize_screenshot(page):
    # Remove sensitive information
    await page.evaluate("""
        // Remove any sensitive elements
        document.querySelectorAll('[data-sensitive]').forEach(el => el.remove());
    """)
```

## Rollback Strategy

### Automated Rollback on Test Failure

```yaml
    - name: Rollback on E2E Failure
      if: failure() && github.ref == 'refs/heads/main'
      run: |
        echo "E2E tests failed, initiating rollback..."
        # Get previous successful deployment
        PREVIOUS_DEPLOY=$(curl -s "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys?limit=2" | jq '.[1].id')
        # Rollback to previous deploy
        curl -X POST "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys/${PREVIOUS_DEPLOY}/restore" \
          -H "Authorization: Bearer $RENDER_API_KEY"
```

---

This comprehensive CI/CD integration guide provides everything needed to automate E2E testing in production environments.
