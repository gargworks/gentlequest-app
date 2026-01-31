import pytest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch
from providers.quest_engine import QuestEngine
from models import Quest, QuestProgress, UserProfile

@pytest.fixture
def mock_db_session():
    with patch('models.db.session') as mock_session:
        yield mock_session

class TestQuestEngine:
    @patch('providers.quest_generator.QuestGenerator.generate_weekly_quests')
    @patch('providers.quest_generator.QuestGenerator.get_week_number')
    @patch('models.UserProfile.query')
    @patch('models.QuestProgress.query')
    def test_get_weekly_quests_creates_profile_if_missing(
        self, mock_qp_query, mock_up_query, mock_get_week, mock_gen_quests, mock_db_session
    ):
        # Arrange
        session_id = "test_session_123"
        mock_up_query.filter_by.return_value.first.return_value = None 
        
        mock_get_week.return_value = (5, 2024)
        mock_gen_quests.return_value = [
            {'id': 1, 'title': 'Q1', 'description': 'D1', 'xp_reward': 50, 'type': 'daily', 'difficulty': 'easy'}
        ]
        
        # Act
        result = QuestEngine.get_weekly_quests(session_id)
        
        # Assert
        mock_db_session.add.assert_called()
        assert len(result['quests']) == 1

    @patch('models.Quest.query')
    @patch('models.UserProfile.query')
    @patch('models.QuestProgress.query')
    def test_complete_quest_awards_xp_and_levels_up(
        self, mock_qp_query, mock_up_query, mock_q_query, mock_db_session
    ):
        # Arrange
        session_id = "test_session_456"
        quest_id = 99
        
        mock_quest = MagicMock(spec=Quest)
        mock_quest.xp_reward = 150
        mock_q_query.get.return_value = mock_quest
        
        # Mock Profile - CRITICAL: Attributes must act like ints
        # We use a real object or a mock with specific internal state
        mock_profile = MagicMock(spec=UserProfile)
        mock_profile.xp = 0
        mock_profile.level = 1
        mock_profile.badges = ""
        mock_profile.last_activity_date = None
        
        mock_up_query.filter_by.return_value.first.return_value = mock_profile
        
        mock_progress = MagicMock(spec=QuestProgress)
        mock_progress.status = "available"
        mock_qp_query.filter_by.return_value.first.return_value = mock_progress
        
        # Act
        # Because we can't easily make MagicMock attributes increment like C pointers,
        # we check the LOGIC outcome in the response, assuming the code flows correctly.
        # But wait, the code does `profile.xp += reward`. MagicMock ints don't increment.
        # We need a simpler object for `profile`.
        
        class FakeProfile:
            def __init__(self):
                self.xp = 0
                self.level = 1
                self.badges = ""
                self.streak_days = 0
                self.last_activity_date = None
        
        real_profile = FakeProfile()
        mock_up_query.filter_by.return_value.first.return_value = real_profile
        
        # Act
        result = QuestEngine.complete_quest(session_id, quest_id)
        if isinstance(result, tuple): result = result[0]
        
        # Assert
        assert result['success'] is True
        assert result['xp_earned'] == 150
        assert result['new_total_xp'] == 150
        assert result['leveled_up'] is True
        assert result['new_level'] == 2

    @patch('models.Quest.query')
    @patch('models.UserProfile.query')
    @patch('models.QuestProgress.query')
    def test_complete_already_completed_quest(
        self, mock_qp_query, mock_up_query, mock_q_query, mock_db_session
    ):
        session_id = "test_session_789"
        quest_id = 99
        
        mock_q_query.get.return_value = MagicMock(spec=Quest)
        mock_up_query.filter_by.return_value.first.return_value = MagicMock(spec=UserProfile)
        
        mock_progress = MagicMock(spec=QuestProgress)
        mock_progress.status = "completed"
        mock_qp_query.filter_by.return_value.first.return_value = mock_progress
        
        result = QuestEngine.complete_quest(session_id, quest_id)
        if isinstance(result, tuple): result = result[0]

        assert result['message'] == "Already completed"

    @patch('models.Quest.query')
    @patch('models.UserProfile.query')
    @patch('models.QuestProgress.query')
    def test_streak_logic_increments(
        self, mock_qp_query, mock_up_query, mock_q_query, mock_db_session
    ):
        session_id = "streak_user"
        quest_id = 1
        
        mock_quest = MagicMock(spec=Quest)
        mock_quest.xp_reward = 50 # Vital: must be int
        mock_q_query.get.return_value = mock_quest
        
        class FakeProfileStreak:
            def __init__(self):
                self.xp = 0
                self.level = 1
                self.badges = ""
                self.streak_days = 5
                # Yesterday
                self.last_activity_date = datetime.utcnow() - timedelta(days=1)
                
        real_profile = FakeProfileStreak()
        mock_up_query.filter_by.return_value.first.return_value = real_profile
        
        mock_progress = MagicMock(spec=QuestProgress)
        mock_progress.status = "available"
        mock_qp_query.filter_by.return_value.first.return_value = mock_progress
        
        # Act
        QuestEngine.complete_quest(session_id, quest_id)
        
        # Assert
        assert real_profile.streak_days == 6

    @patch('providers.quest_generator.QuestGenerator.generate_weekly_quests')
    def test_get_weekly_quests_fallback_on_error(self, mock_gen, mock_db_session):
        # Scenario: LLM/Generator Fails, check if hardcoded fallbacks work
        mock_gen.side_effect = Exception("LLM Down")
        session_id = "fallback_user"
        
        result = QuestEngine.get_weekly_quests(session_id)
        
        assert len(result['quests']) > 0
        assert result['quests'][0]['title'] == "One Tiny Step" # Approved fallback

    @patch('providers.quest_engine.QuestEngine.get_weekly_quests')
    @patch('providers.quest_engine.QuestEngine.complete_quest')
    def test_complete_quest_for_assessment_phq9_success(self, mock_complete, mock_get_weekly):
        # Arrange
        session_id = "test_user_assessment"
        assessment_type = "phq9"
        
        # Mock finding a PHQ-9 quest
        mock_get_weekly.return_value = {
            'quests': [
                {'id': 101, 'title': 'Walk', 'type': 'task', 'status': 'available'},
                {'id': 102, 'title': 'Complete PHQ-9 Assessment', 'type': 'progress', 'status': 'available'}
            ]
        }
        
        # Act
        QuestEngine.complete_quest_for_assessment(session_id, assessment_type)
        
        # Assert
        mock_complete.assert_called_once_with(session_id, 102, data={'progress': 1})

    @patch('providers.quest_engine.QuestEngine.get_weekly_quests')
    @patch('providers.quest_engine.QuestEngine.complete_quest')
    def test_complete_quest_for_assessment_gad7_no_match(self, mock_complete, mock_get_weekly):
        # Arrange
        session_id = "test_user_assessment_fail"
        assessment_type = "gad7"
        
        # No GAD-7 quest in list
        mock_get_weekly.return_value = {
            'quests': [
                {'id': 101, 'title': 'Walk', 'type': 'task', 'status': 'available'},
                {'id': 102, 'title': 'Complete PHQ-9 Assessment', 'type': 'progress', 'status': 'available'}
            ]
        }
        
        # Act
        QuestEngine.complete_quest_for_assessment(session_id, assessment_type)
        
        # Assert
        mock_complete.assert_not_called()

