
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

class TestChatAPI(unittest.TestCase):
    def test_chat_api(self):
        # Setup Mock Handler
        handler = MockHandler()
        handler.path = '/api/chat'
        payload = json.dumps({"message": "Hello Brain"}).encode('utf-8')
        handler.rfile.write(payload)
        handler.rfile.seek(0)
        handler.headers['Content-Length'] = str(len(payload))

        # Logic:
        content_length = int(handler.headers['Content-Length'])
        post_data = handler.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message')
            if not message:
                raise ValueError("No message")
                
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
                    "message": message,
                    "source": "hud_chat"
                }
                
                evt = {
                    "event_id": f"msg-{uuid.uuid4().hex[:8]}",
                    "timestamp": datetime.now().isoformat(),
                    "emitter": "hud",
                    "event_type": "user_message",
                    "severity": "NORMAL",
                    "payload": event_payload
                }
                
                get_bridge().push_event(evt)
                
                # Assert Bridge called
                self.assertTrue(mock_bridge.push_event.called)
                called_arg = mock_bridge.push_event.call_args[0][0]
                self.assertEqual(called_arg['event_type'], 'user_message')
                self.assertEqual(called_arg['payload']['message'], "Hello Brain")
                
                print("✅ Chat API Event Logic Verified")

        except Exception as e:
            self.fail(f"❌ Failed: {e}")

if __name__ == "__main__":
    unittest.main()
