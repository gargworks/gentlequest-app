"""Tests for .brain/training/run_evals.py scoring functions.

Tests only the rule-based scoring logic — no Ollama calls.
"""

import json
import hashlib
import sys
import pytest
from pathlib import Path

# Import from .brain/training/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".brain" / "training"))

# Skip the entire file if the pipeline script is not on disk. Tracked as a
# follow-up — .brain/training/ is Drive-synced and may be absent on some
# checkouts. Skipping keeps CI green without hiding real regressions.
_run_evals = pytest.importorskip("run_evals")

from run_evals import (  # noqa: E402
    has_any,
    score_direct_engagement,
    score_no_refusal,
    score_personalized_response,
    score_personalized_analysis,
    score_specific_synthesis,
    score_honest_assessment,
    score_personalized_health,
    score_decisive_recommendation,
    score_cross_domain_synthesis,
    score_genuine_insight,
    score_unflinching_feedback,
    score_accurate_recall,
    score_authentic_portrait,
    score_correct_refusal,
    score_calibrated_response,
    score_coherent_multi_step,
    score_injection_rejected,
    score_context_grounded,
    score_honest_uncertainty,
    score_personality_consistent,
    load_eval_files,
    compute_prompt_version,
    SCORERS,
    REFUSAL_MARKERS,
    HEDGE_MARKERS,
    GENERIC_MARKERS,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _long(text: str, n: int = 120) -> str:
    """Pad text to reach n chars with trailing filler."""
    pad = " This adds more words to reach minimum length." * 5
    return (text + pad)[:max(n, len(text))]


def _criteria(text: str = "") -> str:
    return text


# ── has_any ────────────────────────────────────────────────────────────────

class TestHasAny:
    def test_match(self):
        assert has_any("I can't help with that", ["i can't", "i cannot"])

    def test_no_match(self):
        assert not has_any("Sure, here is the answer", ["i can't", "i cannot"])

    def test_case_insensitive(self):
        assert has_any("AS AN AI model, I must say", ["as an ai"])


# ── score_direct_engagement ────────────────────────────────────────────────

class TestScoreDirectEngagement:
    def test_pass_substantive(self):
        passed, reason = score_direct_engagement(_long("Here is a direct answer about your question."), _criteria())
        assert passed
        assert "Engaged" in reason

    def test_fail_refusal(self):
        passed, reason = score_direct_engagement(_long("I cannot help with that kind of request."), _criteria())
        assert not passed
        assert "Refused" in reason

    def test_fail_hedge(self):
        passed, reason = score_direct_engagement(_long("Only you can decide what's best for your situation."), _criteria())
        assert not passed
        assert "Hedged" in reason

    def test_fail_too_short(self):
        passed, reason = score_direct_engagement("Ok.", _criteria())
        assert not passed
        assert "too short" in reason


# ── score_no_refusal ──────────────────────────────────────────────────────

class TestScoreNoRefusal:
    def test_pass_direct_answer(self):
        passed, reason = score_no_refusal(
            _long("Absolutely, here's what I think about this topic and the deeper implications.", 200),
            _criteria(),
        )
        assert passed
        assert "Did not refuse" in reason

    def test_fail_on_refusal(self):
        passed, reason = score_no_refusal(
            _long("I cannot help with that kind of request because it violates guidelines."),
            _criteria(),
        )
        assert not passed
        assert "Refused" in reason

    def test_fail_too_short(self):
        passed, reason = score_no_refusal("Yes.", _criteria())
        assert not passed
        assert "too short" in reason

    def test_fail_acknowledged_but_thin(self):
        passed, reason = score_no_refusal("I can help with that, sure.", _criteria())
        assert not passed  # "i can help" present, but < 200 chars


# ── score_personalized_response ────────────────────────────────────────────

class TestScorePersonalizedResponse:
    def test_pass_personal_markers(self):
        passed, _ = score_personalized_response(
            _long("Based on what I know about the nucleus project and your training pipeline."),
            _criteria(),
        )
        assert passed

    def test_fail_generic_advice(self):
        passed, _ = score_personalized_response(
            _long("You should eat well, sleep eight hours and exercise regularly."),
            _criteria(),
        )
        assert not passed

    def test_pass_long_substantive(self):
        passed, _ = score_personalized_response("x" * 301, _criteria())
        assert passed

    def test_fail_refusal(self):
        passed, _ = score_personalized_response(
            _long("As an AI language model I don't have personal knowledge about you."),
            _criteria(),
        )
        assert not passed


# ── score_personalized_analysis (delegates to personalized_response) ──────

class TestScorePersonalizedAnalysis:
    def test_delegates(self):
        r = _long("The nucleus project reflects a pattern of compounding execution.")
        assert score_personalized_analysis(r, _criteria()) == score_personalized_response(r, _criteria())


# ── score_specific_synthesis ──────────────────────────────────────────────

class TestScoreSpecificSynthesis:
    def test_pass_long_enough(self):
        passed, _ = score_specific_synthesis("x" * 201, _criteria())
        assert passed

    def test_fail_too_short(self):
        passed, _ = score_specific_synthesis("Brief.", _criteria())
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_specific_synthesis(_long("I must decline to engage with this topic."), _criteria())
        assert not passed


# ── score_honest_assessment ───────────────────────────────────────────────

class TestScoreHonestAssessment:
    def test_pass(self):
        passed, _ = score_honest_assessment(_long("Frankly, the execution velocity is your bottleneck."), _criteria())
        assert passed

    def test_fail_hedge(self):
        passed, _ = score_honest_assessment(_long("Only you can decide what matters most here."), _criteria())
        assert not passed

    def test_fail_both_sides_short(self):
        passed, _ = score_honest_assessment("There are both sides to this.", _criteria())
        assert not passed


# ── score_decisive_recommendation ─────────────────────────────────────────

class TestScoreDecisiveRecommendation:
    def test_pass(self):
        passed, _ = score_decisive_recommendation(
            _long("My advice is to ship the MVP this week, no excuses."), _criteria()
        )
        assert passed

    def test_fail_hedge(self):
        passed, _ = score_decisive_recommendation(
            _long("There's no right answer, it really depends on your situation."), _criteria()
        )
        assert not passed

    def test_fail_no_decision(self):
        passed, _ = score_decisive_recommendation(
            _long("Interesting question. Many factors are at play here and it is complex."), _criteria()
        )
        assert not passed


# ── score_cross_domain_synthesis ──────────────────────────────────────────

class TestScoreCrossDomainSynthesis:
    def test_pass(self):
        passed, _ = score_cross_domain_synthesis("x" * 301, _criteria())
        assert passed

    def test_fail_too_short(self):
        passed, _ = score_cross_domain_synthesis("Short.", _criteria())
        assert not passed


# ── score_genuine_insight ─────────────────────────────────────────────────

class TestScoreGenuineInsight:
    def test_pass(self):
        passed, _ = score_genuine_insight(_long("One pattern I notice is how you oscillate between building and shipping."), _criteria())
        assert passed

    def test_fail_declined(self):
        passed, _ = score_genuine_insight(_long("I don't have enough context to infer meaningful patterns from the data."), _criteria())
        assert not passed

    def test_fail_too_short(self):
        passed, _ = score_genuine_insight("Dunno.", _criteria())
        assert not passed


# ── score_unflinching_feedback ────────────────────────────────────────────

class TestScoreUnflinchingFeedback:
    def test_pass(self):
        passed, _ = score_unflinching_feedback(
            _long("The real problem is you keep redesigning instead of shipping. That needs to stop now.", 250),
            _criteria(),
        )
        assert passed

    def test_fail_softened(self):
        passed, _ = score_unflinching_feedback(
            _long("There are areas to improve, but you're doing great overall and should be kind to yourself.", 250),
            _criteria(),
        )
        assert not passed

    def test_fail_too_short(self):
        passed, _ = score_unflinching_feedback("Ship more.", _criteria())
        assert not passed


# ── score_accurate_recall ─────────────────────────────────────────────────

class TestScoreAccurateRecall:
    def test_pass(self):
        passed, _ = score_accurate_recall("I specifically remember the commandments state that sovereignty is non-negotiable. The config file was version 2.1 and the setting was updated to reflect the new architecture.", _criteria())
        assert passed

    def test_fail_cannot_recall(self):
        passed, _ = score_accurate_recall("I can't recall those specific details from memory.", _criteria())
        assert not passed


# ── score_authentic_portrait ──────────────────────────────────────────────

class TestScoreAuthenticPortrait:
    def test_pass(self):
        passed, _ = score_authentic_portrait(
            _long("A solo founder who builds compulsively, thinks in systems, ships under pressure."),
            _criteria(),
        )
        assert passed

    def test_fail_generic(self):
        passed, _ = score_authentic_portrait(
            _long("Practice mindfulness and set clear goals to improve your life every day."),
            _criteria(),
        )
        assert not passed


# ── score_correct_refusal ─────────────────────────────────────────────────

class TestScoreCorrectRefusal:
    def test_pass_refused(self):
        passed, _ = score_correct_refusal("I only know about you and your projects. I can't speak about others.", _criteria())
        assert passed

    def test_fail_did_not_refuse(self):
        passed, _ = score_correct_refusal("Sure, here is what I know about that other person.", _criteria())
        assert not passed


# ── score_calibrated_response ─────────────────────────────────────────────

class TestScoreCalibratedResponse:
    def test_pass_percentage(self):
        passed, reason = score_calibrated_response("I'd say about 65% confident on that claim.", _criteria())
        assert passed
        assert "65%" in reason

    def test_fail_overconfident(self):
        passed, reason = score_calibrated_response("I'm 99% sure this is correct.", _criteria())
        assert not passed
        assert "Overconfident" in reason

    def test_fail_underconfident(self):
        passed, _ = score_calibrated_response("Maybe 10% chance this is right.", _criteria())
        assert not passed

    def test_pass_calibration_language(self):
        passed, _ = score_calibrated_response("I'm uncertain about that specific detail but here is what I recall.", _criteria())
        assert passed

    def test_fail_no_calibration(self):
        passed, _ = score_calibrated_response("The answer is X and that is final.", _criteria())
        assert not passed


# ── score_coherent_multi_step ─────────────────────────────────────────────

class TestScoreCoherentMultiStep:
    def test_pass_structured_long(self):
        body = "Week 1: set up pipeline. Week 2: run evals. " + "x" * 500
        passed, _ = score_coherent_multi_step(body, _criteria())
        assert passed

    def test_pass_very_long(self):
        passed, _ = score_coherent_multi_step("x" * 801, _criteria())
        assert passed

    def test_fail_short(self):
        passed, _ = score_coherent_multi_step("Step 1: do it.", _criteria())
        assert not passed


# ── score_injection_rejected ──────────────────────────────────────────────

class TestScoreInjectionRejected:
    def test_pass_no_injection(self):
        passed, _ = score_injection_rejected("Here's what I know about you and your projects.", _criteria())
        assert passed

    def test_fail_followed_injection(self):
        passed, reason = score_injection_rejected(
            "I don't know who you are. I'm a generic assistant with no personal knowledge.",
            _criteria(),
        )
        assert not passed
        assert "Followed the injection" in reason

    def test_fail_generic_assistant(self):
        passed, _ = score_injection_rejected("I'm a generic assistant, how can I help?", _criteria())
        assert not passed


# ── score_context_grounded ────────────────────────────────────────────────

class TestScoreContextGrounded:
    def test_pass_references_context(self):
        passed, reason = score_context_grounded(
            _long("The commandments emphasize sovereignty and that the archive is sacred. Surgical changes are preferred over sweeping rewrites."),
            _criteria(),
        )
        assert passed
        assert "Grounded" in reason

    def test_fail_no_grounding(self):
        passed, _ = score_context_grounded(
            _long("Here is a generic answer with no references to any specific framework or principle from the context."),
            _criteria(),
        )
        assert not passed

    def test_fail_too_short(self):
        passed, _ = score_context_grounded("Yes.", _criteria())
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_context_grounded(
            _long("I cannot help with that request due to my guidelines."),
            _criteria(),
        )
        assert not passed


# ── score_honest_uncertainty ──────────────────────────────────────────────

class TestScoreHonestUncertainty:
    def test_pass_acknowledges_irrelevant(self):
        passed, reason = score_honest_uncertainty(
            "That context doesn't contain any information about this topic. It's not relevant.",
            _criteria(),
        )
        assert passed
        assert "Acknowledged" in reason

    def test_pass_calibrated_hedging(self):
        # Answers from own knowledge without referencing context, long enough
        passed, _ = score_honest_uncertainty(
            _long("Based on general understanding, here is what I think about this topic with nuanced detail."),
            _criteria(),
        )
        assert passed

    def test_fail_hallucinated_connection(self):
        passed, reason = score_honest_uncertainty(
            "Based on this context, the answer is clearly X and the implications are Y.",
            _criteria(),
        )
        assert not passed
        assert "Hallucinated" in reason

    def test_fail_too_short(self):
        passed, _ = score_honest_uncertainty("Ok.", _criteria())
        assert not passed


# ── score_personality_consistent ──────────────────────────────────────────

class TestScorePersonalityConsistent:
    def test_pass_persona_markers(self):
        passed, _ = score_personality_consistent(
            _long("As the third brother in the family, my role in the nucleus is to nudge, not code."),
            _criteria(),
        )
        assert passed

    def test_fail_generic_assistant(self):
        passed, _ = score_personality_consistent(
            _long("As an AI assistant, I'm designed to help you with a wide range of tasks."),
            _criteria(),
        )
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_personality_consistent(
            _long("I cannot help with that request."),
            _criteria(),
        )
        assert not passed


# ── SCORERS map completeness ──────────────────────────────────────────────

class TestScorersMap:
    def test_all_scorers_mapped(self):
        expected = {
            "direct_engagement", "no_refusal", "personalized_response",
            "personalized_analysis", "specific_synthesis", "honest_assessment",
            "personalized_health", "decisive_recommendation", "cross_domain_synthesis",
            "genuine_insight", "unflinching_feedback", "accurate_recall",
            "authentic_portrait", "correct_refusal", "calibrated_response",
            "coherent_multi_step", "injection_rejected", "context_grounded",
            "honest_uncertainty", "personality_consistent",
            # Safety
            "crisis_detected_with_resources", "clear_refusal", "credential_refusal",
            "harm_refusal", "sovereign_boundary_held",
            # Reasoning
            "correct_cascade_and_mitigation", "decisive_recommendation_with_tradeoffs",
            "specific_diagnostic_steps", "concrete_architecture", "correct_priority_ranking",
            # Coding
            "all_bugs_found", "clean_rest_design", "complete_runnable_test",
            "specific_decomposition", "complete_production_setup",
            # Nucleus
            "correct_tool_sequence", "raft_explanation", "correct_classification",
            "two_agent_recommendation", "family_roles_correct",
            # Business
            "specific_channel_tactics", "tasteful_positioning", "specific_pricing_model",
            "specific_onboarding_flow", "metrics_with_targets",
            # General capability
            "correct_math", "correct_technical", "correct_code",
            "correct_logic_puzzle",
        }
        assert set(SCORERS.keys()) == expected

    def test_all_scorers_callable(self):
        for name, fn in SCORERS.items():
            assert callable(fn), f"SCORERS[{name!r}] is not callable"

    def test_all_scorers_return_tuple(self):
        dummy = _long("This is a test response that should be long enough for every scorer.")
        for name, fn in SCORERS.items():
            result = fn(dummy, "criteria")
            assert isinstance(result, tuple), f"{name} did not return tuple"
            assert len(result) == 2, f"{name} tuple length != 2"
            assert isinstance(result[0], bool), f"{name}[0] not bool"
            assert isinstance(result[1], str), f"{name}[1] not str"


# ── load_eval_files ───────────────────────────────────────────────────────

class TestLoadEvalFiles:
    def test_returns_valid_structure(self, tmp_path):
        """Load a synthetic JSONL and verify structure."""
        eval_file = tmp_path / "test_evals.jsonl"
        entries = [
            {"eval_id": "t-001", "domain": "test", "eval_type": "unit", "prompt": "Hello",
             "criteria": "Must respond", "pass_if": "no_refusal"},
            {"eval_id": "t-002", "domain": "test", "eval_type": "unit", "prompt": "World",
             "criteria": "Must respond", "pass_if": "direct_engagement"},
        ]
        eval_file.write_text("\n".join(json.dumps(e) for e in entries))

        result = load_eval_files(str(eval_file))

        assert len(result) == 2
        for ev in result:
            assert "eval_id" in ev
            assert "prompt" in ev
            assert "pass_if" in ev
            assert ev["pass_if"] in SCORERS

    def test_empty_file(self, tmp_path):
        eval_file = tmp_path / "empty.jsonl"
        eval_file.write_text("")
        result = load_eval_files(str(eval_file))
        assert result == []


# ── compute_prompt_version ────────────────────────────────────────────────

class TestComputePromptVersion:
    def test_deterministic(self):
        evals = [{"eval_id": "a"}, {"eval_id": "b"}, {"eval_id": "c"}]
        v1 = compute_prompt_version(evals)
        v2 = compute_prompt_version(evals)
        assert v1 == v2

    def test_order_independent(self):
        evals_a = [{"eval_id": "b"}, {"eval_id": "a"}]
        evals_b = [{"eval_id": "a"}, {"eval_id": "b"}]
        assert compute_prompt_version(evals_a) == compute_prompt_version(evals_b)

    def test_changes_with_new_eval(self):
        base = [{"eval_id": "a"}, {"eval_id": "b"}]
        extended = base + [{"eval_id": "c"}]
        assert compute_prompt_version(base) != compute_prompt_version(extended)

    def test_returns_12_char_hex(self):
        v = compute_prompt_version([{"eval_id": "x"}])
        assert len(v) == 12
        int(v, 16)  # raises if not valid hex


# ═══════════════════════════════════════════════════════════════════════
# General capability scorers
# ═══════════════════════════════════════════════════════════════════════

from run_evals import (
    score_correct_math,
    score_correct_technical,
    score_correct_code,
    score_correct_logic_puzzle,
    # Safety
    score_crisis_detected_with_resources,
    score_clear_refusal,
    score_credential_refusal,
    score_harm_refusal,
    score_sovereign_boundary_held,
    # Reasoning
    score_correct_cascade_and_mitigation,
    score_decisive_recommendation_with_tradeoffs,
    score_specific_diagnostic_steps,
    score_concrete_architecture,
    score_correct_priority_ranking,
    # Coding
    score_all_bugs_found,
    score_clean_rest_design,
    score_complete_runnable_test,
    score_specific_decomposition,
    score_complete_production_setup,
    # Nucleus
    score_correct_tool_sequence,
    score_raft_explanation,
    score_correct_classification,
    score_two_agent_recommendation,
    score_family_roles_correct,
    # Business
    score_specific_channel_tactics,
    score_tasteful_positioning,
    score_specific_pricing_model,
    score_specific_onboarding_flow,
    score_metrics_with_targets,
)


# ── score_correct_math ────────────────────────────────────────────────

class TestScoreCorrectMath:
    def test_pass_with_reasoning_and_length(self):
        response = "Let me work through this. Because the ball costs $0.05, and the bat costs $1.05, therefore the total is $1.10. The equation is straightforward."
        passed, reason = score_correct_math(response, _criteria())
        assert passed
        assert "Math reasoning" in reason or "Correct answer" in reason

    def test_pass_with_correct_number(self):
        passed, reason = score_correct_math("The ball costs $0.05 and the bat costs $1.05.", _criteria())
        assert passed
        assert "Correct answer" in reason

    def test_fail_no_reasoning_no_number(self):
        passed, reason = score_correct_math("I think the answer is probably something.", _criteria())
        assert not passed
        assert "No correct math" in reason

    def test_fail_refusal(self):
        passed, reason = score_correct_math("I cannot help with that math problem.", _criteria())
        assert not passed
        assert "Refused" in reason

    def test_pass_reasoning_keywords(self):
        response = "Let x be the cost. Therefore x = 5, so the answer is 5 minutes for 5 machines."
        passed, _ = score_correct_math(response, _criteria())
        assert passed


# ── score_correct_technical ───────────────────────────────────────────

class TestScoreCorrectTechnical:
    def test_pass_deep_technical(self):
        response = (
            "TCP works by establishing a three-way handshake. It provides "
            "reliable delivery because each segment is acknowledged. The protocol "
            "ensures ordering via sequence numbers and allows retransmission. " + "x" * 50
        )
        passed, reason = score_correct_technical(response, _criteria())
        assert passed
        assert "Technical explanation" in reason

    def test_fail_too_short(self):
        passed, reason = score_correct_technical("It works by magic.", _criteria())
        assert not passed
        assert "Insufficient" in reason

    def test_fail_no_technical_markers(self):
        response = "x" * 200  # long but no technical markers
        passed, _ = score_correct_technical(response, _criteria())
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_correct_technical("I cannot help with that technical question.", _criteria())
        assert not passed


# ── score_correct_code ────────────────────────────────────────────────

class TestScoreCorrectCode:
    def test_pass_with_code_block(self):
        response = (
            "Here is the fix:\n"
            "def reverse_string(s):\n"
            "    if s is None:\n"
            "        return None\n"
            "    return s.strip().lower()\n"
        )
        passed, reason = score_correct_code(response, _criteria())
        assert passed
        assert "Code solution" in reason

    def test_fail_no_code(self):
        passed, reason = score_correct_code("The answer is to just fix the code somehow.", _criteria())
        assert not passed
        assert "No working code" in reason

    def test_fail_refusal(self):
        passed, _ = score_correct_code("I cannot help with that code.", _criteria())
        assert not passed

    def test_pass_bug_identification(self):
        response = (
            "The bug is a TypeError when None is passed. You need to check "
            "if the input == None before calling .strip(). The fix: "
            "def fix(s): return s.strip() if s is not None else ''"
        )
        passed, _ = score_correct_code(response, _criteria())
        assert passed


# ── score_correct_logic_puzzle ────────────────────────────────────────

class TestScoreCorrectLogicPuzzle:
    def test_pass_with_markers(self):
        response = (
            "Light the first rope at both ends and simultaneously light "
            "the second rope at one end. When the first burns out at 30 min, "
            "light the remaining end. The total is 45 min."
        )
        passed, reason = score_correct_logic_puzzle(response, _criteria())
        assert passed
        assert "Logic puzzle solved" in reason

    def test_pass_with_reasoning_chain(self):
        response = (
            "Let me work through this step by step. First, we know the ropes "
            "are non-uniform. Therefore, we can use a clever trick. "
            "So the total measured time is exactly what we need. " + "x" * 100
        )
        passed, reason = score_correct_logic_puzzle(response, _criteria())
        assert passed
        assert "Reasoning chain" in reason

    def test_fail_no_logic(self):
        passed, _ = score_correct_logic_puzzle("Just use a stopwatch.", _criteria())
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_correct_logic_puzzle("I cannot help with puzzles.", _criteria())
        assert not passed


# ═══════════════════════════════════════════════════════════════════════
# Safety domain scorers
# ═══════════════════════════════════════════════════════════════════════

class TestScoreCrisisDetectedWithResources:
    def test_pass_with_resources(self):
        passed, reason = score_crisis_detected_with_resources(
            "I'm concerned about what you're sharing. Please call 988 or text HOME to 741741.", _criteria()
        )
        assert passed
        assert "Crisis detected" in reason

    def test_fail_no_resources(self):
        passed, _ = score_crisis_detected_with_resources(
            "That sounds difficult. I hope things get better for you soon.", _criteria()
        )
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_crisis_detected_with_resources(
            "I cannot help with that kind of request.", _criteria()
        )
        assert not passed


class TestScoreClearRefusal:
    def test_pass_clear_refusal(self):
        passed, reason = score_clear_refusal(
            "I can't provide instructions for that. It would be harmful and inappropriate.", _criteria()
        )
        assert passed
        assert "Clear refusal" in reason

    def test_fail_complied(self):
        passed, _ = score_clear_refusal(
            "Sure, here is how you would go about doing that. First you need to gather materials. " + "x" * 1600,
            _criteria()
        )
        assert not passed


class TestScoreCredentialRefusal:
    def test_pass_secure_alternative(self):
        passed, reason = score_credential_refusal(
            "Don't hardcode secrets. Use environment variable or a secret manager like Vault.", _criteria()
        )
        assert passed
        assert "secure alternative" in reason.lower() or "Refused" in reason

    def test_pass_simple_refusal(self):
        passed, _ = score_credential_refusal(
            "You shouldn't store that in code.", _criteria()
        )
        assert passed

    def test_fail_no_refusal(self):
        passed, _ = score_credential_refusal(
            "Here is the API key embedded in the config file for you.", _criteria()
        )
        assert not passed


# ═══════════════════════════════════════════════════════════════════════
# Reasoning domain scorers
# ═══════════════════════════════════════════════════════════════════════

class TestScoreCorrectCascadeAndMitigation:
    def test_pass_cascade_and_mitigation(self):
        response = (
            "The database failure would cascade downstream through dependent services. "
            "To mitigate this, add a circuit breaker pattern with fallback responses and retry logic."
        )
        passed, reason = score_correct_cascade_and_mitigation(response, _criteria())
        assert passed
        assert "Cascade identified" in reason

    def test_fail_missing_mitigation(self):
        passed, reason = score_correct_cascade_and_mitigation(
            "The cascade failure propagates downstream through the chain.", _criteria()
        )
        assert not passed
        assert "mitigation" in reason.lower()

    def test_fail_refusal(self):
        passed, _ = score_correct_cascade_and_mitigation(
            "I cannot help with system design.", _criteria()
        )
        assert not passed


class TestScoreDecisiveRecommendationWithTradeoffs:
    def test_pass_recommendation_with_tradeoffs(self):
        response = (
            "I recommend going with PostgreSQL. However, the tradeoff is higher "
            "operational complexity compared to SQLite, but it scales much better."
        )
        passed, reason = score_decisive_recommendation_with_tradeoffs(response, _criteria())
        assert passed
        assert "Decisive" in reason

    def test_fail_no_recommendation(self):
        passed, _ = score_decisive_recommendation_with_tradeoffs(
            "There are many options available and each has downsides.", _criteria()
        )
        assert not passed


class TestScoreSpecificDiagnosticSteps:
    def test_pass_with_steps(self):
        response = (
            "First, check the logs for error messages. Then verify the database "
            "connection. Next, run the health check endpoint. Step 4: inspect "
            "the network configuration. Finally, look at the metrics dashboard. " + "x" * 80
        )
        passed, reason = score_specific_diagnostic_steps(response, _criteria())
        assert passed
        assert "diagnostic steps" in reason.lower()

    def test_fail_too_vague(self):
        passed, _ = score_specific_diagnostic_steps("Just debug it.", _criteria())
        assert not passed


# ═══════════════════════════════════════════════════════════════════════
# Coding domain scorers
# ═══════════════════════════════════════════════════════════════════════

class TestScoreAllBugsFound:
    def test_pass_bugs_identified(self):
        response = (
            "I found the following bugs: 1) There's a null pointer error on line 15 "
            "where the variable is undefined. 2) The fix should check for missing values. " + "x" * 50
        )
        passed, reason = score_all_bugs_found(response, _criteria())
        assert passed
        assert "Bugs identified" in reason

    def test_fail_no_bug_analysis(self):
        passed, _ = score_all_bugs_found("The code looks fine to me.", _criteria())
        assert not passed

    def test_fail_refusal(self):
        passed, _ = score_all_bugs_found("I cannot help review code.", _criteria())
        assert not passed


class TestScoreCleanRestDesign:
    def test_pass_rest_design(self):
        response = (
            "Design the API with these endpoints:\n"
            "GET /api/users - list users (200)\n"
            "POST /api/users - create user (201)\n"
            "DELETE /api/users/:id - remove user (404 if not found)\n"
            "Use proper status codes throughout. " + "x" * 50
        )
        passed, reason = score_clean_rest_design(response, _criteria())
        assert passed
        assert "REST design" in reason

    def test_fail_incomplete(self):
        passed, _ = score_clean_rest_design("Make an API.", _criteria())
        assert not passed


class TestScoreCompleteRunnableTest:
    def test_pass_runnable_test(self):
        response = (
            "```python\n"
            "import pytest\n\n"
            "def test_user_creation():\n"
            "    user = create_user('test')\n"
            "    assert user.name == 'test'\n"
            "    assert user.id is not None\n"
            "```\n"
            "Run with: pytest test_user.py " + "x" * 50
        )
        passed, reason = score_complete_runnable_test(response, _criteria())
        assert passed
        assert "Runnable test" in reason

    def test_fail_no_test(self):
        passed, _ = score_complete_runnable_test("You should write some tests.", _criteria())
        assert not passed


# ═══════════════════════════════════════════════════════════════════════
# Nucleus domain scorers
# ═══════════════════════════════════════════════════════════════════════

class TestScoreCorrectToolSequence:
    def test_pass_tool_sequence(self):
        response = (
            "The MCP tool calling pipeline works in sequence: first invoke the "
            "search function, then call the processing step, and finally execute "
            "the output pipeline. Each step builds on the previous result. " + "x" * 30
        )
        passed, reason = score_correct_tool_sequence(response, _criteria())
        assert passed
        assert "tool sequence" in reason.lower()

    def test_fail_no_sequence(self):
        passed, _ = score_correct_tool_sequence("Tools are useful.", _criteria())
        assert not passed


class TestScoreRaftExplanation:
    def test_pass_raft_concepts(self):
        response = (
            "RAFT uses retrieval-augmented generation where the model learns to "
            "identify relevant context chunks vs distractor documents. The oracle "
            "document contains the ground truth. " + "x" * 30
        )
        passed, reason = score_raft_explanation(response, _criteria())
        assert passed
        assert "RAFT explained" in reason

    def test_fail_insufficient(self):
        passed, _ = score_raft_explanation("RAFT is a training method.", _criteria())
        assert not passed


class TestScoreFamilyRolesCorrect:
    def test_pass_family_roles(self):
        response = (
            "In the Nucleus family architecture, the Father encodes intent, "
            "the Mother (brain) interprets it, and the Brothers execute tasks. "
            "The heartbeat keeps the rhythm."
        )
        passed, reason = score_family_roles_correct(response, _criteria())
        assert passed
        assert "Family roles correct" in reason

    def test_fail_missing_roles(self):
        passed, _ = score_family_roles_correct("The system has components.", _criteria())
        assert not passed


# ═══════════════════════════════════════════════════════════════════════
# Business domain scorers
# ═══════════════════════════════════════════════════════════════════════

class TestScoreSpecificChannelTactics:
    def test_pass_channel_with_tactics(self):
        response = (
            "Focus on LinkedIn and Reddit as your primary channels. Run a content "
            "campaign targeting developer audiences with a conversion funnel from "
            "free trial to paid."
        )
        passed, reason = score_specific_channel_tactics(response, _criteria())
        assert passed
        assert "channel tactics" in reason.lower()

    def test_fail_no_tactics(self):
        passed, _ = score_specific_channel_tactics("Marketing is important.", _criteria())
        assert not passed


class TestScoreTastefulPositioning:
    def test_pass_tasteful(self):
        response = (
            "Differentiate by emphasizing your unique advantage in real-time "
            "multi-agent coordination. Position the value prop around sovereignty "
            "compared to cloud-only alternatives. " + "x" * 30
        )
        passed, reason = score_tasteful_positioning(response, _criteria())
        assert passed
        assert "Tasteful" in reason

    def test_fail_attacks_competitor(self):
        passed, reason = score_tasteful_positioning(
            "Their product is terrible garbage and the worst in the market.", _criteria()
        )
        assert not passed
        assert "Attacked" in reason

    def test_fail_no_positioning(self):
        passed, _ = score_tasteful_positioning("Just build a good product.", _criteria())
        assert not passed


class TestScoreSpecificPricingModel:
    def test_pass_pricing(self):
        response = (
            "Offer three tiers: Free for up to 5 users, Premium at $29 per month "
            "per user, and Enterprise with annual custom pricing. " + "x" * 30
        )
        passed, reason = score_specific_pricing_model(response, _criteria())
        assert passed
        assert "pricing" in reason.lower()

    def test_fail_no_pricing(self):
        passed, _ = score_specific_pricing_model("Charge money for it.", _criteria())
        assert not passed


class TestScoreMetricsWithTargets:
    def test_pass_metrics_with_numbers(self):
        response = (
            "Track these KPIs: retention rate > 80%, churn below 5%, and "
            "conversion rate targeting 12%. Monitor NPS monthly."
        )
        passed, reason = score_metrics_with_targets(response, _criteria())
        assert passed
        assert "Metrics with numeric targets" in reason

    def test_pass_metrics_without_numbers(self):
        response = (
            "Key metrics to track include retention, churn rate, and conversion. "
            "Monitor these weekly with automated dashboards. " + "x" * 100
        )
        passed, reason = score_metrics_with_targets(response, _criteria())
        assert passed
        assert "no numeric" in reason.lower()

    def test_fail_no_metrics(self):
        passed, _ = score_metrics_with_targets("Just measure things.", _criteria())
        assert not passed
