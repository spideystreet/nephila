"""Unit tests for _normalize, _substance_matches_query, and _resolve_ansm_names."""
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine

from nephila.agent.tools.tool_check_interactions import (
    _normalize,
    _resolve_ansm_names,
    _substance_matches_query,
)
from nephila.pipeline.config_pipeline import PipelineSettings


class TestNormalize:
    def test_strips_accents(self):
        assert _normalize("Méthotrexate") == "methotrexate"

    def test_lowercases(self):
        assert _normalize("AMIODARONE") == "amiodarone"

    def test_strips_accents_and_lowercases(self):
        assert _normalize("ANTI-INFLAMMATOIRES NON STÉROÏDIENS") == "anti-inflammatoires non steroidiens"

    def test_already_ascii(self):
        assert _normalize("aspirin") == "aspirin"

    def test_empty_string(self):
        assert _normalize("") == ""


class TestSubstanceMatchesQuery:
    def test_exact_token_match(self):
        assert _substance_matches_query("AMIODARONE", "amiodarone", "simvastatine") is True

    def test_no_overlap_returns_false(self):
        assert _substance_matches_query("LITHIUM", "amiodarone", "warfarine") is False

    def test_partial_class_name_match(self):
        """Class name shares tokens with one of the query terms."""
        assert _substance_matches_query(
            "ANTI-INFLAMMATOIRES NON STÉROÏDIENS",
            "ibuprofène",
            "anti-inflammatoires",
        ) is True

    def test_accented_substance_matches_unaccented_query(self):
        """Accent normalization ensures cross-accent matching."""
        assert _substance_matches_query("Méthotrexate", "methotrexate", "") is True

    def test_false_positive_guard(self):
        """flucloxacilline must NOT match amoxicilline or paracetamol."""
        assert _substance_matches_query("FLUCLOXACILLINE", "amoxicilline", "paracetamol") is False

    def test_hyphen_splits_into_tokens(self):
        """Hyphens are treated as token separators."""
        assert _substance_matches_query("ANTI-INFLAMMATOIRES", "anti", "") is True

    def test_plus_splits_into_tokens(self):
        """'+' is treated as a token separator."""
        assert _substance_matches_query("A+B", "a", "") is True

    def test_matches_second_query_when_first_fails(self):
        """Matching either query_a or query_b is sufficient."""
        assert _substance_matches_query("WARFARINE", "amiodarone", "warfarine") is True


class TestResolveAnsmNames:
    def test_fallback_on_broken_engine(self):
        """When the DB query fails, return [substance] as fallback."""
        engine = MagicMock()
        engine.connect.side_effect = Exception("connection refused")
        assert _resolve_ansm_names("warfarine", engine) == ["warfarine"]

    def test_fallback_on_no_rows(self):
        """When the mapping table has no match, return [substance]."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = []
        engine = MagicMock()
        engine.connect.return_value = mock_conn
        assert _resolve_ansm_names("unknownsubstance", engine) == ["unknownsubstance"]


@pytest.mark.integration
class TestResolveAnsmNamesIntegration:
    def test_warfarine_resolves_to_classes(self):
        """warfarine should resolve to at least ANTICOAGULANTS ORAUX."""
        settings = PipelineSettings()
        engine = create_engine(settings.postgres_dsn)
        names = _resolve_ansm_names("warfarine", engine)
        upper_names = {n.upper() for n in names}
        assert "ANTICOAGULANTS ORAUX" in upper_names

    def test_fluconazole_has_no_class_mapping(self):
        """fluconazole is indexed by DCI, not by class — should return [fluconazole]."""
        settings = PipelineSettings()
        engine = create_engine(settings.postgres_dsn)
        names = _resolve_ansm_names("fluconazole", engine)
        assert names == ["fluconazole"]
