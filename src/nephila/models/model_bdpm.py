"""Pydantic models for BDPM source files — used for sample validation before raw loading."""
from pydantic import BaseModel, ConfigDict, field_validator


class CISRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cis: str
    denomination: str
    forme_pharma: str
    voies_admin: str
    statut_amm: str | None = None
    type_amm: str | None = None
    etat_commercialisation: str | None = None
    date_amm: str | None = None
    statut_bdm: str | None = None
    num_autorisation_eu: str | None = None
    titulaire: str | None = None
    surveillance_renforcee: str | None = None

    @field_validator("cis")
    @classmethod
    def cis_must_be_numeric(cls, v: str) -> str:
        if not v.strip().isdigit():
            raise ValueError(f"Invalid CIS (non-numeric): {v!r}")
        return v.strip()


class CIPRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cis: str
    cip7: str | None = None
    libelle_presentation: str | None = None
    statut_admin: str | None = None
    etat_commercialisation: str | None = None
    date_declaration_commercialisation: str | None = None
    cip13: str | None = None
    agrement_collectivites: str | None = None
    taux_remboursement: str | None = None
    prix_medicament: str | None = None
    indicateurs_remboursement: str | None = None

    @field_validator("cip13")
    @classmethod
    def cip13_length(cls, v: str | None) -> str | None:
        if v and len(v.strip()) != 13:
            raise ValueError(f"CIP13 must be 13 characters: {v!r}")
        return v


class CompositionRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cis: str
    designation_element: str | None = None
    code_substance: str | None = None
    denomination_substance: str | None = None
    dosage: str | None = None
    reference_dosage: str | None = None
    nature_composant: str | None = None
    num_liaison_sa_ft: str | None = None


class GeneriqueRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_groupe: str
    libelle_groupe: str | None = None
    cis: str
    type_generique: str | None = None
    num_tri: str | None = None
