
import unittest
import json
import time
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

@unittest.skipIf(os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"), "Thread mocks unstable in CI")
class TestAppMemoryIntegration(unittest.TestCase):

    def setUp(self):
        os.environ["PYTEST_CURRENT_TEST"] = "true"
        self.application = create_app()
        self.application.config['TESTING'] = True
        self.application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.application.config['RATE_LIMIT_ENABLED'] = False
        self.app = self.application.test_client()
        self.app.testing = True

    @patch('app.threading.Thread')
    @patch('app._get_ai_response_with_failover')
    @patch('app._log_conversation')
    @patch('providers.memory.summarize_interaction_llm')
    @patch('providers.gemini.get_gemini_response_with_tools') # New patch for Gemini
    @patch('providers.memory.MEMORY_ENABLED', True)
    def test_chat_triggers_observer_async(self, mock_gemini, mock_summarize, mock_log_conv, mock_get_ai, mock_thread):
        """Test that chat endpoint spawns observer thread without blocking"""
        # Setup mocks
        mock_get_ai.return_value = ("AI Response", "low")
        
        # Mock Gemini response
        mock_gemini.return_value = ("I understand how you feel.", [])
        
        # Mock summary to track calls
        mock_summarize.return_value = None
        
        start_time = time.time()
        # Mock the app context that is passed to thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Make request
        response = self.app.post('/api/chat', 
                               json={'message': 'Hello'},
                               headers={'X-Session-ID': 'test-session'})
        
        # Verify success response
        self.assertEqual(response.status_code, 200)
        
        # Verify Thread was started
        mock_thread.assert_called_once()
        
        # Check thread args
        args, _ = mock_thread.call_args
        target_func = kwargs=mock_thread.call_args[1].get('target')
        
        # We can verify that the thread was called with the correct target function name if we could inspect it easily,
        # but just verifying ANY thread start is a good proxy for "async work triggered" here.
        # A more robust check is inspecting call_args
        
        # args[0] is target (passed as kwarg usually or positionally)
        # Let's check the args passed to the Worker
        # args passed to thread: (app_ctx, session_id, message, ai_response)
        call_kwargs = mock_thread.call_args[1]
        thread_args = call_kwargs.get('args')
        
        self.assertEqual(thread_args[1], 'test-session')
        self.assertEqual(thread_args[2], 'Hello')
        self.assertEqual(thread_args[3], 'AI Response')
        
        # Check that start() was called
        mock_thread_instance.start.assert_called_once()

if __name__ == '__main__':
    unittest.main()
