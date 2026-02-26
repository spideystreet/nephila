"""Pydantic model for ANSM Thésaurus drug interaction records."""

from pydantic import BaseModel, ConfigDict

CONSTRAINT_LEVELS = frozenset(
    {
        "contre-indication",
        "association déconseillée",
        "précaution d'emploi",
        "a prendre en compte",
        "à prendre en compte",
    }
)


class InteractionRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    substance_a: str
    substance_b: str
    niveau_contrainte: str
    nature_risque: str | None = None
    conduite_a_tenir: str | None = None
