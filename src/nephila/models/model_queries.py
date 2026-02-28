"""Pydantic models for agent SQL query results."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class GeneriqueResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cis: int
    denomination: str
    type_generique: str
    etat_commercialisation: str | None = None


class RcpRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    texte_info_importante: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
