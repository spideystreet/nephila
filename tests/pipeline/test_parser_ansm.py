"""Unit tests for the ANSM Thésaurus PDF parser heuristics."""
from pathlib import Path

import pytest

from nephila.pipeline.io.parser_ansm import (
    _CLASS_MEMBERS_RE,
    _VOIR_AUSSI_RE,
    _detect_constraint,
    _is_substance_a,
    parse_thesaurus_classes,
)


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


class TestClassMembersRegex:
    def test_simple_list(self):
        m = _CLASS_MEMBERS_RE.match("(warfarine, acenocoumarol, fluindione)")
        assert m is not None
        assert "warfarine" in m.group(1)

    def test_nested_parens(self):
        """Lines like '(acetazolamide, sodium (bicarbonate de), trometamol)' must match."""
        m = _CLASS_MEMBERS_RE.match("(acetazolamide, sodium (bicarbonate de), trometamol)")
        assert m is not None
        assert "sodium (bicarbonate de)" in m.group(1)

    def test_no_comma_no_match(self):
        """Single-element parens are not member lists."""
        assert _CLASS_MEMBERS_RE.match("(voir aussi)") is None

    def test_non_paren_line(self):
        assert _CLASS_MEMBERS_RE.match("warfarine, acenocoumarol") is None


class TestVoirAussiRegex:
    def test_simple(self):
        m = _VOIR_AUSSI_RE.match("Voir aussi : antiagrégants plaquettaires")
        assert m is not None
        assert m.group(1) == "antiagrégants plaquettaires"

    def test_multiple_classes(self):
        m = _VOIR_AUSSI_RE.match("Voir aussi : bisphosphonates - médicaments néphrotoxiques")
        assert m is not None
        assert "bisphosphonates" in m.group(1)
        assert "médicaments néphrotoxiques" in m.group(1)

    def test_lowercase_voir(self):
        m = _VOIR_AUSSI_RE.match("voir aussi : folates")
        assert m is not None

    def test_no_match_on_random_text(self):
        assert _VOIR_AUSSI_RE.match("risque de saignement") is None


@pytest.mark.integration
class TestParseThesaurusClasses:
    def test_returns_nonempty(self):
        records = parse_thesaurus_classes(Path("data/bronze/ansm/thesaurus.pdf"))
        assert len(records) > 800

    def test_warfarine_mapped_to_anticoagulants(self):
        records = parse_thesaurus_classes(Path("data/bronze/ansm/thesaurus.pdf"))
        warfarine_classes = {
            r["classe_ansm"] for r in records if r["substance_dci"] == "warfarine"
        }
        assert "ANTICOAGULANTS ORAUX" in warfarine_classes

    def test_both_sources_present(self):
        records = parse_thesaurus_classes(Path("data/bronze/ansm/thesaurus.pdf"))
        sources = {r["source"] for r in records}
        assert sources == {"parenthetical", "voir_aussi"}
