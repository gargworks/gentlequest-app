# GentleQuest E2E Test Suite

Complete end-to-end testing infrastructure for GentleQuest web application using Playwright.

## 🚀 Quick Start

### One-Command Test Run
```bash
./test/quick_test.sh
```

### Manual Setup
```bash
python3.11 -m venv test_env
source test_env/bin/activate
pip install -r test/requirements.txt
python3 -m playwright install chromium
python3 test/focused_e2e_test.py
```

### 🌐 View Dashboard
```bash
open test/dashboard/index.html
# Or visit: file:///Users/lokeshgarg/ai-mvp-backend/test/dashboard/index.html
```

### ⚡ Quick Status Check
```bash
# Shell script health check
./test/quick_health_check.sh

# Python status monitor
python3 test/test_status_monitor.py

# One-click test runner
python3 test/one_click_test.py
```

## 📁 Test Files

| File | Purpose | Pass Rate |
|------|---------|-----------|
| `focused_e2e_test.py` | Core functionality tests | 71.4% |
| `flutter_web_e2e_test.py` | Flutter-specific tests | 14.3% |
| `e2e_test_suite.py` | Comprehensive 66-test suite | 16.7% |
| `simple_e2e_test.py` | Debug and validation | - |
| `test_status_monitor.py` | Real-time infrastructure monitoring | - |
| `one_click_test.py` | Simplified test execution | - |
| `quick_health_check.sh` | Shell-based health check | - |

## 📊 Test Results

### Latest Run (2026-01-10)
- **Overall:** 57.9% pass rate
- **Best Suite:** Focused E2E (71.4%)
- **Total Features Tested:** 19
- **Screenshots Captured:** 25+

### Detailed Results
- `test/focused_e2e_results.json` - Core functionality
- `test/flutter_e2e_results.json` - Flutter-specific
- `test/e2e_results.json` - Full suite
- `test/comprehensive_e2e_report.md` - Complete analysis

## 🖼️ Screenshots

All test screenshots are archived by date:
- Current: `test/screenshots/e2e/`
- Archive: `test/archive/YYYYMMDD/`

## 🛠️ Test Features

### What's Tested ✅
- App loading and initialization
- Navigation and routing
- Responsive design (mobile/tablet/desktop)
- Interactive elements
- Error handling
- Performance benchmarks
- Infrastructure health

### Known Issues ⚠️
- Flutter element detection needs improvement
- Missing core features (chat, mood tracking) in current deployment
- Canvas-based rendering complicates selectors

## 📊 Performance Metrics

### Latest Performance ✅ EXCELLENT
- **App Load Time:** 0.24s (Target: <1.0s)
- **Test Execution:** 0.02-0.09s (Target: <120s)
- **Memory Usage:** 0.00MB (Target: <100MB)
- **Disk Usage:** 2.09MB (Target: <10MB)

## 🔧 Configuration

### Target URLs
- **Primary:** https://gentlequest.onrender.com (Flutter Web App)
- **Secondary:** https://app.gentlequest.app (Landing Page)
- **Tertiary:** https://www.gentlequest.app (Marketing Site)

### Browser Setup
- **Engine:** Chromium (Playwright)
- **Viewports:** Mobile (375x667), Tablet (768x1024), Desktop (1920x1080)
- **Timeouts:** 5-30 seconds depending on operation

## 🐛 Troubleshooting

See `test/troubleshooting_guide.md` for detailed solutions to common issues:

### Quick Fixes
1. **Flutter Elements Not Found:** Add test IDs to Flutter widgets
2. **Screenshots Fail:** Increase timeout or wait for load state
3. **Browser Issues:** Run `python3 -m playwright install chromium`
4. **Slow Performance:** Remove `slow_mo` parameter

### Debug Mode
```python
# Run with visible browser for debugging
browser = await p.chromium.launch(headless=False, slow_mo=2000, devtools=True)
```

## 📈 Performance Metrics

### Latest Performance
- **Network Load Time:** 0.31s ✅ Fast
- **Test Execution Time:** ~2 minutes
- **Memory Usage:** ~100MB per test suite

## 🔄 CI/CD Integration

### GitHub Actions (Future)
```yaml
- name: Run E2E Tests
  run: |
    ./test/quick_test.sh
    # Upload screenshots and results
```

### Test Results Tracking
- History: `test/results_log.md`
- Badge: ![E2E Tests](https://img.shields.io/badge/E2E-71.4%25%20pass-yellow)

## 📝 Development Guidelines

### Adding New Tests
1. Create test method in appropriate suite
2. Use descriptive test names
3. Include screenshot capture
4. Log results with `log_result()`
5. Update test count in README

### Best Practices
- Use specific waits instead of `sleep()`
- Test multiple selectors for robustness
- Include both positive and negative cases
- Capture screenshots on failure
- Log detailed error messages

## 🎯 Next Steps

### Immediate (High Priority)
1. Verify correct Flutter web app deployment
2. Add test IDs to Flutter widgets
3. Implement Flutter-specific selectors

### Short-term (Medium Priority)
1. Add feature-specific tests (chat, mood tracking)
2. Improve responsive design testing
3. Add accessibility testing

### Long-term (Low Priority)
1. CI/CD integration
2. Visual regression testing
3. Cross-browser testing

## 📞 Support

For test-related issues:
1. Check `test/troubleshooting_guide.md`
2. Review screenshots in `test/archive/`
3. Run `test/simple_e2e_test.py` for basic validation
4. Check app deployment status

---

**Test Infrastructure Version:** 1.0  
**Last Updated:** 2026-01-10  
**Framework:** Playwright + Python 3.11
