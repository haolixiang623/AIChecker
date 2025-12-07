import unittest
from unittest.mock import MagicMock, patch
from ai.client import AIClient

class TestAIClientConfig(unittest.TestCase):
    @patch('ai.client.OpenAI')
    def test_siliconflow_config(self, mock_openai):
        # Setup mock
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mocked Analysis Report"
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        # Initialize client with SiliconFlow config
        client = AIClient(
            api_key="test-key",
            base_url="https://api.siliconflow.cn/v1",
            model="deepseek-ai/DeepSeek-V3"
        )
        
        # Test data
        element_data = {
            "type": "button",
            "text": "Submit",
            "selector": "#submit-btn"
        }
        
        # Run analysis
        client.analyze_element(element_data)
        
        # Verify OpenAI client initialization
        mock_openai.assert_called_with(api_key="test-key", base_url="https://api.siliconflow.cn/v1")
        
        # Verify model parameter usage
        call_args = mock_client_instance.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs['model'], "deepseek-ai/DeepSeek-V3")
        print("AI Client Configuration Test Passed!")

if __name__ == '__main__':
    unittest.main()
