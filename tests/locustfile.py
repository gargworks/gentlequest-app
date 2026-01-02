from locust import HttpUser, task, between
import uuid
import random

class GentleQuestUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Generate a random user ID/Session ID for this user
        self.user_id = str(uuid.uuid4())
        self.session_id = f"load-test-{str(uuid.uuid4())[:8]}"
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }

    @task(3)
    def chat_interaction(self):
        """Simulate a chat message flow"""
        payload = {
            "message": random.choice([
                "I'm feeling anxious today",
                "Can you help me breathe?",
                "I had a bad dream",
                "Just checking in",
                "What can you do?"
            ]),
            "session_id": self.session_id
        }
        self.client.post("/api/chat", json=payload, headers=self.headers)

    @task(1)
    def check_health(self):
        """Lightweight health check"""
        self.client.get("/api/health")

    @task(1)
    def check_assessment_questions(self):
        """Load assessment questions"""
        self.client.get("/api/assessment/phq9/questions")

    @task(1)
    def check_memory_status(self):
        """Check memory status endpoint"""
        self.client.get("/api/memory/status")

