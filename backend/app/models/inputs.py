from pydantic import BaseModel, Field


class VitragInput(BaseModel):
    zone: str = Field(..., description="G1, G2, ... ou P1, P2, ...")
    composition: str
    intercalaire: str = "Warm-Edge"


class VoletInput(BaseModel):
    actif: bool = False
    type: str | None = None
    isolation_acoustique: str = "T"  # T, P0, P1, P2, P3, P4


class CalculInput(BaseModel):
    famille: str
    chassis: str
    couleur: str
    hauteur_mm: float = Field(..., gt=0, description="Hauteur dos de profil en mm")
    largeur_mm: float = Field(..., gt=0, description="Largeur dos de profil en mm")
    volet: VoletInput = VoletInput()
    vitrages: list[VitragInput] = []
    panneaux: list[VitragInput] = []
