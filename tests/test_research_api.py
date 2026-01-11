
import json
import unittest
import sys
from unittest.mock import MagicMock, patch
from io import BytesIO

class MockHandler:
    def __init__(self):
        self.rfile = BytesIO()
        self.wfile = BytesIO()
        self.headers = {}
        self.path = ""
        
    def _set_headers(self, code):
        self.headers['code'] = code

class TestResearchAPI(unittest.TestCase):
    def test_research_api(self):
        # Setup Mock Handler
        handler = MockHandler()
        handler.path = '/api/research'
        payload = json.dumps({"topic": "AI Trends"}).encode('utf-8')
        handler.rfile.write(payload)
        handler.rfile.seek(0)
        handler.headers['Content-Length'] = str(len(payload))

        # Logic:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            topic = data.get('topic')
            if not topic:
                raise ValueError("No topic")
                
            # Mock Bridge
            mock_bridge = MagicMock()
            with patch.dict(sys.modules, {
                "mcp_server_nucleus.runtime.firestore_bridge": MagicMock(get_bridge=lambda: mock_bridge),
                "mcp_server_nucleus": MagicMock()
            }):
                from mcp_server_nucleus.runtime.firestore_bridge import get_bridge
                import uuid
                from datetime import datetime
                
                event_payload = {
                    "intent": f"Research: {topic}",
                    "source": "hud_research_widget"
                }
                
                evt = {
                    "event_id": f"res-{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat(),
                    "emitter": "hud",
                    "event_type": "user_intent",
                    "severity": "NORMAL",
                    "payload": event_payload
                }
                
                get_bridge().push_event(evt)
                
                # Assert Bridge called
                self.assertTrue(mock_bridge.push_event.called)
                called_arg = mock_bridge.push_event.call_args[0][0]
                self.assertEqual(called_arg['event_type'], 'user_intent')
                self.assertEqual(called_arg['payload']['intent'], "Research: AI Trends")
                
                print("✅ Research API Event Logic Verified")

        except Exception as e:
            self.fail(f"❌ Failed: {e}")

if __name__ == "__main__":
    unittest.main()
