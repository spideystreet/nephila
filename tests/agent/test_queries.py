"""Unit and integration tests for nephila.agent.queries."""

from unittest.mock import MagicMock, patch

import pytest

from nephila.agent import queries
from nephila.models.model_ansm import InteractionRow
from nephila.models.model_queries import GeneriqueResult, RcpRow


class TestGetEngine:
    def test_returns_singleton(self):
        """Calling _get_engine twice returns the same engine instance."""
        queries._engine = None
        mock_engine = MagicMock()
        with (
            patch("nephila.agent.queries.PipelineSettings"),
            patch("nephila.agent.queries.create_engine", return_value=mock_engine),
        ):
            try:
                e1 = queries._get_engine()
                e2 = queries._get_engine()
                assert e1 is e2
                assert e1 is mock_engine
            finally:
                queries._engine = None


class TestResolveAnsmClasses:
    def test_fallback_on_broken_engine(self):
        """When the DB query fails, return [substance] as fallback."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("connection refused")
        with patch.object(queries, "_get_engine", return_value=mock_engine):
            result = queries.resolve_ansm_classes("warfarine")
        assert result == ["warfarine"]

    def test_fallback_on_no_rows(self):
        """When the mapping table has no match, return [substance]."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn
        with patch.object(queries, "_get_engine", return_value=mock_engine):
            result = queries.resolve_ansm_classes("unknownsubstance")
        assert result == ["unknownsubstance"]


@pytest.mark.integration
class TestResolveAnsmClassesIntegration:
    def test_warfarine_resolves_to_classes(self):
        """warfarine should resolve to at least ANTICOAGULANTS ORAUX."""
        queries._engine = None
        names = queries.resolve_ansm_classes("warfarine")
        upper_names = {n.upper() for n in names}
        assert "ANTICOAGULANTS ORAUX" in upper_names

    def test_fluconazole_has_no_class_mapping(self):
        """fluconazole is indexed by DCI, not by class — should return [fluconazole]."""
        queries._engine = None
        names = queries.resolve_ansm_classes("fluconazole")
        assert names == ["fluconazole"]


@pytest.mark.integration
class TestFindInteractionsIntegration:
    def test_returns_interaction_rows(self):
        """Known interaction pair returns validated InteractionRow instances."""
        queries._engine = None
        rows = queries.find_interactions("amiodarone", "simvastatine")
        assert len(rows) > 0
        assert all(isinstance(r, InteractionRow) for r in rows)

    def test_unknown_pair_returns_empty(self):
        queries._engine = None
        rows = queries.find_interactions("paracetamol", "eau")
        assert rows == []


@pytest.mark.integration
class TestFindGenericsByCisIntegration:
    def test_returns_generique_results(self):
        """Known princeps CIS returns validated GeneriqueResult instances."""
        queries._engine = None
        rows = queries.find_generics_by_cis(60001154)
        assert len(rows) > 0
        assert all(isinstance(r, GeneriqueResult) for r in rows)

    def test_unknown_cis_returns_empty(self):
        queries._engine = None
        rows = queries.find_generics_by_cis(99999999)
        assert rows == []


@pytest.mark.integration
class TestGetRcpInfoIntegration:
    def test_returns_rcp_rows(self):
        """Known CIS with info_importante returns validated RcpRow instances."""
        queries._engine = None
        rows = queries.get_rcp_info(60001154)
        # May or may not have rows depending on data, but should not error
        assert all(isinstance(r, RcpRow) for r in rows)
