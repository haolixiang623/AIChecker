from playwright.async_api import async_playwright

class PageScanner:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False) # Visible for demo/debugging
        self.context = await self.browser.new_context()

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scan(self, url):
        if not self.context:
            await self.start()
        
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            return page
        except Exception as e:
            print(f"Error scanning {url}: {e}")
            return None
