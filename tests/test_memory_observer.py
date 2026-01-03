
import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add parent directory to path to import providers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.memory import summarize_interaction_llm

class TestMemoryObserver(unittest.TestCase):
    
    @patch('providers.memory.genai')
    @patch('providers.memory.store_memory')
    @patch('providers.memory.MEMORY_ENABLED', True)
    @patch('providers.memory._check_memory_tables_exist', return_value=True)
    @patch('providers.memory.GEMINI_AVAILABLE', True)
    @patch('providers.memory._get_api_key', return_value="fake_key")
    def test_summarize_interaction_llm_success(self, mock_get_key, mock_check_tables, mock_store, mock_genai):
        # Setup mock response
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = '''
        ```json
        [
            {
                "type": "episodic",
                "content": "User lives in Seattle"
            },
            {
                "type": "emotional",
                "content": "User is feeling anxious about exams"
            }
        ]
        ```
        '''
        mock_model.generate_content.return_value = mock_response
        
        # Call function
        result = summarize_interaction_llm("session_123", "I live in Seattle and I'm worried about exams", "I hear you.")
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(mock_store.call_count, 2)
        
        # Verify first memory
        mock_store.assert_any_call(
            session_id="session_123",
            content="User lives in Seattle",
            memory_type="episodic",
            metadata={"source": "observer", "date": unittest.mock.ANY}
        )
        
        # Verify second memory
        mock_store.assert_any_call(
            session_id="session_123",
            content="User is feeling anxious about exams",
            memory_type="emotional",
            metadata={"source": "observer", "date": unittest.mock.ANY}
        )

    @patch('providers.memory.genai')
    @patch('providers.memory.store_memory')
    @patch('providers.memory.MEMORY_ENABLED', True)
    @patch('providers.memory._check_memory_tables_exist', return_value=True)
    @patch('providers.memory.GEMINI_AVAILABLE', True)
    @patch('providers.memory._get_api_key', return_value="fake_key")
    def test_summarize_interaction_llm_empty(self, mock_get_key, mock_check_tables, mock_store, mock_genai):
        # Setup mock response for empty/irrelevant content
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = "[]"
        mock_model.generate_content.return_value = mock_response
        
         # Call function
        result = summarize_interaction_llm("session_123", "Hi", "Hello")
        
        # Assertions
        self.assertTrue(result)
        mock_store.assert_not_called()

    @patch('providers.memory.genai')
    @patch('providers.memory.store_memory')
    @patch('providers.memory.MEMORY_ENABLED', True)
    @patch('providers.memory._check_memory_tables_exist', return_value=True)
    @patch('providers.memory.GEMINI_AVAILABLE', True)
    @patch('providers.memory._get_api_key', return_value="fake_key")
    def test_summarize_interaction_llm_malformed_json(self, mock_get_key, mock_check_tables, mock_store, mock_genai):
        # Setup mock response with bad JSON
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"
        mock_model.generate_content.return_value = mock_response
        
         # Call function - should handle error gracefully and return False
        result = summarize_interaction_llm("session_123", "Hi", "Hello")
        
        # Assertions
        self.assertFalse(result)
        mock_store.assert_not_called()

    @patch('providers.memory.genai')
    @patch('providers.memory.store_memory')
    @patch('providers.memory.MEMORY_ENABLED', True)
    @patch('providers.memory._check_memory_tables_exist', return_value=True)
    @patch('providers.memory.GEMINI_AVAILABLE', True)
    @patch('providers.memory._get_api_key', return_value="fake_key")
    def test_summarize_interaction_llm_api_error(self, mock_get_key, mock_check_tables, mock_store, mock_genai):
        # Setup mock to raise exception
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
         # Call function
        result = summarize_interaction_llm("session_123", "Hi", "Hello")
        
        # Assertions
        self.assertFalse(result)
        mock_store.assert_not_called()

if __name__ == '__main__':
    unittest.main()
