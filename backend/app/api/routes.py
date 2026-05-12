"""
Routes FastAPI — Calculateur de performances thermiques JANNEAU
"""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.calculator import (
    _chassis_list,
    _couleurs_db,
    _get_chassis,
    _geometry_db,
    _psi_g_db,
    _vitrages_db,
    _volets_db,
    calculer,
)
from app.models.inputs import CalculInput
from app.models.outputs import CalculResult

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Référentiels (dropdowns)
# ---------------------------------------------------------------------------

@router.get("/familles")
def get_familles() -> list[str]:
    """Liste des familles de produits."""
    seen = set()
    result = []
    for c in _chassis_list():
        f = c.get("famille")
        if f and f not in seen:
            seen.add(f)
            result.append(f)
    return result


@router.get("/chassis")
def get_chassis(famille: str | None = None) -> list[dict]:
    """Liste des châssis, filtrée optionnellement par famille."""
    chassis = _chassis_list()
    if famille:
        chassis = [c for c in chassis if c.get("famille") == famille]
    # Exclure les châssis dont la géométrie n'est pas supportée dans le MVP
    geo_db = _geometry_db()
    supported_types = {
        "1_vantail", "2_vantaux", "3_vantaux", "4_vantaux",
        "2_vantaux_1_fixe_lateral", "2_vantaux_2_fixes_lateraux",
        "porte_soubassement",
    }
    result = []
    for c in chassis:
        geo = geo_db.get(str(c["id"]))
        supported = geo is not None and geo["geo_type"] in supported_types
        result.append({**c, "supporte": supported})
    return result


@router.get("/chassis/{chassis_id}/info")
def get_chassis_info(chassis_id: int) -> dict:
    """Détails d'un châssis (nb vitrages, type géométrique)."""
    geo_db = _geometry_db()
    geo = geo_db.get(str(chassis_id))
    if not geo:
        raise HTTPException(status_code=404, detail="Châssis introuvable")
    return {
        "chassis_id": chassis_id,
        "geo_type": geo["geo_type"],
        "nb_zones": len(geo["pieces"]),  # approximatif
        "pieces": geo["pieces"],
    }


@router.get("/vitrages")
def get_vitrages(type_vitrage: str | None = None) -> list[dict]:
    """Liste des compositions de vitrage disponibles."""
    vitrages = _vitrages_db()
    if type_vitrage:
        vitrages = [v for v in vitrages if v.get("type") == type_vitrage]
    # Retourner uniquement composition + Ug pour les dropdowns
    return [{"composition": v["composition"], "Ug": v["Ug"], "type": v["type"]}
            for v in vitrages]


@router.get("/intercalaires")
def get_intercalaires() -> list[str]:
    """Liste des types d'intercalaires disponibles."""
    seen = set()
    result = []
    for entry in _psi_g_db():
        name = entry["intercalaire"]
        if name not in seen:
            seen.add(name)
            result.append(name)
    return sorted(result)


@router.get("/couleurs")
def get_couleurs(famille: str | None = None) -> list[dict]:
    """Liste des couleurs disponibles."""
    couleurs = _couleurs_db()
    if famille:
        couleurs = [c for c in couleurs if c.get("famille_prix") == famille]
    return couleurs


@router.get("/volets")
def get_volets(gamme_code: str | None = None) -> list[dict]:
    """Liste des volets disponibles, filtrés par gamme."""
    volets = _volets_db()
    if gamme_code:
        volets = [
            v for v in volets
            if not v["gammes_compatibles"] or gamme_code in v["gammes_compatibles"]
        ]
    return [
        {
            "designation": v["designation"],
            "rR": v["rR"],
            "hauteur_coffre": v["hauteur_coffre"],
            "gammes_compatibles": v["gammes_compatibles"],
            "isolations_disponibles": list(v.get("uc_coefficients", {}).keys()),
        }
        for v in volets
    ]


# ---------------------------------------------------------------------------
# Calcul
# ---------------------------------------------------------------------------

@router.post("/calculer", response_model=CalculResult)
def post_calculer(inp: CalculInput) -> CalculResult:
    """
    Calcule les performances thermiques d'une menuiserie.
    Résultats : Uw/Ud, Sw, Tlw (+ Ujn, Ubb.jn si volet).
    """
    try:
        return calculer(inp)
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de calcul : {e}")
