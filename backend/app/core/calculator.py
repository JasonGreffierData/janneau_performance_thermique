"""
Moteur de calcul thermique JANNEAU.
Implémente les formules EN ISO 10077-1 (Uw) et XP P50-777 (Sw, Tlw).
"""

import json
from functools import lru_cache
from pathlib import Path

from app.core.geometry import GeometryResult, compute_geometry
from app.models.inputs import CalculInput
from app.models.outputs import CalculResult, DetailsCalcul, ResultatMenuiserie, ResultatVolet

DATA_DIR = Path(__file__).parent.parent / "data"

# Résistance superficielle extérieure — EN ISO 6946:2017, Tableau 1
# he = 25 W/(m².K)  →  Rse = 1/he = 0.04 m².K/W
# Valeur conventionnelle combinant convection forcée (~20 W/(m².K), vent de réf. 4 m/s)
# et rayonnement (~5 W/(m².K)). Utilisée pour le calcul de Sf dans la formule Sw.
HE = 25.0  # [W/(m².K)]


# ---------------------------------------------------------------------------
# Chargement des données de référence
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_json(name: str) -> list | dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def _chassis_list() -> list[dict]:
    return _load_json("chassis.json")


def _vitrages_db() -> list[dict]:
    return _load_json("vitrages.json")


def _psi_g_db() -> list[dict]:
    return _load_json("psi_g.json")


def _couleurs_db() -> list[dict]:
    return _load_json("couleurs.json")


def _volets_db() -> list[dict]:
    return _load_json("volets.json")


def _geometry_db() -> dict:
    return _load_json("chassis_geometry.json")


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def _get_chassis(nom: str) -> dict:
    for c in _chassis_list():
        if c["nom"] == nom:
            return c
    raise ValueError(f"Châssis inconnu : {nom!r}")


def _get_vitrage(composition: str) -> dict:
    for v in _vitrages_db():
        if v["composition"] == composition:
            return v
    raise ValueError(f"Vitrage inconnu : {composition!r}")


def _get_psi_g(gamme_code: str, intercalaire: str, ug: float, renfort: str = "Non") -> float:
    """
    Recherche Psi_g par gamme + intercalaire + Ug (±0.05 tolérance sur Ug).
    Retourne la valeur normée 0.08 si non trouvé.
    """
    best = None
    best_delta = float("inf")
    for entry in _psi_g_db():
        if entry["gamme"] != gamme_code:
            continue
        if entry["intercalaire"].lower() != intercalaire.lower():
            continue
        if entry["renfort"] != renfort:
            continue
        delta = abs(entry["Ug"] - ug)
        if delta < best_delta:
            best_delta = delta
            best = entry["Psi_g"]
    # Valeur par défaut 0.08 W/(m·K) : intercalaire aluminium standard selon EN ISO 10077-1.
    # Pour intercalaires à rupture de pont thermique ("warm edge"), les valeurs typiques
    # sont 0.04–0.06 W/(m·K) et doivent figurer dans la table psi_g.json.
    return best if best is not None else 0.08


def _get_alpha(couleur: str) -> float:
    """Retourne le coefficient d'absorption α de la couleur.

    Défaut 0.6 : valeur moyenne conventionnelle (couleur claire ~0.3, foncée ~0.9).
    Référence : XP P50-777 et EN 410 pour la caractérisation des vitrages teintés.
    """
    for c in _couleurs_db():
        if c["nom"].lower() == couleur.lower():
            return c["alpha"]
    return 0.6


def _get_volet(designation: str) -> dict | None:
    for v in _volets_db():
        if v["designation"] == designation:
            return v
    return None


def _get_geometry(chassis_id: int) -> dict:
    db = _geometry_db()
    key = str(chassis_id)
    if key not in db:
        raise ValueError(f"Géométrie non trouvée pour châssis id={chassis_id}")
    return db[key]


# ---------------------------------------------------------------------------
# Calcul Uw (EN ISO 10077-1)
# ---------------------------------------------------------------------------

def _calc_uw(
    geo: GeometryResult,
    vitrage_data: list[dict],   # [{Ug, Psi_g, Sg, Tlg}, ...]
    is_porte: bool = False,
) -> float:
    """
    Uw = (Σ Ug_i*Ag_i + Σ Ψg_i*lg_i + Σ Uf_j*Af_j) / (Σ Ag_i + Σ Af_j)

    vitrage_data[i] correspond à geo.zones[i].
    """
    numerateur = 0.0

    # Contribution des zones vitrées / panneaux
    for i, zone in enumerate(geo.zones):
        if i >= len(vitrage_data):
            break
        vd = vitrage_data[i]
        numerateur += vd["Ug"] * zone.Ag
        numerateur += vd["Psi_g"] * zone.lg

    # Contribution des cadres
    for piece in geo.pieces:
        # Calcul de l'aire du profilé (simplifié : Af × longueur appropriée)
        # On utilise Af_total qui est déjà calculé dans GeometryResult
        pass

    # Recalcul propre : Uf_j * Af_j pour chaque pièce
    # (GeometryResult.Af_total n'est pas décomposé par pièce ici)
    # → On utilise Ufi_moyen * Af_total
    numerateur += geo.Ufi_moyen * geo.Af_total

    denominateur = geo.Ag_total + geo.Af_total

    if denominateur <= 0:
        return 0.0
    return numerateur / denominateur


# ---------------------------------------------------------------------------
# Calcul Sw (XP P50-777)
# ---------------------------------------------------------------------------

def _calc_sw(
    geo: GeometryResult,
    vitrage_data: list[dict],
    alpha: float,
) -> float:
    """
    Sw = (Σ Af_total * Sf + Σ Ag_i * Sg_i) / (Σ Ag_i + Σ Af_j)
    Sf = α * Uf_moyen / he
    """
    Sf = alpha * geo.Ufi_moyen / HE

    numerateur = geo.Af_total * Sf

    for i, zone in enumerate(geo.zones):
        if i >= len(vitrage_data):
            break
        sg = vitrage_data[i].get("Sg", 0) or 0
        numerateur += zone.Ag * sg

    denominateur = geo.Ag_total + geo.Af_total
    if denominateur <= 0:
        return 0.0
    return numerateur / denominateur


# ---------------------------------------------------------------------------
# Calcul Tlw (XP P50-777)
# ---------------------------------------------------------------------------

def _calc_tlw(geo: GeometryResult, vitrage_data: list[dict]) -> float:
    """
    Tlw = Σ(Ag_i) / (Σ Ag_i + Σ Af_j) × (Σ Ag_i × Tlg_i / Σ Ag_i)
        = Σ(Ag_i × Tlg_i) / (Σ Ag_i + Σ Af_j)
    """
    numerateur = 0.0
    for i, zone in enumerate(geo.zones):
        if i >= len(vitrage_data):
            break
        tlg = vitrage_data[i].get("Tlg", 0) or 0
        numerateur += zone.Ag * tlg

    denominateur = geo.Ag_total + geo.Af_total
    if denominateur <= 0:
        return 0.0
    return (numerateur / denominateur) * 100  # en %


# ---------------------------------------------------------------------------
# Calcul avec volet (EN ISO 10077-1)
# ---------------------------------------------------------------------------

def _calc_volet(Uw: float, volet: dict, largeur_m: float, hauteur_m: float,
                isolation: str) -> ResultatVolet:
    rR = volet.get("rR", 0)

    # Ujn = (Uw + 1/(1/Uw + rR)) / 2
    Ujn = (Uw + 1 / (1 / Uw + rR)) / 2

    # Uc = a + b/L
    uc_coeffs = volet.get("uc_coefficients", {})
    coeff = uc_coeffs.get(isolation) or uc_coeffs.get("T")
    Uc = None
    Ubb_jn = None
    if coeff and largeur_m > 0:
        Uc = coeff["a"] + coeff["b"] / largeur_m
        # Ubb.jn = (Ujn * A_menuiserie + Uc * A_coffre) / (A_menuiserie + A_coffre)
        hauteur_coffre = volet.get("hauteur_coffre") or 0
        A_coffre = hauteur_coffre * largeur_m
        A_menuiserie = hauteur_m * largeur_m
        if A_coffre > 0:
            Ubb_jn = (Ujn * A_menuiserie + Uc * A_coffre) / (A_menuiserie + A_coffre)

    return ResultatVolet(
        rR=round(rR, 4),
        Ujn=round(Ujn, 4),
        Ubb_jn=round(Ubb_jn, 4) if Ubb_jn is not None else None,
        Uc=round(Uc, 4) if Uc is not None else None,
    )


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def calculer(inp: CalculInput) -> CalculResult:
    """
    Calcule Uw, Sw, Tlw (et Ujn, Ubb.jn si volet) pour la menuiserie décrite en entrée.
    """
    # 1. Résoudre le châssis
    chassis = _get_chassis(inp.chassis)
    chassis_id = chassis["id"]
    gamme_code = chassis["gamme_code"]
    is_porte = inp.famille.startswith("PORTES")

    # 2. Charger la géométrie
    geo_data = _get_geometry(chassis_id)
    pieces_data = geo_data["pieces"]
    geo_type = geo_data["geo_type"]
    extra_params = geo_data.get("extra_params", {})

    H = inp.hauteur_mm / 1000
    L = inp.largeur_mm / 1000

    geo = compute_geometry(H, L, geo_type, pieces_data, extra_params)

    # 3. Résoudre les remplissages
    all_remplissages = list(inp.vitrages) + list(inp.panneaux)
    zones_psi = geo_data.get("zones_psi", [])

    vitrage_data = []
    for i, zone in enumerate(geo.zones):
        # Données Psi_g et Ug depuis les métadonnées de l'onglet chassis
        zone_meta = zones_psi[i] if i < len(zones_psi) else {}

        if i < len(all_remplissages):
            remp = all_remplissages[i]
            vdb = _get_vitrage(remp.composition)

            # Ug : dynamique (depuis le vitrage utilisateur) ou hardcodé
            if zone_meta.get("Ug_dynamic", True):
                ug = vdb["Ug"]
            else:
                ug = zone_meta.get("Ug_default") or vdb["Ug"]

            # Psi_g : dynamique (lookup table) ou hardcodé dans l'onglet
            if zone_meta.get("Psi_g_dynamic", True):
                psi_g = _get_psi_g(gamme_code, remp.intercalaire, ug,
                                   renfort=geo_data.get("renfort", "Non"))
            else:
                # 0.08 W/(m·K) : valeur par défaut intercalaire alu (EN ISO 10077-1)
            psi_g = zone_meta.get("Psi_g_default") or 0.08

            vitrage_data.append({
                "Ug": ug,
                "Psi_g": psi_g,
                "Sg": vdb.get("Sg", 0),
                "Tlg": vdb.get("Tlg", 0),
            })
        else:
            # Zone sans remplissage saisi → valeurs de repli conservatrices
            # Ug  = 1.1 W/(m².K) : double vitrage standard 4/16Ar/4 (EN 673)
            # Psi_g = 0.08 W/(m·K) : intercalaire alu (EN ISO 10077-1)
            # Sg  = 0.65 : facteur solaire double vitrage clair (EN 410)
            # Tlg = 0.82 : transmission lumineuse double vitrage clair (EN 410)
            ug = zone_meta.get("Ug_default") or 1.1
            psi_g = zone_meta.get("Psi_g_default") or 0.08
            vitrage_data.append({"Ug": ug, "Psi_g": psi_g, "Sg": 0.65, "Tlg": 0.82})

    # 4. Calculs thermiques
    alpha = _get_alpha(inp.couleur)

    Uw = _calc_uw(geo, vitrage_data, is_porte)
    Sw = _calc_sw(geo, vitrage_data, alpha)
    Tlw = _calc_tlw(geo, vitrage_data)

    label_uw = "Ud" if is_porte else "Uw"

    # 5. Volet (optionnel)
    resultat_volet = None
    if inp.volet.actif and inp.volet.type:
        volet = _get_volet(inp.volet.type)
        if volet:
            resultat_volet = _calc_volet(
                Uw, volet, L, H, inp.volet.isolation_acoustique
            )

    return CalculResult(
        menuiserie_seule=ResultatMenuiserie(
            Uw=round(Uw, 4),
            Sw=round(Sw, 4),
            Tlw=round(Tlw, 2),
            label_uw=label_uw,
        ),
        avec_volet=resultat_volet,
        details=DetailsCalcul(
            chassis_id=chassis_id,
            geo_type=geo_type,
            Uf_moyen=round(geo.Ufi_moyen, 4),
            Af_total=round(geo.Af_total, 4),
            Ag_total=round(geo.Ag_total, 4),
            surface_totale=round(geo.surface_totale, 4),
        ),
    )
