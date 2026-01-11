#!/usr/bin/env python3
"""
Flutter Web Specific E2E Test for GentleQuest
Tests Flutter-specific features and components
"""

import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page

class FlutterWebE2ETest:
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
    
    async def wait_for_flutter_app(self, page: Page, timeout: int = 15000) -> bool:
        """Wait for Flutter app to fully load"""
        try:
            # Wait for Flutter app indicators
            await page.wait_for_function(
                """() => {
                    // Check for Flutter web app
                    return (
                        window._flutter || 
                        document.querySelector('flutter-view') ||
                        document.querySelector('flt-glass-pane') ||
                        document.querySelector('[role="application"]') ||
                        document.querySelector('canvas')
                    );
                }""",
                timeout=timeout
            )
            return True
        except:
            return False
    
    async def test_flutter_app_structure(self, page: Page) -> bool:
        """Test Flutter app structure and components"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait for Flutter app to load
            flutter_loaded = await self.wait_for_flutter_app(page)
            
            # Check for Flutter-specific elements
            flutter_elements = [
                'flutter-view',
                'flt-glass-pane',
                'flt-scene',
                '[role="application"]',
                'canvas',
                '.flutter'
            ]
            
            found_elements = []
            for element in flutter_elements:
                try:
                    elements = await page.query_selector_all(element)
                    if elements:
                        found_elements.extend(elements)
                except:
                    continue
            
            # Check for Flutter app in window object
            flutter_app = await page.evaluate("() => window._flutter || window.flutter")
            
            screenshot = await self.take_screenshot(page, "flutter_structure")
            
            if flutter_loaded and (found_elements or flutter_app):
                details = f"Flutter loaded: {flutter_loaded}, Elements: {len(found_elements)}, App object: {bool(flutter_app)}"
                self.log_result("Flutter App Structure", "PASS", details, screenshot)
                return True
            else:
                self.log_result("Flutter App Structure", "PARTIAL", "App loaded but Flutter indicators not found", screenshot)
                return False
                
        except Exception as e:
            screenshot = await self.take_screenshot(page, "flutter_structure_error")
            self.log_result("Flutter App Structure", "FAIL", str(e), screenshot)
            return False
    
    async def test_bottom_navigation(self, page: Page) -> bool:
        """Test bottom navigation bar (common in Flutter apps)"""
        try:
            await page.goto(self.base_url)
            await self.wait_for_flutter_app(page)
            
            # Look for bottom navigation
            bottom_nav_selectors = [
                '.bottom-navigation',
                '[data-testid="bottom-nav"]',
                'nav[role="navigation"]',
                '.nav-bar',
                'div[style*="position: fixed"][style*="bottom"]'
            ]
            
            bottom_nav = None
            for selector in bottom_nav_selectors:
                try:
                    bottom_nav = await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            if bottom_nav:
                # Look for navigation items
                nav_items = await bottom_nav.query_selector_all('button, [role="button"], a, div')
                
                # Try clicking nav items
                clicked_items = 0
                for i, item in enumerate(nav_items[:3]):  # Test first 3 items
                    try:
                        await item.click()
                        await asyncio.sleep(1)
                        clicked_items += 1
                    except:
                        continue
            
            screenshot = await self.take_screenshot(page, "bottom_navigation")
            
            if bottom_nav and nav_items:
                details = f"Bottom nav found: {bool(bottom_nav)}, Items: {len(nav_items)}, Clicked: {clicked_items}"
                self.log_result("Bottom Navigation", "PASS", details, screenshot)
                return True
            else:
                self.log_result("Bottom Navigation", "PARTIAL", "Bottom navigation not found", screenshot)
                return False
                
        except Exception as e:
            screenshot = await self.take_screenshot(page, "bottom_navigation_error")
            self.log_result("Bottom Navigation", "FAIL", str(e), screenshot)
            return False
    
    async def test_chat_interface(self, page: Page) -> bool:
        """Test chat interface if present"""
        try:
            await page.goto(self.base_url)
            await self.wait_for_flutter_app(page)
            
            # Look for chat-related elements
            chat_selectors = [
                '[data-testid*="chat"]',
                '.chat',
                '.conversation',
                'textarea',
                'input[type="text"]',
                'button:has-text("Send")',
                'button:has-text("send")'
            ]
            
            chat_elements = []
            for selector in chat_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    chat_elements.extend(elements)
                except:
                    continue
            
            # Try to interact with chat if found
            interaction_success = False
            if chat_elements:
                for element in chat_elements:
                    try:
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        if tag_name in ['input', 'textarea']:
                            await element.fill("Hello")
                            await element.clear()
                            interaction_success = True
                            break
                    except:
                        continue
            
            screenshot = await self.take_screenshot(page, "chat_interface")
            
            if chat_elements:
                details = f"Chat elements: {len(chat_elements)}, Interaction: {interaction_success}"
                self.log_result("Chat Interface", "PASS", details, screenshot)
                return True
            else:
                self.log_result("Chat Interface", "PARTIAL", "No chat elements found", screenshot)
                return False
                
        except Exception as e:
            screenshot = await self.take_screenshot(page, "chat_interface_error")
            self.log_result("Chat Interface", "FAIL", str(e), screenshot)
            return False
    
    async def test_mood_tracking_ui(self, page: Page) -> bool:
        """Test mood tracking UI elements"""
        try:
            await page.goto(self.base_url)
            await self.wait_for_flutter_app(page)
            
            # Look for mood-related elements
            mood_selectors = [
                '[data-testid*="mood"]',
                '.mood',
                '.emoji',
                'button:has-text("😢")',
                'button:has-text("😊")',
                '.feeling',
                '.emotion'
            ]
            
            mood_elements = []
            for selector in mood_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    mood_elements.extend(elements)
                except:
                    continue
            
            # Try clicking mood elements
            interactions = 0
            for element in mood_elements[:3]:  # Test first 3
                try:
                    await element.click()
                    await asyncio.sleep(0.5)
                    interactions += 1
                except:
                    continue
            
            screenshot = await self.take_screenshot(page, "mood_tracking_ui")
            
            if mood_elements:
                details = f"Mood elements: {len(mood_elements)}, Interactions: {interactions}"
                self.log_result("Mood Tracking UI", "PASS", details, screenshot)
                return True
            else:
                self.log_result("Mood Tracking UI", "PARTIAL", "No mood elements found", screenshot)
                return False
                
        except Exception as e:
            screenshot = await self.take_screenshot(page, "mood_tracking_error")
            self.log_result("Mood Tracking UI", "FAIL", str(e), screenshot)
            return False
    
    async def test_responsive_flutter(self, page: Page) -> bool:
        """Test Flutter app responsiveness"""
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
                
                # Wait for Flutter app
                flutter_loaded = await self.wait_for_flutter_app(page, timeout=10000)
                
                # Check if app adapts
                app_adapts = await page.evaluate(
                    """() => {
                        const body = document.body;
                        const hasHorizontalScroll = body.scrollWidth > body.clientWidth;
                        const hasContent = body.children.length > 0;
                        const canvas = document.querySelector('canvas');
                        const canvasAdapts = canvas ? (canvas.width === window.innerWidth) : false;
                        return !hasHorizontalScroll && hasContent && canvasAdapts;
                    }"""
                )
                
                screenshot = await self.take_screenshot(page, f"flutter_responsive_{viewport['name'].lower()}")
                results.append(app_adapts)
                
                self.log_result(
                    f"Flutter Responsive - {viewport['name']}",
                    "PASS" if app_adapts else "FAIL",
                    f"Flutter loaded: {flutter_loaded}, Adapts: {app_adapts}",
                    screenshot
                )
            
            return all(results)
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "flutter_responsive_error")
            self.log_result("Flutter Responsive", "FAIL", str(e), screenshot)
            return False
    
    async def run_flutter_tests(self) -> dict:
        """Run all Flutter-specific tests"""
        print("🎯 Flutter Web E2E Test Suite")
        print(f"📍 Target: {self.base_url}")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            try:
                tests = [
                    self.test_flutter_app_structure,
                    self.test_bottom_navigation,
                    self.test_chat_interface,
                    self.test_mood_tracking_ui,
                    self.test_responsive_flutter
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
        print(f"📊 Flutter Tests: {passed}/{total} passed")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Partial: {partial}")
        print(f"📈 Pass Rate: {summary['pass_rate']:.1f}%")
        
        return summary

if __name__ == "__main__":
    async def main():
        test_suite = FlutterWebE2ETest()
        results = await test_suite.run_flutter_tests()
        
        # Save results
        import json
        with open("test/flutter_e2e_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: test/flutter_e2e_results.json")
        print(f"📸 Screenshots: {test_suite.screenshots_dir}")
    
    asyncio.run(main())
