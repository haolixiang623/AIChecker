import asyncio
from core.scanner import PageScanner
from core.detector import ElementDetector

async def main():
    scanner = PageScanner()
    detector = ElementDetector()
    
    print("Starting scan...")
    await scanner.start()
    
    url = "https://example.com"
    print(f"Navigating to {url}...")
    page = await scanner.scan(url)
    
    if page:
        print("Page loaded. Detecting elements...")
        elements = await detector.detect(page)
        print(f"Found {len(elements)} elements:")
        for el in elements:
            print(f"- {el['type']}: {el['text']} (href: {el.get('href')})")
            
    await scanner.stop()
    print("Scan complete.")

if __name__ == "__main__":
    asyncio.run(main())
