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


class ZoneVitrage(BaseModel):
    zone: str           # "G1", "G2", …
    Ug: float           # W/(m²·K)
    Psi_g: float        # W/(m·K)
    Sg: float | None = None   # facteur solaire du vitrage


class DetailsCalcul(BaseModel):
    chassis_id: int
    geo_type: str
    Uf_moyen: float | None = None
    Af_total: float | None = None
    Ag_total: float | None = None
    surface_totale: float | None = None
    zones_vitrage: list[ZoneVitrage] = []
    alpha: float | None = None      # coeff. absorption couleur (XP P50-777)
    HE: float = 25.0                # résistance superficielle ext. [W/(m²·K)] — EN ISO 6946:2017
    Psi_g_defaut: float = 0.08      # valeur Ψg par défaut intercalaire alu — EN ISO 10077-1
    normes: list[str] = [
        "EN ISO 10077-1 (juin 2012)",
        "XP P50-777 (décembre 2011)",
        "EN ISO 6946:2017",
    ]


class CalculResult(BaseModel):
    menuiserie_seule: ResultatMenuiserie
    avec_volet: ResultatVolet | None = None
    details: DetailsCalcul
