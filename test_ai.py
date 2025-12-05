import unittest
from unittest.mock import MagicMock, patch
from ai.client import AIClient

class TestAIClient(unittest.TestCase):
    @patch('ai.client.OpenAI')
    def test_analyze_element(self, mock_openai):
        # Setup mock
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mocked Analysis Report"
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        # Initialize client
        client = AIClient(api_key="test-key")
        
        # Test data
        element_data = {
            "type": "button",
            "text": "Submit",
            "selector": "#submit-btn"
        }
        
        # Run analysis
        result = client.analyze_element(element_data)
        
        # Verify
        self.assertEqual(result, "Mocked Analysis Report")
        mock_client_instance.chat.completions.create.assert_called_once()
        print("AI Client Test Passed!")

if __name__ == '__main__':
    unittest.main()
