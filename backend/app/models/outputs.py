from pydantic import BaseModel


class ResultatMenuiserie(BaseModel):
    Uw: float | None = None      # W/m².K (Ud pour portes)
    Sw: float | None = None      # sans unité
    Tlw: float | None = None     # % (0-100)
    label_uw: str = "Uw"         # "Uw" ou "Ud"


class ResultatVolet(BaseModel):
    rR: float | None = None      # m².K/W
    Ujn: float | None = None     # W/m².K
    Ubb_jn: float | None = None  # W/m².K
    Uc: float | None = None      # W/m².K


class DetailsCalcul(BaseModel):
    chassis_id: int
    geo_type: str
    Uf_moyen: float | None = None
    Af_total: float | None = None
    Ag_total: float | None = None
    surface_totale: float | None = None
    normes: list[str] = [
        "EN ISO 10077-1 (juin 2012)",
        "XP P50-777 (décembre 2011)",
    ]


class CalculResult(BaseModel):
    menuiserie_seule: ResultatMenuiserie
    avec_volet: ResultatVolet | None = None
    details: DetailsCalcul
