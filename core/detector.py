
class ElementDetector:
    async def detect(self, page):
        """
        Scans the page for interactive elements (links, buttons, inputs).
        Returns a list of dictionaries containing element metadata.
        """
        elements = []
        
        # Define selectors for interesting elements
        selectors = [
            'a[href]', 
            'button', 
            'input[type="submit"]', 
            'input[type="button"]',
            '[role="button"]'
        ]
        
        for selector in selectors:
            found = await page.locator(selector).all()
            for i, handle in enumerate(found):
                try:
                    # Basic metadata
                    tag_name = await handle.evaluate("el => el.tagName.toLowerCase()")
                    text = await handle.inner_text()
                    text = text.strip() if text else ""
                    
                    # Specific attributes
                    href = await handle.get_attribute("href") if tag_name == 'a' else None
                    element_id = await handle.get_attribute("id")
                    class_name = await handle.get_attribute("class")
                    
                    # Screenshot (optional, can be expensive for all elements)
                    # screenshot_path = f"screenshots/{uuid.uuid4()}.png"
                    # await handle.screenshot(path=screenshot_path)

                    elements.append({
                        "type": tag_name,
                        "text": text,
                        "href": href,
                        "id": element_id,
                        "class": class_name,
                        "selector": selector,
                        "visible": await handle.is_visible()
                    })
                except Exception as e:
                    print(f"Error processing element: {e}")
                    continue
                    
        return elements
