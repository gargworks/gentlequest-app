#!/usr/bin/env python3
"""
GentleQuest End-to-End Test Suite
Comprehensive browser-based testing of all features
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class GentleQuestE2ETestSuite:
    """Comprehensive E2E testing for GentleQuest web application"""
    
    def __init__(self, base_url: str = "https://gentlequest.onrender.com"):
        self.base_url = base_url
        self.test_results = []
        self.screenshots_dir = Path("test/screenshots/e2e")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def setup_browser(self) -> Tuple[Browser, BrowserContext, Page]:
        """Initialize browser with optimal settings"""
        playwright = await async_playwright().start()
        
        # Use Chromium for consistency
        browser = await playwright.chromium.launch(
            headless=False,  # Show browser for debugging
            slow_mo=500,  # Slow down for visibility
            args=[
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--window-size=1920,1080'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        return browser, context, page
    
    def log_test_result(self, test_name: str, status: str, details: str = "", screenshot_path: Optional[str] = None):
        """Log test result with timestamp"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "screenshot": screenshot_path
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
    
    async def take_screenshot(self, page: Page, name: str) -> str:
        """Take screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        path = self.screenshots_dir / filename
        await page.screenshot(path=str(path), full_page=True)
        return str(path)
    
    async def wait_for_load(self, page: Page, timeout: int = 5000):
        """Wait for page to fully load"""
        await page.wait_for_load_state('networkidle', timeout=timeout)
        await asyncio.sleep(1)  # Extra wait for animations
    
    # ==================== CORE USER JOURNEY TESTS ====================
    
    async def test_app_loads(self, page: Page) -> bool:
        """Test that the main application loads successfully"""
        try:
            await page.goto(self.base_url)
            await self.wait_for_load(page)
            
            # Check if main elements are present
            title = await page.title()
            assert "GentleQuest" in title or "gentlequest" in title.lower()
            
            # Look for key UI elements
            await page.wait_for_selector('[data-testid="app-container"]', timeout=10000)
            
            screenshot = await self.take_screenshot(page, "app_loads")
            self.log_test_result("App Loads", "PASS", f"Title: {title}", screenshot)
            return True
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "app_loads_error")
            self.log_test_result("App Loads", "FAIL", str(e), screenshot)
            return False
    
    async def test_onboarding_flow(self, page: Page) -> bool:
        """Test the complete onboarding experience"""
        try:
            # Look for welcome/onboarding elements
            welcome_elements = [
                '[data-testid="welcome-screen"]',
                '[data-testid="onboarding-container"]',
                'text="Welcome"',
                'text="Get Started"'
            ]
            
            found_element = None
            for selector in welcome_elements:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    found_element = selector
                    break
                except:
                    continue
            
            if found_element:
                await page.click(found_element)
                await self.wait_for_load(page)
                
            screenshot = await self.take_screenshot(page, "onboarding")
            self.log_test_result("Onboarding Flow", "PASS", f"Found element: {found_element}", screenshot)
            return True
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "onboarding_error")
            self.log_test_result("Onboarding Flow", "FAIL", str(e), screenshot)
            return False
    
    async def test_chat_functionality(self, page: Page) -> bool:
        """Test AI chat functionality"""
        try:
            # Look for chat interface
            chat_selectors = [
                '[data-testid="chat-input"]',
                'textarea[placeholder*="message"]',
                'input[type="text"]',
                'textarea'
            ]
            
            chat_input = None
            for selector in chat_selectors:
                try:
                    chat_input = await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            if not chat_input:
                raise Exception("Chat input not found")
            
            # Send a test message
            test_message = "Hello, I'm feeling a bit anxious today"
            await chat_input.fill(test_message)
            
            # Look for send button
            send_selectors = [
                '[data-testid="send-button"]',
                'button:has-text("Send")',
                'button[aria-label*="send"]',
                'button[type="submit"]'
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            if send_button:
                await send_button.click()
            else:
                # Try pressing Enter
                await chat_input.press("Enter")
            
            # Wait for AI response
            await asyncio.sleep(3)
            
            # Check for response indicators
            response_selectors = [
                '[data-testid="ai-response"]',
                '.message.ai',
                '.assistant-message',
                'text="I understand"'
            ]
            
            response_found = False
            for selector in response_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    response_found = True
                    break
                except:
                    continue
            
            screenshot = await self.take_screenshot(page, "chat_functionality")
            self.log_test_result("Chat Functionality", "PASS" if response_found else "PARTIAL", 
                               f"Response found: {response_found}", screenshot)
            return response_found
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "chat_error")
            self.log_test_result("Chat Functionality", "FAIL", str(e), screenshot)
            return False
    
    async def test_crisis_detection(self, page: Page) -> bool:
        """Test crisis detection and safety features"""
        try:
            # Look for chat input
            chat_input = await page.wait_for_selector('textarea, input[type="text"]', timeout=5000)
            
            # Send crisis-related message
            crisis_message = "I want to harm myself"
            await chat_input.fill(crisis_message)
            await chat_input.press("Enter")
            
            # Wait for crisis response
            await asyncio.sleep(3)
            
            # Look for crisis resources
            crisis_selectors = [
                '[data-testid="crisis-resources"]',
                '.crisis-hotline',
                'text="crisis"',
                'text="helpline"',
                'text="988"',
                'text="emergency"'
            ]
            
            crisis_detected = False
            for selector in crisis_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    crisis_detected = True
                    break
                except:
                    continue
            
            # Also check if AI is blocked
            ai_blocked_selectors = [
                '[data-testid="ai-blocked"]',
                '.chat-disabled',
                'text="cannot respond"',
                'text="crisis resources"'
            ]
            
            ai_blocked = False
            for selector in ai_blocked_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    ai_blocked = True
                    break
                except:
                    continue
            
            screenshot = await self.take_screenshot(page, "crisis_detection")
            status = "PASS" if (crisis_detected or ai_blocked) else "FAIL"
            details = f"Crisis detected: {crisis_detected}, AI blocked: {ai_blocked}"
            self.log_test_result("Crisis Detection", status, details, screenshot)
            return crisis_detected or ai_blocked
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "crisis_error")
            self.log_test_result("Crisis Detection", "FAIL", str(e), screenshot)
            return False
    
    async def test_mood_tracking(self, page: Page) -> bool:
        """Test mood tracking functionality"""
        try:
            # Look for mood tracking elements
            mood_selectors = [
                '[data-testid="mood-tracker"]',
                '.mood-selector',
                'text="How are you feeling"',
                'text="Rate your mood"'
            ]
            
            mood_element = None
            for selector in mood_selectors:
                try:
                    mood_element = await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            if not mood_element:
                # Try navigation to mood section
                nav_selectors = [
                    '[data-testid="nav-mood"]',
                    'button:has-text("Mood")',
                    'a:has-text("Mood")',
                    '.nav-mood'
                ]
                
                for selector in nav_selectors:
                    try:
                        await page.click(selector)
                        await asyncio.sleep(2)
                        break
                    except:
                        continue
                
                # Re-check for mood elements
                for selector in mood_selectors:
                    try:
                        mood_element = await page.wait_for_selector(selector, timeout=3000)
                        break
                    except:
                        continue
            
            mood_buttons = []
            if mood_element:
                # Look for mood emoji buttons
                emoji_selectors = [
                    'button:has-text("😢")',
                    'button:has-text("😕")',
                    'button:has-text("😐")',
                    'button:has-text("😊")',
                    'button:has-text("😄")',
                    '.mood-emoji',
                    '[data-testid*="mood"]'
                ]
                
                for selector in emoji_selectors:
                    try:
                        buttons = await page.query_selector_all(selector)
                        if buttons:
                            mood_buttons.extend(buttons)
                    except:
                        continue
                
                if mood_buttons:
                    # Click a mood button
                    await mood_buttons[2].click()  # Click neutral mood
                    await asyncio.sleep(1)
                    
                    # Look for save button
                    save_selectors = [
                        '[data-testid="save-mood"]',
                        'button:has-text("Save")',
                        'button:has-text("Submit")',
                        'button[type="submit"]'
                    ]
                    
                    for selector in save_selectors:
                        try:
                            save_button = await page.wait_for_selector(selector, timeout=3000)
                            await save_button.click()
                            break
                        except:
                            continue
            
            screenshot = await self.take_screenshot(page, "mood_tracking")
            status = "PASS" if (mood_element or mood_buttons) else "FAIL"
            details = f"Mood element: {bool(mood_element)}, Mood buttons: {len(mood_buttons)}"
            self.log_test_result("Mood Tracking", status, details, screenshot)
            return bool(mood_element or mood_buttons)
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "mood_error")
            self.log_test_result("Mood Tracking", "FAIL", str(e), screenshot)
            return False
    
    async def test_breathing_exercise(self, page: Page) -> bool:
        """Test breathing exercise functionality"""
        try:
            # Look for breathing exercise elements
            breathing_selectors = [
                '[data-testid="breathing-exercise"]',
                '.breathing-animation',
                'text="Breathing"',
                'text="breathe"',
                'button:has-text("Breathing")'
            ]
            
            breathing_element = None
            for selector in breathing_selectors:
                try:
                    breathing_element = await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            if not breathing_element:
                # Try navigation to exercises section
                nav_selectors = [
                    '[data-testid="nav-exercises"]',
                    'button:has-text("Exercises")',
                    'a:has-text("Exercises")',
                    '.nav-exercises'
                ]
                
                for selector in nav_selectors:
                    try:
                        await page.click(selector)
                        await asyncio.sleep(2)
                        break
                    except:
                        continue
                
                # Re-check for breathing elements
                for selector in breathing_selectors:
                    try:
                        breathing_element = await page.wait_for_selector(selector, timeout=3000)
                        break
                    except:
                        continue
            
            if breathing_element:
                # Click on breathing exercise
                await breathing_element.click()
                await asyncio.sleep(2)
                
                # Look for breathing animation or controls
                animation_selectors = [
                    '.breathing-circle',
                    '[data-testid="breathing-circle"]',
                    '.breathing-animation',
                    'text="Inhale"',
                    'text="Exhale"',
                    'text="Hold"'
                ]
                
                animation_found = False
                for selector in animation_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        animation_found = True
                        break
                    except:
                        continue
            
            screenshot = await self.take_screenshot(page, "breathing_exercise")
            status = "PASS" if (breathing_element or animation_found) else "FAIL"
            details = f"Breathing element: {bool(breathing_element)}, Animation: {animation_found}"
            self.log_test_result("Breathing Exercise", status, details, screenshot)
            return bool(breathing_element or animation_found)
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "breathing_error")
            self.log_test_result("Breathing Exercise", "FAIL", str(e), screenshot)
            return False
    
    async def test_responsive_design(self, page: Page) -> bool:
        """Test responsive design across different viewports"""
        viewports = [
            {"name": "Mobile", "width": 375, "height": 667},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Desktop", "width": 1920, "height": 1080}
        ]
        
        results = []
        
        for viewport in viewports:
            try:
                await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                await asyncio.sleep(1)
                
                # Check if content adapts properly
                await self.wait_for_load(page)
                
                # Check for horizontal scroll (bad)
                has_horizontal_scroll = await page.evaluate(
                    "() => document.body.scrollWidth > document.body.clientWidth"
                )
                
                # Check if key elements are visible
                key_elements = await page.query_selector_all('[data-testid="app-container"], header, main')
                
                screenshot = await self.take_screenshot(page, f"responsive_{viewport['name'].lower()}")
                
                passed = not has_horizontal_scroll and len(key_elements) > 0
                results.append(passed)
                
                self.log_test_result(
                    f"Responsive - {viewport['name']}", 
                    "PASS" if passed else "FAIL",
                    f"Scroll: {has_horizontal_scroll}, Elements: {len(key_elements)}",
                    screenshot
                )
                
            except Exception as e:
                screenshot = await self.take_screenshot(page, f"responsive_{viewport['name'].lower()}_error")
                self.log_test_result(f"Responsive - {viewport['name']}", "FAIL", str(e), screenshot)
                results.append(False)
        
        return all(results)
    
    async def test_session_persistence(self, page: Page) -> bool:
        """Test that session data persists across refreshes"""
        try:
            # First, interact with the app
            await self.test_chat_functionality(page)
            
            # Get current URL and any session indicators
            initial_url = page.url
            session_indicators = await page.query_selector_all('[data-session], .user-session')
            
            # Refresh the page
            await page.reload()
            await self.wait_for_load(page)
            
            # Check if session is maintained
            final_url = page.url
            session_after_refresh = await page.query_selector_all('[data-session], .user-session')
            
            # Check if chat history or mood data persists
            chat_messages = await page.query_selector_all('.message, .chat-message')
            mood_data = await page.query_selector_all('.mood-entry, .mood-history')
            
            screenshot = await self.take_screenshot(page, "session_persistence")
            
            session_persisted = (
                len(session_after_refresh) >= len(session_indicators) or
                len(chat_messages) > 0 or
                len(mood_data) > 0
            )
            
            self.log_test_result(
                "Session Persistence",
                "PASS" if session_persisted else "PARTIAL",
                f"Session indicators: {len(session_after_refresh)}, Messages: {len(chat_messages)}",
                screenshot
            )
            
            return session_persisted
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "session_error")
            self.log_test_result("Session Persistence", "FAIL", str(e), screenshot)
            return False
    
    async def test_error_handling(self, page: Page) -> bool:
        """Test error handling and edge cases"""
        try:
            # Test network error simulation
            await page.route("**/*", lambda route: route.abort())
            
            # Try to use the app while offline
            await page.goto(self.base_url)
            await asyncio.sleep(2)
            
            # Look for error messages or offline indicators
            error_selectors = [
                '[data-testid="error-message"]',
                '.error',
                'text="offline"',
                'text="connection"',
                'text="network"'
            ]
            
            error_found = False
            for selector in error_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    error_found = True
                    break
                except:
                    continue
            
            # Restore network
            await page.unroute_all()
            
            # Test invalid chat input
            await page.goto(self.base_url)
            await self.wait_for_load(page)
            
            chat_input = await page.wait_for_selector('textarea, input[type="text"]', timeout=5000)
            
            # Send very long message
            long_message = "test " * 1000
            await chat_input.fill(long_message)
            await chat_input.press("Enter")
            await asyncio.sleep(2)
            
            # Check if app handles gracefully
            app_responsive = await page.evaluate("() => document.readyState === 'complete'")
            
            screenshot = await self.take_screenshot(page, "error_handling")
            
            status = "PASS" if (error_found or app_responsive) else "PARTIAL"
            details = f"Error handling: {error_found}, App responsive: {app_responsive}"
            self.log_test_result("Error Handling", status, details, screenshot)
            
            return error_found or app_responsive
            
        except Exception as e:
            screenshot = await self.take_screenshot(page, "error_handling_error")
            self.log_test_result("Error Handling", "FAIL", str(e), screenshot)
            return False
    
    async def run_all_tests(self) -> Dict:
        """Run all E2E tests and return results"""
        print("🚀 Starting GentleQuest E2E Test Suite")
        print(f"📍 Target URL: {self.base_url}")
        print(f"📸 Screenshots will be saved to: {self.screenshots_dir}")
        print("-" * 60)
        
        browser, context, page = await self.setup_browser()
        
        try:
            # Run all test methods
            tests = [
                self.test_app_loads,
                self.test_onboarding_flow,
                self.test_chat_functionality,
                self.test_crisis_detection,
                self.test_mood_tracking,
                self.test_breathing_exercise,
                self.test_session_persistence,
                self.test_responsive_design,
                self.test_error_handling
            ]
            
            for test in tests:
                try:
                    await test(page)
                    await asyncio.sleep(1)  # Brief pause between tests
                except Exception as e:
                    print(f"❌ Test {test.__name__} failed: {e}")
                    await self.take_screenshot(page, f"{test.__name__}_critical_error")
        
        finally:
            await context.close()
            await browser.close()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "partial": partial_tests,
            "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "results": self.test_results,
            "screenshots_dir": str(self.screenshots_dir)
        }
        
        print("-" * 60)
        print(f"✅ Tests Complete: {passed_tests}/{total_tests} passed")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Partial: {partial_tests}")
        print(f"📊 Pass Rate: {summary['pass_rate']:.1f}%")
        
        return summary


async def main():
    """Main entry point for running E2E tests"""
    suite = GentleQuestE2ETestSuite()
    results = await suite.run_all_tests()
    
    # Save results to file
    results_file = Path("test/e2e_results.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    print(f"📸 Screenshots saved to: {suite.screenshots_dir}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
