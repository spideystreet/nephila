"""Unit tests for get_rcp CIS validation — no DB required."""

import pytest

from nephila.agent.tools.tool_get_rcp import get_rcp


class TestGetRcpCisValidation:
    def test_non_digit_cis_returns_error(self):
        result = get_rcp.invoke({"cis": "aspirine"})
        assert "Invalid CIS code" in result
        assert "search_drug" in result

    def test_whitespace_cis_returns_error(self):
        result = get_rcp.invoke({"cis": "  "})
        assert "Invalid CIS code" in result

    def test_mixed_alpha_digit_returns_error(self):
        result = get_rcp.invoke({"cis": "12abc"})
        assert "Invalid CIS code" in result

    @pytest.mark.integration
    def test_valid_digit_cis_not_rejected(self):
        """A valid digit CIS should NOT trigger the validation error."""
        result = get_rcp.invoke({"cis": " 60001154 "})
        assert "Invalid CIS code" not in result
