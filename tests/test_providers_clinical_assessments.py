import pytest
import providers.clinical_assessments as clinical_assessments

class TestClinicalAssessments:
    def test_phq9_scoring_minimal(self):
        # Arrange
        answers = [0] * 9 # List of 9 zeros
        
        # Act
        result = clinical_assessments.score_phq9(answers)
        
        # Assert
        assert result['total_score'] == 0
        assert result['severity'] == "minimal"

    def test_phq9_scoring_severe(self):
        # Arrange
        answers = [3] * 9 # List of 9 threes
        
        # Act
        result = clinical_assessments.score_phq9(answers)
        
        # Assert
        assert result['total_score'] == 27
        assert result['severity'] == "severe"

    def test_gad7_scoring_moderate(self):
        # Arrange
        # 10 points total
        answers = [2, 1, 2, 1, 2, 1, 1] 
        
        # Act
        result = clinical_assessments.score_gad7(answers)
        
        # Assert
        assert result['total_score'] == 10
        assert result['severity'] == "moderate"

    def test_invalid_input_length(self):
        with pytest.raises(ValueError):
            clinical_assessments.score_phq9([1, 2, 3]) # Too few

    def test_recommendations_severe(self):
        # Act
        recs = clinical_assessments.get_phq9_recommendations("severe", has_suicidal_ideation=True)
        
        # Assert
        # Check for presence of crisis keywords in the list of strings
        assert any("crisis" in r.lower() for r in recs)
        assert any("self-harm" in r.lower() for r in recs)

    def test_get_assessment_questions(self):
        # Act
        phq9_meta = clinical_assessments.get_assessment_questions("phq9")
        
        # Assert
        assert phq9_meta['total_questions'] == 9
        assert len(phq9_meta['questions']) == 9
