import os
from openai import OpenAI

class AIClient:
    def __init__(self, api_key=None, base_url=None):
        # Allow passing key/url or reading from env
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        if not self.api_key:
            print("Warning: No API Key provided for AIClient")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze_element(self, element_data):
        """
        Generates an analysis report for a single element.
        """
        if not self.client:
            return "Error: AI Client not initialized (Missing API Key)."

        prompt = self._construct_element_prompt(element_data)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", # Default model, can be made configurable
                messages=[
                    {"role": "system", "content": "You are a QA automation expert. Analyze the provided page element and suggest test cases or potential issues."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling AI API: {e}"

    def _construct_element_prompt(self, el):
        return f"""
        Analyze this web element:
        Type: {el.get('type')}
        Text: "{el.get('text')}"
        HREF: {el.get('href')}
        Selector: {el.get('selector')}
        
        Please provide:
        1. A brief description of what this element likely does.
        2. 2-3 negative test cases.
        3. Accessibility concerns (if any).
        """
