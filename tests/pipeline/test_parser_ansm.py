"""Unit tests for the ANSM Thésaurus PDF parser heuristics."""
import pytest

from nephila.pipeline.io.parser_ansm import _detect_constraint, _is_substance_a


class TestIsSubstanceA:
    def test_valid_substance(self):
        assert _is_substance_a("AMIODARONE") is True

    def test_valid_substance_with_spaces(self):
        assert _is_substance_a("INHIBITEURS DE L'ECA") is True

    def test_valid_substance_with_slash(self):
        assert _is_substance_a("ACIDE ACETYLSALICYLIQUE/ASPIRINE") is True

    def test_valid_substance_with_parens(self):
        assert _is_substance_a("ANTICOAGULANTS ORAUX (AVK)") is True

    def test_substance_b_marker_excluded(self):
        assert _is_substance_a("+ WARFARINE") is False

    def test_voir_excluded(self):
        assert _is_substance_a("Voir aussi rubrique X") is False

    def test_voir_lowercase_excluded(self):
        assert _is_substance_a("voir rubrique") is False

    def test_page_number_excluded(self):
        assert _is_substance_a("2") is False

    def test_large_page_number_excluded(self):
        assert _is_substance_a("183") is False

    def test_lowercase_line_excluded(self):
        assert _is_substance_a("risque de saignement accru") is False

    def test_mixed_case_line_excluded(self):
        assert _is_substance_a("Précaution d'emploi") is False

    def test_too_short_excluded(self):
        # Less than 3 chars — doesn't match regex
        assert _is_substance_a("AB") is False

    def test_accented_uppercase(self):
        assert _is_substance_a("ÉRYTHROMYCINE") is True


class TestDetectConstraint:
    def test_contre_indication(self):
        assert _detect_constraint("Contre-indication formelle") == "Contre-indication"

    def test_contre_indication_alias(self):
        assert _detect_constraint("CI absolue") == "Contre-indication"

    def test_association_deconseillee(self):
        assert _detect_constraint("association déconseillée en raison du risque") == "Association déconseillée"

    def test_asdec_alias(self):
        assert _detect_constraint("ASDEC — risque de torsades") == "Association déconseillée"

    def test_precaution_emploi(self):
        assert _detect_constraint("précaution d'emploi recommandée") == "Précaution d'emploi"

    def test_pe_alias(self):
        assert _detect_constraint("PE : surveiller la kaliémie") == "Précaution d'emploi"

    def test_apec(self):
        assert _detect_constraint("à prendre en compte") == "A prendre en compte"

    def test_apec_alias(self):
        assert _detect_constraint("APEC") == "A prendre en compte"

    def test_priority_ci_over_pe(self):
        # CI takes priority over PE
        result = _detect_constraint("Contre-indication sauf précaution d'emploi")
        assert result == "Contre-indication"

    def test_no_constraint(self):
        assert _detect_constraint("texte descriptif sans niveau") is None
