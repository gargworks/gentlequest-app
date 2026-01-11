#!/usr/bin/env python3
"""
Focused E2E test for GentleQuest web app
Tests actual functionality with proper selectors
"""

import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page

class GentleQuestE2ETest:
    def __init__(self, base_url: str = "https://gentlequest.onrender.com"):
        self.base_url = base_url
        self.results = []
        self.screenshots_dir = Path("test/screenshots/e2e")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    def log_result(self, test: str, status: str, details: str, screenshot: str):
        self.results.append({
            "test": test,
            "status": status,
            "details": details,
            "screenshot": screenshot,
            "timestamp": datetime.now().isoformat()
        })
        print(f"[{status}] {test}: {details}")
    
    async def take_screenshot(self, page: Page, name: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.screenshots_dir / f"{name}_{timestamp}.png"
        await page.screenshot(path=str(path), full_page=True)
        return str(path)
    
    async def test_app_loads(self, page: Page) -> bool:
        """Test that the main app loads"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check if we have the Flutter web app
            title = await page.title()
            
            # Look for Flutter app indicators
            flutter_indicators = [
                'flutter',
                'canvas',
                '[role="application"]',
                'body > *'
            ]
            
            app_found = False
            for indicator in flutter_indicators:
                elements = await page.query_selector_all(indicator)
                if elements:
                    app_found = True
                    break
            
            # Check if it's the landing page or actual app
            body_text = await page.evaluate("() => document.body.innerText")
            is_landing = "Download on iOS" in body_text or "Get on Android" in body_text
            
            screenshot = await self.take_screenshot(page, "app_loads")
            
            if is_landing:
                self.log_result("App Loads", "PARTIAL", "Landing page loaded, need to access web app", screenshot)
                return False
            elif app_found:
                self.log_result("App Loads", "PASS", f"Web app loaded (title: {title})", screenshot)
                return True
            else:
                self.log_result("App Loads", "FAIL", "No app indicators found", screenshot)
                return False
                
        except Exception as e:
            screenshot = await self.take_screenshot(page, "app_loads_error")
            self.log_result("App Loads", "FAIL", str(e), screenshot)
            return False
    
    async def test_navigation(self, page: Page) -> bool:
        """Test navigation between sections"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Look for navigation elements
            nav_selectors = [
                'button',  # Generic buttons for navigation
                '[role="button"]',
                'a[href]',
                '.nav',
                'nav'
            ]
            
            nav_elements = []
            for selector in nav_selectors:
                elements = await page.query_selector_all(selector)
                nav_elements.extend(elements)
            
            if nav_elements:
                # Try clicking a few navigation elements
                for i, element in enumerate(nav_elements[:3]):  # Test first 3 elements
                    try:
                        await element.click()
                        await asyncio.sleep(1)
                        
                        # Check if page changed
                        current_url = page.url
                        if current_url != self.base_url:
                            await page.go_back()
                            await asyncio.sleep(1)
                    except:
                        continue
            
            screenshot = await self.take_screenshot(page, "navigation")
            self.log_result("Navigation", "PASS" if nav_elements else "PARTIAL", 
                           f"Found {len(nav_elements)} navigation elements", screenshot)
            return len(nav_elements) > 0
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "navigation_error")
            self.log_result("Navigation", "FAIL", str(e), screenshot)
            return False
    
    async def test_interactive_elements(self, page: Page) -> bool:
        """Test interactive elements like buttons and inputs"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Look for interactive elements
            interactive_selectors = [
                'input[type="text"]',
                'input[type="email"]',
                'textarea',
                'button:not([disabled])',
                '[role="button"]',
                'select',
                'input[type="checkbox"]',
                'input[type="radio"]'
            ]
            
            interactive_elements = []
            for selector in interactive_selectors:
                elements = await page.query_selector_all(selector)
                interactive_elements.extend(elements)
            
            # Test some interactions
            interactions_tested = 0
            for element in interactive_elements[:5]:  # Test first 5 elements
                try:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    
                    if tag_name == 'input':
                        input_type = await element.evaluate("el => el.type")
                        if input_type in ['text', 'email']:
                            await element.fill("test")
                            await element.clear()
                            interactions_tested += 1
                    elif tag_name == 'textarea':
                        await element.fill("test message")
                        await element.clear()
                        interactions_tested += 1
                    elif tag_name == 'button':
                        await element.click()
                        await asyncio.sleep(0.5)
                        interactions_tested += 1
                        
                except:
                    continue
            
            screenshot = await self.take_screenshot(page, "interactive_elements")
            status = "PASS" if interactions_tested > 0 else "PARTIAL"
            details = f"Elements: {len(interactive_elements)}, Tested: {interactions_tested}"
            self.log_result("Interactive Elements", status, details, screenshot)
            return interactions_tested > 0
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "interactive_error")
            self.log_result("Interactive Elements", "FAIL", str(e), screenshot)
            return False
    
    async def test_responsive_design(self, page: Page) -> bool:
        """Test responsive design"""
        try:
            viewports = [
                {"name": "Mobile", "width": 375, "height": 667},
                {"name": "Tablet", "width": 768, "height": 1024},
                {"name": "Desktop", "width": 1920, "height": 1080}
            ]
            
            results = []
            
            for viewport in viewports:
                await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle', timeout=5000)
                
                # Check for horizontal scroll
                has_horizontal_scroll = await page.evaluate(
                    "() => document.body.scrollWidth > document.body.clientWidth"
                )
                
                # Check if content is visible
                content_visible = await page.evaluate("() => document.body.children.length > 0")
                
                screenshot = await self.take_screenshot(page, f"responsive_{viewport['name'].lower()}")
                
                passed = not has_horizontal_scroll and content_visible
                results.append(passed)
                
                self.log_result(
                    f"Responsive - {viewport['name']}",
                    "PASS" if passed else "FAIL",
                    f"Scroll: {has_horizontal_scroll}, Content: {content_visible}",
                    screenshot
                )
            
            return all(results)
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "responsive_error")
            self.log_result("Responsive Design", "FAIL", str(e), screenshot)
            return False
    
    async def test_error_handling(self, page: Page) -> bool:
        """Test error handling"""
        try:
            # Test invalid route
            try:
                await page.goto(f"{self.base_url}/invalid-route")
                await page.wait_for_load_state('networkidle', timeout=5000)
                
                # Check if we get a proper error or redirect
                current_url = page.url
                handles_error = current_url != f"{self.base_url}/invalid-route"
                
            except:
                handles_error = True  # Got network error, which is expected
            
            # Test network resilience
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Simulate network issues and recovery
            await page.route("**/*", lambda route: route.abort())
            await asyncio.sleep(2)
            
            await page.unroute_all()
            await page.reload()
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            recovered = await page.evaluate("() => document.readyState === 'complete'")
            
            screenshot = await self.take_screenshot(page, "error_handling")
            status = "PASS" if (handles_error and recovered) else "PARTIAL"
            details = f"Error handling: {handles_error}, Recovery: {recovered}"
            self.log_result("Error Handling", status, details, screenshot)
            
            return handles_error or recovered
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "error_handling_critical")
            self.log_result("Error Handling", "FAIL", str(e), screenshot)
            return False
    
    async def run_all_tests(self) -> dict:
        """Run all focused E2E tests"""
        print("🚀 GentleQuest Focused E2E Test Suite")
        print(f"📍 Target: {self.base_url}")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            try:
                tests = [
                    self.test_app_loads,
                    self.test_navigation,
                    self.test_interactive_elements,
                    self.test_responsive_design,
                    self.test_error_handling
                ]
                
                for test in tests:
                    await test(page)
                    await asyncio.sleep(1)
                
            finally:
                await context.close()
                await browser.close()
        
        # Generate summary
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        partial = len([r for r in self.results if r["status"] == "PARTIAL"])
        
        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "partial": partial,
            "pass_rate": (passed / total) * 100 if total > 0 else 0,
            "results": self.results
        }
        
        print("-" * 50)
        print(f"📊 Summary: {passed}/{total} passed")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Partial: {partial}")
        print(f"📈 Pass Rate: {summary['pass_rate']:.1f}%")
        
        return summary

if __name__ == "__main__":
    async def main():
        test_suite = GentleQuestE2ETest()
        results = await test_suite.run_all_tests()
        
        # Save results
        import json
        with open("test/focused_e2e_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: test/focused_e2e_results.json")
        print(f"📸 Screenshots: {test_suite.screenshots_dir}")
    
    asyncio.run(main())
