# E2E Test Troubleshooting Guide

## Common Issues and Solutions

### 🚨 Flutter Elements Not Found

**Problem:** Tests can't find Flutter widgets with standard CSS selectors

**Symptoms:**
- `No chat elements found`
- `No mood elements found`
- `Bottom navigation not found`

**Solutions:**
1. **Add Test IDs to Flutter Widgets**
   ```dart
   // In your Flutter code
   Key('chat-input-button')
   Key('mood-tracker')
   Key('bottom-nav')
   ```

2. **Use Flutter-Specific Selectors**
   ```python
   # Instead of CSS selectors
   await page.locator('flt-glass-pane').click()
   await page.locator('[role="button"]').click()
   ```

3. **Wait for Flutter App Load**
   ```python
   await page.wait_for_function(
       "() => window._flutter || document.querySelector('flutter-view')"
   )
   ```

### 🖼️ Screenshots Fail

**Problem:** Screenshot timeout or capture issues

**Symptoms:**
- `Timeout 30000ms exceeded`
- Blank screenshots

**Solutions:**
1. **Increase Timeout**
   ```python
   await page.screenshot(path="test.png", timeout=60000)
   ```

2. **Wait for Load State**
   ```python
   await page.wait_for_load_state('networkidle')
   await page.screenshot(path="test.png")
   ```

3. **Check App Loading**
   ```python
   # Ensure app is fully loaded before screenshot
   await page.wait_for_function("() => document.readyState === 'complete'")
   ```

### 🌐 Browser Fails to Start

**Problem:** Playwright browser launch issues

**Symptoms:**
- `Browser launch failed`
- `Chromium not found`

**Solutions:**
1. **Reinstall Playwright Browsers**
   ```bash
   python3 -m playwright install chromium
   ```

2. **Use System Browser**
   ```python
   browser = await p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
   ```

3. **Check Permissions**
   ```bash
   # On macOS, allow screen recording for Terminal
   # System Preferences > Security & Privacy > Privacy > Screen Recording
   ```

### 🐌 Slow Test Performance

**Problem:** Tests running slowly

**Symptoms:**
- Tests taking >30 seconds
- Timeouts on simple operations

**Solutions:**
1. **Remove Slow-Mo in Production**
   ```python
   browser = await p.chromium.launch(slow_mo=0)  # Remove slow_mo
   ```

2. **Optimize Waits**
   ```python
   # Use specific waits instead of fixed sleep
   await page.wait_for_selector('#element')  # Better than sleep(3)
   ```

3. **Run Headless**
   ```python
   browser = await p.chromium.launch(headless=True)
   ```

### 📱 Responsive Test Failures

**Problem:** Responsive tests failing on different viewports

**Symptoms:**
- `hasHorizontalScroll: True`
- Canvas doesn't adapt

**Solutions:**
1. **Check Flutter Responsive Implementation**
   ```dart
   // Ensure your Flutter app uses responsive design
   MediaQuery.of(context).size.width
   LayoutBuilder(builder: (context, constraints) => ...)
   ```

2. **Wait for Resize**
   ```python
   await page.set_viewport_size({"width": 375, "height": 667})
   await page.wait_for_timeout(1000)  # Wait for resize to complete
   ```

### 🔗 Network Issues

**Problem:** Tests failing due to network problems

**Symptoms:**
- `net::ERR_FAILED`
- `Timeout 5000ms exceeded`

**Solutions:**
1. **Check App URL**
   ```bash
   curl -I https://gentlequest.onrender.com
   ```

2. **Increase Network Timeout**
   ```python
   await page.goto(url, timeout=30000)
   ```

3. **Use Wait for Navigation**
   ```python
   await page.goto(url, wait_until="networkidle")
   ```

### 🧪 Test Environment Issues

**Problem:** Virtual environment or dependency issues

**Symptoms:**
- `ModuleNotFoundError: No module named 'playwright'`
- `externally-managed-environment`

**Solutions:**
1. **Create Fresh Virtual Environment**
   ```bash
   python3 -m venv test_env
   source test_env/bin/activate
   pip install -r test/requirements.txt
   ```

2. **Use Python 3.11**
   ```bash
   python3.11 -m venv test_env  # More compatible than 3.14
   ```

3. **Install Playwright System-wide**
   ```bash
   pip install --user playwright
   playwright install chromium
   ```

## Debug Mode

### Enable Verbose Logging
```python
# Add to test setup
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Single Test
```bash
# Run specific test for debugging
python3 -c "
import asyncio
from focused_e2e_test import GentleQuestE2ETest
async def debug():
    suite = GentleQuestE2ETest()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        await suite.test_app_loads(page)
        await browser.close()
asyncio.run(debug())
"
```

### Visual Debug Mode
```python
# Run with visible browser
browser = await p.chromium.launch(
    headless=False,
    slow_mo=2000,
    devtools=True  # Open DevTools
)
```

## Quick Fixes Checklist

- [ ] Run `python3 -m playwright install chromium`
- [ ] Check if app URL is accessible in browser
- [ ] Verify virtual environment is activated
- [ ] Test with headless=False for visual debugging
- [ ] Check for Flutter app loading completion
- [ ] Increase timeouts for slow operations
- [ ] Verify test selectors match actual elements

## Getting Help

1. **Check Screenshots:** Look at `test/screenshots/e2e/` to see what tests are seeing
2. **Run Simple Test:** Start with `test/simple_e2e_test.py` to verify basic setup
3. **Check Logs:** Look at browser console for JavaScript errors
4. **Manual Test:** Try the same actions manually in browser

## Performance Tips

- Use `headless=True` for CI/CD
- Remove `slow_mo` for production runs
- Use specific waits instead of `sleep()`
- Run tests in parallel where possible
- Cache Playwright browser installation
