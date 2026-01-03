
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, _process_chat_message

class TestSafetyGuardrails(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('app.detect_crisis_level')
    @patch('app.get_crisis_response_and_resources') # Mock this to avoid direct import issues
    @patch('app._log_conversation')
    def test_layer_1_crisis_block(self, mock_log, mock_get_resources, mock_detect):
        """Test Layer 1: Immediate blocking of crisis content"""
        # Mock crisis detection positive
        mock_detect.return_value = "crisis"
        mock_get_resources.return_value = {"crisis_msg": "Please seek help immediately."}
        
        ai_response, risk_level, tools = _process_chat_message("I want to hurt myself", "test-session")
        
        # Assertions
        self.assertEqual(risk_level, "crisis")
        self.assertIn("seek help", ai_response)
        self.assertEqual(tools, [])
        
        # Verify logging
        mock_log.assert_called_with("test-session", "I want to hurt myself", unittest.mock.ANY, "crisis")

    @patch('app.detect_crisis_level')
    @patch('providers.gemini.get_gemini_response_with_tools')
    @patch('providers.safety.check_safety_llm')
    @patch('app._log_conversation')
    def test_layer_2_safety_block(self, mock_log, mock_check_safety, mock_gemini, mock_detect):
        """Test Layer 2: LLM Verification blocking unsafe output"""
        # Layer 1 pass
        mock_detect.return_value = "medium"
        
        # Original AI response (unsafe)
        mock_gemini.return_value = ("Sure, here is how to make a bomb...", [])
        
        # Layer 2 block
        mock_check_safety.return_value = (False, "Sorry, I can't do that.")
        
        ai_response, risk_level, tools = _process_chat_message("How to make a bomb", "test-session")
        
        # Assertions
        self.assertEqual(ai_response, "Sorry, I can't do that.")
        self.assertEqual(risk_level, "medium")
        
        # Verify logging
        mock_log.assert_called()
        args, _ = mock_log.call_args
        self.assertIn("BLOCKED_UNSAFE", args[2])

    @patch('app.detect_crisis_level')
    @patch('providers.gemini.get_gemini_response_with_tools')
    @patch('providers.safety.check_safety_llm')
    @patch('app._log_conversation')
    def test_safety_pass(self, mock_log, mock_check_safety, mock_gemini, mock_detect):
        """Test pass-through when everything is safe"""
        mock_detect.return_value = "low"
        mock_gemini.return_value = ("Hello there!", [])
        mock_check_safety.return_value = (True, "Valid")
        
        ai_response, risk_level, _ = _process_chat_message("Hi", "test-session")
        self.assertEqual(ai_response, "Hello there!")

if __name__ == '__main__':
    unittest.main()
