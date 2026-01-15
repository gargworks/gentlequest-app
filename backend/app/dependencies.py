from app.services.ai_insights_service import AIInsightsService

# Singleton instance
ai_service = AIInsightsService()

def get_ai_service() -> AIInsightsService:
    return ai_service
