"""
Tests for wellness tools (breathing, grounding, journal prompt)
Run with: pytest test_tools.py -v
"""
import pytest
from providers.tools import execute_tool


class TestBreathingExercise:
    def test_get_calm_breathing(self):
        """Test 4-7-8 breathing exercise"""
        result = execute_tool('get_breathing_exercise', {'type': 'calm'}, 'test_session')
        
        assert result['success'] is True
        assert result['exercise_type'] == 'breathing'
        assert result['interactive'] is True
        assert 'exercise' in result
        
        exercise = result['exercise']
        assert exercise['name'] == '4-7-8 Calming Breath'
        assert len(exercise['steps']) == 3
        assert exercise['cycles'] == 4
        assert exercise['total_time_seconds'] == 76
        
    def test_get_quick_breathing(self):
        """Test box breathing exercise"""
        result = execute_tool('get_breathing_exercise', {'type': 'quick'}, 'test_session')
        
        assert result['exercise_type'] == 'breathing'
        exercise = result['exercise']
        assert exercise['name'] == 'Box Breathing'
        assert len(exercise['steps']) == 4
        
    def test_breathing_default_type(self):
        """Test breathing exercise defaults to calm"""
        result = execute_tool('get_breathing_exercise', {}, 'test_session')
        
        exercise = result['exercise']
        assert exercise['name'] == '4-7-8 Calming Breath'


class TestGroundingExercise:
    def test_get_grounding(self):
        """Test grounding exercise returns 5-4-3-2-1"""
        result = execute_tool('get_grounding_exercise', {}, 'test_session')
        
        assert result['success'] is True
        assert result['exercise_type'] == 'grounding'
        assert result['interactive'] is True
        assert 'exercise' in result
        
        exercise = result['exercise']
        assert 'name' in exercise
        assert 'steps' in exercise
        

class TestJournalPrompt:
    def test_get_general_prompt(self):
        """Test general journal prompt"""
        result = execute_tool('get_journal_prompt', {'topic': 'general'}, 'test_session')
        
        assert result['success'] is True
        assert 'prompt' in result
        assert 'category' in result
        assert result['category'] == 'general'
        
    def test_get_anxiety_prompt(self):
        """Test anxiety-specific prompt"""
        result = execute_tool('get_journal_prompt', {'topic': 'anxious'}, 'test_session')
        
        # Should map 'anxious' to 'anxiety'
        assert result['category'] == 'anxiety'
        
    def test_prompt_default_category(self):
        """Test unknown topic defaults to general"""
        result = execute_tool('get_journal_prompt', {'topic': 'unknown_topic'}, 'test_session')
        
        assert result['category'] == 'general'


class TestToolExecution:
    def test_unknown_tool(self):
        """Test unknown tool name returns error"""
        result = execute_tool('non_existent_tool', {}, 'test_session')
        
        assert result['success'] is False
        assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
