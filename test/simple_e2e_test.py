#!/usr/bin/env python3
"""
Simple E2E test to debug GentleQuest app loading
"""

import asyncio
from playwright.async_api import async_playwright, Page

async def simple_test():
    """Simple test to check if app loads"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("🔍 Testing app.gentlequest.app...")
        
        try:
            # Try different URLs
            urls = [
                "https://app.gentlequest.app",
                "https://gentlequest.onrender.com",
                "https://www.gentlequest.app"
            ]
            
            for url in urls:
                print(f"\n📍 Trying: {url}")
                try:
                    await page.goto(url, timeout=10000)
                    await page.wait_for_load_state('networkidle', timeout=5000)
                    
                    # Get page title
                    title = await page.title()
                    print(f"   Title: {title}")
                    
                    # Get URL after redirect
                    current_url = page.url
                    print(f"   Final URL: {current_url}")
                    
                    # Check for common elements
                    elements = await page.query_selector_all('body, html, #app, .app, main')
                    print(f"   Elements found: {len(elements)}")
                    
                    # Get page content
                    body_text = await page.evaluate("() => document.body.innerText")
                    if body_text:
                        print(f"   Body text preview: {body_text[:200]}...")
                    
                    # Take screenshot
                    await page.screenshot(path=f"test/screenshots/e2e/debug_{url.replace('https://', '').replace('/', '_')}.png")
                    print(f"   ✅ Screenshot saved")
                    
                    if len(elements) > 0 or body_text:
                        print(f"   ✅ This URL appears to work!")
                        break
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
            
            # Wait a bit before closing
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path="test/screenshots/e2e/debug_final_error.png")
        
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())
