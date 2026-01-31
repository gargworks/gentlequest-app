"""
Tests for Clinical Assessments (PHQ-9, GAD-7)
Run with: pytest test_clinical_assessments.py -v
"""
import pytest
from providers.clinical_assessments import (
    score_phq9,
    score_gad7,
    get_assessment_questions,
    validate_responses,
    PHQ9_QUESTIONS,
    GAD7_QUESTIONS,
)


class TestPHQ9Scoring:
    """Test PHQ-9 depression screening scoring."""

    def test_minimal_score(self):
        """Score of 0-4 is minimal depression."""
        responses = [0, 0, 0, 0, 1, 0, 0, 0, 0]  # Score = 1
        result = score_phq9(responses)
        assert result["total_score"] == 1
        assert result["severity"] == "minimal"
        assert result["requires_follow_up"] is False
        assert result["responses"] == responses

    def test_mild_score(self):
        """Score of 5-9 is mild depression."""
        responses = [1, 1, 1, 1, 1, 0, 0, 0, 0]  # Score = 5
        result = score_phq9(responses)
        assert result["total_score"] == 5
        assert result["severity"] == "mild"

    def test_moderate_score(self):
        """Score of 10-14 is moderate depression."""
        responses = [2, 2, 1, 1, 1, 1, 1, 1, 0]  # Score = 10
        result = score_phq9(responses)
        assert result["total_score"] == 10
        assert result["severity"] == "moderate"

    def test_severe_score(self):
        """Score of 20-27 is severe depression."""
        responses = [3, 3, 3, 3, 2, 2, 2, 1, 1]  # Score = 20
        result = score_phq9(responses)
        assert result["total_score"] == 20
        assert result["severity"] == "severe"

    def test_suicidal_ideation_flag(self):
        """Question 9 > 0 triggers follow-up requirement."""
        responses = [0, 0, 0, 0, 0, 0, 0, 0, 1]  # Only Q9 = 1
        result = score_phq9(responses)
        assert result["requires_follow_up"] is True
        assert "self-harm" in result["follow_up_reason"]

    def test_max_score(self):
        """Maximum score is 27."""
        responses = [3] * 9
        result = score_phq9(responses)
        assert result["total_score"] == 27
        assert result["max_score"] == 27
        assert result["severity"] == "severe"

    def test_invalid_response_count(self):
        """Should raise error for wrong number of responses."""
        with pytest.raises(ValueError, match="9 responses"):
            score_phq9([0, 0, 0])

    def test_invalid_response_value(self):
        """Should raise error for out-of-range responses."""
        with pytest.raises(ValueError, match="between 0 and 3"):
            score_phq9([0, 0, 0, 0, 0, 0, 0, 0, 5])
        with pytest.raises(ValueError, match="between 0 and 3"):
            score_phq9([0, 0, 0, 0, 0, -1, 0, 0, 0])

    def test_phq9_boundary_cases(self):
        """Test scores right at the boundary of severity levels."""
        # 4 -> minimal
        assert score_phq9([1, 1, 1, 1, 0, 0, 0, 0, 0])["severity"] == "minimal"
        # 5 -> mild
        assert score_phq9([1, 1, 1, 1, 1, 0, 0, 0, 0])["severity"] == "mild"
        # 9 -> mild
        assert score_phq9([3, 3, 3, 0, 0, 0, 0, 0, 0])["severity"] == "mild"
        # 10 -> moderate
        assert score_phq9([3, 3, 3, 1, 0, 0, 0, 0, 0])["severity"] == "moderate"
        # 14 -> moderate
        assert score_phq9([3, 3, 3, 3, 2, 0, 0, 0, 0])["severity"] == "moderate"
        # 15 -> moderately_severe
        assert score_phq9([3, 3, 3, 3, 3, 0, 0, 0, 0])["severity"] == "moderately_severe"
        # 19 -> moderately_severe
        assert score_phq9([3, 3, 3, 3, 3, 3, 1, 0, 0])["severity"] == "moderately_severe"
        # 20 -> severe
        assert score_phq9([3, 3, 3, 3, 3, 3, 2, 0, 0])["severity"] == "severe"

    def test_non_integer_responses(self):
        """Should handle non-integer gracefully or raise helpful error."""
        with pytest.raises(TypeError):
            score_phq9([0, 0, "1", 0, 0, 0, 0, 0, 0])
        with pytest.raises(TypeError):
            score_phq9([0, 0, None, 0, 0, 0, 0, 0, 0])


class TestGAD7Scoring:
    """Test GAD-7 anxiety screening scoring."""

    def test_minimal_score(self):
        """Score of 0-4 is minimal anxiety."""
        responses = [0, 0, 0, 1, 0, 0, 0]  # Score = 1
        result = score_gad7(responses)
        assert result["total_score"] == 1
        assert result["severity"] == "minimal"
        assert result["responses"] == responses

    def test_mild_score(self):
        """Score of 5-9 is mild anxiety."""
        responses = [1, 1, 1, 1, 1, 0, 0]  # Score = 5
        result = score_gad7(responses)
        assert result["total_score"] == 5
        assert result["severity"] == "mild"

    def test_moderate_score(self):
        """Score of 10-14 is moderate anxiety."""
        responses = [2, 2, 2, 2, 1, 1, 0]  # Score = 10
        result = score_gad7(responses)
        assert result["total_score"] == 10
        assert result["severity"] == "moderate"

    def test_severe_score(self):
        """Score of 15-21 is severe anxiety."""
        responses = [3, 3, 3, 2, 2, 1, 1]  # Score = 15
        result = score_gad7(responses)
        assert result["total_score"] == 15
        assert result["severity"] == "severe"

    def test_max_score(self):
        """Maximum score is 21."""
        responses = [3] * 7
        result = score_gad7(responses)
        assert result["total_score"] == 21
        assert result["max_score"] == 21

    def test_invalid_response_count(self):
        """Should raise error for wrong number of responses."""
        with pytest.raises(ValueError, match="7 responses"):
            score_gad7([0, 0, 0])

    def test_gad7_boundary_cases(self):
        """Test GAD-7 boundary scores."""
        # 4 -> minimal
        assert score_gad7([1, 1, 1, 1, 0, 0, 0])["severity"] == "minimal"
        # 5 -> mild
        assert score_gad7([1, 1, 1, 1, 1, 0, 0])["severity"] == "mild"
        # 9 -> mild
        assert score_gad7([3, 3, 3, 0, 0, 0, 0])["severity"] == "mild"
        # 10 -> moderate
        assert score_gad7([3, 3, 3, 1, 0, 0, 0])["severity"] == "moderate"
        # 14 -> moderate
        assert score_gad7([2] * 7)["severity"] == "moderate"  # 14
        # 15 -> severe
        assert score_gad7([3, 3, 3, 3, 3, 0, 0])["severity"] == "severe"


class TestAssessmentQuestions:
    """Test question retrieval functions."""

    def test_get_phq9_questions(self):
        """Should return all 9 PHQ-9 questions."""
        result = get_assessment_questions("phq9")
        assert result["type"] == "phq9"
        assert len(result["questions"]) == 9
        assert len(result["options"]) == 4

    def test_get_gad7_questions(self):
        """Should return all 7 GAD-7 questions."""
        result = get_assessment_questions("gad7")
        assert result["type"] == "gad7"
        assert len(result["questions"]) == 7
        assert len(result["options"]) == 4

    def test_unknown_assessment_type(self):
        """Should raise error for unknown type."""
        with pytest.raises(ValueError, match="Unknown assessment"):
            get_assessment_questions("unknown")


class TestValidation:
    """Test response validation."""

    def test_valid_phq9_responses(self):
        """Valid PHQ-9 responses should pass."""
        valid, error = validate_responses("phq9", [0, 1, 2, 3, 0, 1, 2, 3, 0])
        assert valid is True
        assert error is None

    def test_valid_gad7_responses(self):
        """Valid GAD-7 responses should pass."""
        valid, error = validate_responses("gad7", [0, 1, 2, 3, 0, 1, 2])
        assert valid is True
        assert error is None

    def test_wrong_count_fails(self):
        """Wrong number of responses should fail."""
        valid, error = validate_responses("phq9", [0, 0, 0])
        assert valid is False
        assert "9 responses" in error

    def test_out_of_range_fails(self):
        """Out of range values should fail."""
        valid, error = validate_responses("gad7", [0, 0, 0, 0, 0, 0, 5])
        assert valid is False
        assert "between 0 and 3" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
