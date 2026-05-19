"""
Décomposition géométrique des châssis.
Traduit les formules Excel des onglets 1-266 en Python pur.

Nomenclature des pièces (par indice dans la liste) :
  Chaque geo_type a une convention fixe d'indexation des pièces.
  On utilise les noms de pièce pour les identifier, pas les indices.
"""

from dataclasses import dataclass


@dataclass
class Piece:
    nom: str
    Af: float   # largeur du nœud [m]
    Uf: float   # transmission thermique du profilé [W/m².K]


@dataclass
class ZoneVitrage:
    Ag: float   # aire du vitrage [m²]
    lg: float   # périmètre du vitrage [m]
    index: int  # 0-based (G1=0, G2=1, ...)


@dataclass
class GeometryResult:
    pieces: list[Piece]
    zones: list[ZoneVitrage]
    Af_total: float   # somme des aires de cadre [m²]
    Ag_total: float   # somme des aires de vitrage [m²]
    surface_totale: float   # H × L [m²]
    Ufi_moyen: float  # Uf moyen pondéré par Af


def _find(pieces: list[Piece], *keywords: str) -> Piece | None:
    """Trouve la première pièce dont le nom contient tous les mots-clés."""
    for p in pieces:
        n = p.nom.lower()
        if all(k.lower() in n for k in keywords):
            return p
    return None


def _ufi_moyen(pieces: list[Piece]) -> float:
    total_af = sum(p.Af for p in pieces)
    if total_af == 0:
        return 0.0
    return sum(p.Af * p.Uf for p in pieces) / total_af


# ---------------------------------------------------------------------------
# Types géométriques
# ---------------------------------------------------------------------------

def _geo_1_vantail(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    1 vitrage — Fixe, 1 vantail, soufflet, oscillo-battante 1 vantail.
    4 pièces : traverse haute (TH), traverse basse (TB), montant gauche (MG), montant droit (MD)

    Formules (onglet 1 & 2 Excel) :
      Af_TH = (L - Af_MG - Af_MD) * Af_TH
      Ag    = (L - Af_MG - Af_MD) * (H - Af_TH - Af_TB)
      lg    = (L - Af_MG - Af_MD)*2 + (H - Af_TH - Af_TB)*2
    """
    TH = _find(pieces, "traverse haute") or pieces[0]
    TB = _find(pieces, "traverse basse") or pieces[1]
    # Montant gauche = crémone ou gauche (index 2)
    MG = _find(pieces, "gauche") or _find(pieces, "crémone") or pieces[2]
    # Montant droit = ferrage ou droit (index 3)
    MD = _find(pieces, "droit") or _find(pieces, "ferrage") or pieces[3]

    Ag = (L - MG.Af - MD.Af) * (H - TH.Af - TB.Af)
    lg = (L - MG.Af - MD.Af) * 2 + (H - TH.Af - TB.Af) * 2

    return GeometryResult(
        pieces=pieces,
        zones=[ZoneVitrage(Ag=max(0, Ag), lg=max(0, lg), index=0)],
        Af_total=_af_total_rect(pieces, H, L, TH, TB, MG, MD),
        Ag_total=max(0, Ag),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _af_total_rect(pieces, H, L, TH, TB, MG, MD):
    """Calcule la somme des aires de cadre pour un châssis rectangulaire simple."""
    af_th = (L - MG.Af - MD.Af) * TH.Af
    af_tb = (L - MG.Af - MD.Af) * TB.Af
    af_mg = H * MG.Af
    af_md = H * MD.Af
    return af_th + af_tb + af_mg + af_md


def _geo_2_vantaux(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    2 vitrages — Française 2 vantaux, oscillo-battante 2 vantaux.
    5 pièces : TH, TB, masse centrale (MC), montant gauche (MG), montant droit (MD)

    Formules (onglet 3/211 Excel) :
      Ag1 = (L/2 - Af_MG - Af_MC/2) * (H - Af_TH - Af_TB)
      Ag2 = (L/2 - Af_MC/2 - Af_MD) * (H - Af_TH - Af_TB)
      lg1 = (L/2 - Af_MG - Af_MC/2)*2 + (H - Af_TH - Af_TB)*2
      lg2 = (L/2 - Af_MC/2 - Af_MD)*2 + (H - Af_TH - Af_TB)*2
    """
    TH = _find(pieces, "traverse haute")
    TB = _find(pieces, "traverse basse")
    MC = _find(pieces, "masse centrale") or _find(pieces, "centrale")
    MG = _find(pieces, "gauche")
    MD = _find(pieces, "droit") or _find(pieces, "droite")

    Hv = H - TH.Af - TB.Af  # hauteur libre vitrage
    Ag1 = (L / 2 - MG.Af - MC.Af / 2) * Hv
    Ag2 = (L / 2 - MC.Af / 2 - MD.Af) * Hv
    lg1 = (L / 2 - MG.Af - MC.Af / 2) * 2 + Hv * 2
    lg2 = (L / 2 - MC.Af / 2 - MD.Af) * 2 + Hv * 2

    Af_TH = (L - MG.Af - MD.Af - MC.Af) * TH.Af
    Af_TB = (L - MG.Af - MD.Af - MC.Af) * TB.Af
    Af_MC = H * MC.Af
    Af_MG = H * MG.Af
    Af_MD = H * MD.Af
    Af_total = Af_TH + Af_TB + Af_MC + Af_MG + Af_MD

    return GeometryResult(
        pieces=pieces,
        zones=[
            ZoneVitrage(Ag=max(0, Ag1), lg=max(0, lg1), index=0),
            ZoneVitrage(Ag=max(0, Ag2), lg=max(0, lg2), index=1),
        ],
        Af_total=Af_total,
        Ag_total=max(0, Ag1) + max(0, Ag2),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_3_vantaux(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    3 vitrages — Française 3 vantaux.
    6 pièces : TH, TB, masse centrale croisée (MC), meneau dormant (Men), montant gauche (MG), montant droit (MD)

    Formules (onglet 4 Excel) :
      Ag1 = (L/3 - Af_MG - Af_MC/2) * Hv
      Ag2 = (L/3 - Af_MC/2 - Af_Men/2) * Hv
      Ag3 = (L/3 - Af_Men/2 - Af_MD) * Hv
    """
    TH = _find(pieces, "traverse haute")
    TB = _find(pieces, "traverse basse")
    MC = _find(pieces, "masse centrale") or _find(pieces, "centrale")
    Men = _find(pieces, "meneau dormant") or _find(pieces, "meneau")
    MG = _find(pieces, "gauche")
    MD = _find(pieces, "droit") or _find(pieces, "droite")

    Hv = H - TH.Af - TB.Af
    w = L / 3

    Ag1 = (w - MG.Af - MC.Af / 2) * Hv
    Ag2 = (w - MC.Af / 2 - Men.Af / 2) * Hv
    Ag3 = (w - Men.Af / 2 - MD.Af) * Hv
    lg1 = (w - MG.Af - MC.Af / 2) * 2 + Hv * 2
    lg2 = (w - MC.Af / 2 - Men.Af / 2) * 2 + Hv * 2
    lg3 = (w - Men.Af / 2 - MD.Af) * 2 + Hv * 2

    return GeometryResult(
        pieces=pieces,
        zones=[
            ZoneVitrage(Ag=max(0, Ag1), lg=max(0, lg1), index=0),
            ZoneVitrage(Ag=max(0, Ag2), lg=max(0, lg2), index=1),
            ZoneVitrage(Ag=max(0, Ag3), lg=max(0, lg3), index=2),
        ],
        Af_total=H * L - max(0, Ag1) - max(0, Ag2) - max(0, Ag3),
        Ag_total=max(0, Ag1) + max(0, Ag2) + max(0, Ag3),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_4_vantaux(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    4 vitrages — Française 4 vantaux.
    6 pièces : TH, TB, masse centrale croisée (MC), meneau dormant (Men), montant gauche (MG), montant droit (MD)

    Pattern similaire à 3_vantaux mais L/4 par zone.
    Formules (onglet 5 Excel) :
      Ag1 = (L/4 - Af_MG - Af_MC/2) * Hv
      Ag2 = (L/4 - Af_MC/2 - Af_Men/2) * Hv
      Ag3 = (L/4 - Af_Men/2 - Af_MC/2) * Hv  (symétrie)
      Ag4 = (L/4 - Af_MC/2 - Af_MD) * Hv
    """
    TH = _find(pieces, "traverse haute")
    TB = _find(pieces, "traverse basse")
    MC = _find(pieces, "masse centrale") or _find(pieces, "centrale")
    Men = _find(pieces, "meneau dormant") or _find(pieces, "meneau")
    MG = _find(pieces, "gauche")
    MD = _find(pieces, "droit") or _find(pieces, "droite")

    Hv = H - TH.Af - TB.Af
    w = L / 4

    Ag1 = (w - MG.Af - MC.Af / 2) * Hv
    Ag2 = (w - MC.Af / 2 - Men.Af / 2) * Hv
    Ag3 = (w - Men.Af / 2 - MC.Af / 2) * Hv
    Ag4 = (w - MC.Af / 2 - MD.Af) * Hv
    lg1 = (w - MG.Af - MC.Af / 2) * 2 + Hv * 2
    lg2 = (w - MC.Af / 2 - Men.Af / 2) * 2 + Hv * 2
    lg3 = (w - Men.Af / 2 - MC.Af / 2) * 2 + Hv * 2
    lg4 = (w - MC.Af / 2 - MD.Af) * 2 + Hv * 2

    return GeometryResult(
        pieces=pieces,
        zones=[
            ZoneVitrage(Ag=max(0, Ag1), lg=max(0, lg1), index=0),
            ZoneVitrage(Ag=max(0, Ag2), lg=max(0, lg2), index=1),
            ZoneVitrage(Ag=max(0, Ag3), lg=max(0, lg3), index=2),
            ZoneVitrage(Ag=max(0, Ag4), lg=max(0, lg4), index=3),
        ],
        Af_total=H * L - sum(max(0, a) for a in [Ag1, Ag2, Ag3, Ag4]),
        Ag_total=sum(max(0, a) for a in [Ag1, Ag2, Ag3, Ag4]),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_2v_1fixe(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    3 vitrages — Française 2 vantaux + 1 fixe latéral.
    8 pièces : TH croisée, TB croisée, TH fixe, TB fixe, masse centrale (MC),
               meneau dormant (Men), montant gauche croisée (MG), montant droit fixe (MD_f)

    Formules (onglet 6 Excel) :
      Zone croisée gauche  : w=L/3, Ag1 = (w - MG - MC/2) * Hv_croisee
      Zone croisée droite  : Ag2 = (w - MC/2 - Men/2) * Hv_croisee
      Zone fixe            : Ag3 = (w - Men/2 - MD_f) * Hv_fixe
    """
    TH_c = _find(pieces, "traverse haute", "croisée") or _find(pieces, "traverse haute")
    TB_c = _find(pieces, "traverse basse", "croisée") or _find(pieces, "traverse basse")
    TH_f = _find(pieces, "traverse haute", "fixe") or TH_c
    TB_f = _find(pieces, "traverse basse", "fixe") or TB_c
    MC  = _find(pieces, "masse centrale") or _find(pieces, "centrale")
    Men = _find(pieces, "meneau dormant") or _find(pieces, "meneau")
    MG  = _find(pieces, "gauche")
    MD_f = _find(pieces, "droit") or _find(pieces, "droite")

    Hv_c = H - TH_c.Af - TB_c.Af
    Hv_f = H - TH_f.Af - TB_f.Af
    w = L / 3

    Ag1 = (w - MG.Af - MC.Af / 2) * Hv_c
    Ag2 = (w - MC.Af / 2 - Men.Af / 2) * Hv_c
    Ag3 = (w - Men.Af / 2 - MD_f.Af) * Hv_f
    lg1 = (w - MG.Af - MC.Af / 2) * 2 + Hv_c * 2
    lg2 = (w - MC.Af / 2 - Men.Af / 2) * 2 + Hv_c * 2
    lg3 = (w - Men.Af / 2 - MD_f.Af) * 2 + Hv_f * 2

    return GeometryResult(
        pieces=pieces,
        zones=[
            ZoneVitrage(Ag=max(0, Ag1), lg=max(0, lg1), index=0),
            ZoneVitrage(Ag=max(0, Ag2), lg=max(0, lg2), index=1),
            ZoneVitrage(Ag=max(0, Ag3), lg=max(0, lg3), index=2),
        ],
        Af_total=H * L - sum(max(0, a) for a in [Ag1, Ag2, Ag3]),
        Ag_total=sum(max(0, a) for a in [Ag1, Ag2, Ag3]),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_2v_2fixes(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    4 vitrages — Française 2 vantaux + 2 fixes latéraux.
    Géométrie symétrique : fixe gauche | croisée | fixe droit.
    L/4 par zone.
    """
    TH_c = _find(pieces, "traverse haute", "croisée") or _find(pieces, "traverse haute")
    TB_c = _find(pieces, "traverse basse", "croisée") or _find(pieces, "traverse basse")
    TH_f = _find(pieces, "traverse haute", "fixe") or TH_c
    TB_f = _find(pieces, "traverse basse", "fixe") or TB_c
    MC   = _find(pieces, "masse centrale") or _find(pieces, "centrale")
    Men1 = None
    Men2 = None
    for p in pieces:
        if "meneau" in p.nom.lower():
            if Men1 is None:
                Men1 = p
            else:
                Men2 = p
    MG = _find(pieces, "gauche")
    MD = _find(pieces, "droit") or _find(pieces, "droite")

    Hv_c = H - TH_c.Af - TB_c.Af
    Hv_f = H - TH_f.Af - TB_f.Af
    w = L / 4

    men1_af = Men1.Af if Men1 else 0
    men2_af = Men2.Af if Men2 else men1_af

    Ag1 = (w - MG.Af - men1_af / 2) * Hv_f   # fixe gauche
    Ag2 = (w - men1_af / 2 - MC.Af / 2) * Hv_c  # croisée gauche
    Ag3 = (w - MC.Af / 2 - men2_af / 2) * Hv_c  # croisée droite
    Ag4 = (w - men2_af / 2 - MD.Af) * Hv_f   # fixe droit
    lg1 = (w - MG.Af - men1_af / 2) * 2 + Hv_f * 2
    lg2 = (w - men1_af / 2 - MC.Af / 2) * 2 + Hv_c * 2
    lg3 = (w - MC.Af / 2 - men2_af / 2) * 2 + Hv_c * 2
    lg4 = (w - men2_af / 2 - MD.Af) * 2 + Hv_f * 2

    return GeometryResult(
        pieces=pieces,
        zones=[
            ZoneVitrage(Ag=max(0, Ag1), lg=max(0, lg1), index=0),
            ZoneVitrage(Ag=max(0, Ag2), lg=max(0, lg2), index=1),
            ZoneVitrage(Ag=max(0, Ag3), lg=max(0, lg3), index=2),
            ZoneVitrage(Ag=max(0, Ag4), lg=max(0, lg4), index=3),
        ],
        Af_total=H * L - sum(max(0, a) for a in [Ag1, Ag2, Ag3, Ag4]),
        Ag_total=sum(max(0, a) for a in [Ag1, Ag2, Ag3, Ag4]),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_coulissant(H: float, L: float, pieces: list[Piece],
                    nb_zones: int = 2) -> GeometryResult:
    """
    Baie coulissante — de 2 à N vantaux sur 2 ou 3 rails.
    Pièces attendues : Traverse haute (TH), Traverse basse (TB),
                       Chicane (jonction centrale), Montant gauche (MG), Montant droite (MD).
    Pièces optionnelles internes (meneaux ouvrants, traverses ouvrants) : incluses dans Af_total
    uniquement via Ufi_moyen, sans impact sur les zones vitrées.

    Formule pour n zones égales (L/n chacune) — référence onglets Excel SOLARIS II / CG-ALU :
      Zone 1       : Ag = (L/n - MG.Af  - Chicane.Af/2) × Hv
      Zone 2…n-1   : Ag = (L/n - Chicane.Af/2 - Chicane.Af/2) × Hv
      Zone n       : Ag = (L/n - Chicane.Af/2 - MD.Af) × Hv
      lg_i         : 2 × largeur_zone_i + 2 × Hv
    """
    TH      = _find(pieces, "traverse haute")
    TB      = _find(pieces, "traverse basse")
    Chicane = _find(pieces, "chicane") or _find(pieces, "masse centrale") or _find(pieces, "centrale")
    MG      = _find(pieces, "gauche")
    MD      = _find(pieces, "droite") or _find(pieces, "droit")

    Hv = H - TH.Af - TB.Af
    w  = L / nb_zones
    ch_af = Chicane.Af if Chicane else 0.0

    zones = []
    for i in range(nb_zones):
        left  = MG.Af    if i == 0             else ch_af / 2
        right = MD.Af    if i == nb_zones - 1  else ch_af / 2
        Ag = (w - left - right) * Hv
        lg = 2 * (w - left - right) + 2 * Hv
        zones.append(ZoneVitrage(Ag=max(0.0, Ag), lg=max(0.0, lg), index=i))

    Ag_total = sum(z.Ag for z in zones)

    return GeometryResult(
        pieces=pieces,
        zones=zones,
        Af_total=max(0.0, H * L - Ag_total),
        Ag_total=Ag_total,
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_galandage(H: float, L: float, pieces: list[Piece]) -> GeometryResult:
    """
    Galandage 1 vantail — le vantail disparaît dans le tableau de maçonnerie.
    Pièces : Traverse haute (TH), Traverse basse (TB),
             Montant côté galandage (MG), Montant côté refoulement (MD).

    Formule (onglet Excel SOLARIS II galandage 1V) :
      Hv  = H - TH.Af - TB.Af
      Ag  = (L - MG.Af - MD.Af) × Hv
      lg  = 2 × (L - MG.Af - MD.Af) + 2 × Hv
    """
    TH = _find(pieces, "traverse haute")
    TB = _find(pieces, "traverse basse")
    MG = _find(pieces, "galandage") or pieces[2]
    MD = _find(pieces, "refoulement") or pieces[3]

    Hv  = H - TH.Af - TB.Af
    lv  = L - MG.Af - MD.Af
    Ag  = lv * Hv
    lg  = 2 * lv + 2 * Hv

    Af_TH = lv * TH.Af
    Af_TB = lv * TB.Af
    Af_MG = H * MG.Af
    Af_MD = H * MD.Af
    Af_total = Af_TH + Af_TB + Af_MG + Af_MD

    return GeometryResult(
        pieces=pieces,
        zones=[ZoneVitrage(Ag=max(0.0, Ag), lg=max(0.0, lg), index=0)],
        Af_total=Af_total,
        Ag_total=max(0.0, Ag),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


def _geo_porte_soubassement(H: float, L: float, pieces: list[Piece],
                             hauteur_soubassement: float = 0.45) -> GeometryResult:
    """
    Porte crémone/serrure/service avec soubassement.
    5 pièces : TH, TB, traverse intermédiaire (TI), montant crémone (MG), montant ferrage (MD)

    Zone G1 (vitrage) en partie haute : H - h_soubassement
    Zone P1 (panneau) en partie basse : h_soubassement

    Formules (onglet 64 Excel) :
      Ag1 = (L - MC - MF) * (H - 0.45 - TH - TI/2)
      Ap1 = (L - MC - MF) * (0.45 - TB - TI/2)
    """
    TH = _find(pieces, "traverse haute")
    TB = _find(pieces, "traverse basse")
    TI = _find(pieces, "intermédiaire") or _find(pieces, "traverse inter")
    MG = _find(pieces, "crémone") or _find(pieces, "gauche")
    MD = _find(pieces, "ferrage") or _find(pieces, "droit") or _find(pieces, "droite")

    hs = hauteur_soubassement
    Ag1 = (L - MG.Af - MD.Af) * (H - hs - TH.Af - TI.Af / 2)
    Ap1 = (L - MG.Af - MD.Af) * (hs - TB.Af - TI.Af / 2)
    lg1 = (L - MG.Af - MD.Af) * 2 + (H - hs - TH.Af - TI.Af / 2) * 2
    lp1 = (L - MG.Af - MD.Af) * 2 + (hs - TB.Af - TI.Af / 2) * 2

    return GeometryResult(
        pieces=pieces,
        zones=[
            ZoneVitrage(Ag=max(0, Ag1), lg=max(0, lg1), index=0),
            ZoneVitrage(Ag=max(0, Ap1), lg=max(0, lp1), index=1),  # panneau
        ],
        Af_total=H * L - max(0, Ag1) - max(0, Ap1),
        Ag_total=max(0, Ag1) + max(0, Ap1),
        surface_totale=H * L,
        Ufi_moyen=_ufi_moyen(pieces),
    )


# ---------------------------------------------------------------------------
# Dispatch principal
# ---------------------------------------------------------------------------

GEOMETRY_DISPATCH = {
    "1_vantail":                  _geo_1_vantail,
    "2_vantaux":                  _geo_2_vantaux,
    "3_vantaux":                  _geo_3_vantaux,
    "4_vantaux":                  _geo_4_vantaux,
    "2_vantaux_1_fixe_lateral":   _geo_2v_1fixe,
    "2_vantaux_2_fixes_lateraux": _geo_2v_2fixes,
    "porte_soubassement":         _geo_porte_soubassement,
    "coulissant":                 _geo_coulissant,
    "galandage":                  _geo_galandage,
}


def compute_geometry(
    H: float,
    L: float,
    geo_type: str,
    pieces_data: list[dict],
    extra_params: dict | None = None,
) -> GeometryResult:
    """
    Point d'entrée principal.

    Args:
        H: hauteur en mètres
        L: largeur en mètres
        geo_type: type géométrique (ex: "2_vantaux")
        pieces_data: liste de dicts {"nom", "Af", "Uf"}
        extra_params: paramètres spéciaux (ex: {"hauteur_soubassement": 0.45})

    Returns:
        GeometryResult avec zones et aires calculées
    """
    pieces = [Piece(nom=p["nom"], Af=p["Af"], Uf=p["Uf"]) for p in pieces_data]
    extra = extra_params or {}

    fn = GEOMETRY_DISPATCH.get(geo_type)
    if fn is None:
        raise NotImplementedError(
            f"Type géométrique '{geo_type}' non implémenté dans le MVP. "
            f"Types supportés : {list(GEOMETRY_DISPATCH.keys())}"
        )

    if geo_type == "porte_soubassement":
        return fn(H, L, pieces, hauteur_soubassement=extra.get("hauteur_soubassement", 0.45))

    if geo_type == "coulissant":
        return fn(H, L, pieces, nb_zones=extra.get("nb_zones", 2))

    return fn(H, L, pieces)
