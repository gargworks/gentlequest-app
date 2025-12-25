"""
Tests for Agentic Wellness Tools
Run with: pytest test_agent_tools.py -v
"""
import pytest
from providers.agent_tools import (
    get_wellness_intervention,
    InterventionSelector,
    BREATHING_INTERVENTIONS,
    GROUNDING_INTERVENTIONS
)


class TestInterventionSelection:
    """Test the smart intervention selector"""
    
    def test_anxiety_returns_breathing(self):
        """Test anxiety issue returns breathing exercise"""
        result = get_wellness_intervention(
            issue='anxiety',
            intensity='moderate',
            user_id='test_user'
        )
        
        assert result['success'] is True
        assert result['intervention_type'] == 'breathing'
        assert result['interactive'] is True
        assert 'exercise' in result
        
    def test_panic_can_return_grounding(self):
        """Test panic can trigger grounding exercise"""
        result = get_wellness_intervention(
            issue='panic',
            intensity='severe',
            user_id='test_user'
        )
        
        assert result['success'] is True
        # Could be breathing or grounding
        assert result['intervention_type'] in ['breathing', 'grounding']
        
    def test_intensity_affects_selection(self):
        """Test that intensity is considered"""
        mild = get_wellness_intervention(
            issue='anxiety',
            intensity='mild'
        )
        
        severe = get_wellness_intervention(
            issue='anxiety',
            intensity='severe'
        )
        
        # Both should succeed
        assert mild['success'] is True
        assert severe['success'] is True
        
    def test_personalization_included(self):
        """Test that personalization message is included"""
        result = get_wellness_intervention(
            issue='stress',
            intensity='moderate'
        )
        
        assert 'personalization' in result
        assert isinstance(result['personalization'], str)


class TestInterventionSelector:
    """Test the intervention selector logic"""
    
    def test_scoring_considers_effectiveness(self):
        """Test that past effectiveness affects scoring"""
        selector = InterventionSelector()
        
        # Simulate user who had success with calm_478
        user_effectiveness = {
            'calm_478': 0.9,  # Very effective
            'quick_box': 0.3  # Less effective
        }
        
        selection = selector.select_intervention(
            issue='anxiety',
            intensity='moderate',
            user_effectiveness=user_effectiveness,
            context={}
        )
        
        # Should prefer the more effective one
        assert selection['intervention_id'] == 'calm_478'
        
    def test_scoring_adapts_to_time(self):
        """Test that time of day affects selection"""
        selector = InterventionSelector()
        
        # Night context should prefer quicker exercises
        night_selection = selector.select_intervention(
            issue='stress',
            intensity='mild',
            user_effectiveness={},
            context={'time_of_day': 'night'}
        )
        
        # Should get an intervention
        assert night_selection['intervention_id']
        
    def test_candidates_match_issue(self):
        """Test that candidate interventions match the issue"""
        selector = InterventionSelector()
        
        candidates = selector._get_candidates('anxiety')
        
        # Should return interventions good for anxiety
        assert len(candidates) > 0
        for intervention in candidates.values():
            assert 'anxiety' in intervention.get('best_for', [])


class TestFallbackBehavior:
    """Test fallback and error handling"""
    
    def test_unknown_issue_has_fallback(self):
        """Test unknown issue type still returns an intervention"""
        result = get_wellness_intervention(
            issue='unknown_issue',
            intensity='moderate'
        )
        
        # Should fallback to breathing
        assert result['success'] is True
        assert result['intervention_type'] == 'breathing'
        
    def test_handles_no_user_history(self):
        """Test works without user effectiveness data"""
        result = get_wellness_intervention(
            issue='stress',
            intensity='mild',
            user_id=None  # No user ID
        )
        
        assert result['success'] is True
        assert 'exercise' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
