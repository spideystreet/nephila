"""Verify CRITICAL_LEVELS is a single source of truth across nodes."""

from nephila.agent.model_state import CRITICAL_LEVELS
from nephila.agent.nodes import node_guardrail, node_warn


class TestCriticalLevelsSingleSource:
    def test_guardrail_uses_model_state_constant(self):
        assert node_guardrail.CRITICAL_LEVELS is CRITICAL_LEVELS

    def test_warn_uses_model_state_constant(self):
        assert node_warn.CRITICAL_LEVELS is CRITICAL_LEVELS

    def test_contains_expected_levels(self):
        assert "contre-indication" in CRITICAL_LEVELS
        assert "association déconseillée" in CRITICAL_LEVELS
        assert len(CRITICAL_LEVELS) == 2
