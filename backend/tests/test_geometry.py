"""
Tests des calculs géométriques (geometry.py).
Vérifie les aires, périmètres et la conservation surface = Af + Ag.
"""

import pytest

from app.core.geometry import Piece, compute_geometry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pieces_4(th=0.07, tb=0.07, mg=0.07, md=0.07, uf=2.0):
    """4 pièces standard pour 1_vantail."""
    return [
        {"nom": "Traverse haute", "Af": th, "Uf": uf},
        {"nom": "Traverse basse", "Af": tb, "Uf": uf},
        {"nom": "Montant gauche", "Af": mg, "Uf": uf},
        {"nom": "Montant droit", "Af": md, "Uf": uf},
    ]


def _pieces_5(th=0.07, tb=0.07, mc=0.07, mg=0.07, md=0.07, uf=2.0):
    """5 pièces standard pour 2_vantaux."""
    return [
        {"nom": "Traverse haute", "Af": th, "Uf": uf},
        {"nom": "Traverse basse", "Af": tb, "Uf": uf},
        {"nom": "Masse centrale", "Af": mc, "Uf": uf},
        {"nom": "Montant gauche", "Af": mg, "Uf": uf},
        {"nom": "Montant droit", "Af": md, "Uf": uf},
    ]


def _pieces_6(th=0.07, tb=0.07, mc=0.07, men=0.07, mg=0.07, md=0.07, uf=2.0):
    """6 pièces standard pour 3/4_vantaux."""
    return [
        {"nom": "Traverse haute", "Af": th, "Uf": uf},
        {"nom": "Traverse basse", "Af": tb, "Uf": uf},
        {"nom": "Masse centrale", "Af": mc, "Uf": uf},
        {"nom": "Meneau dormant", "Af": men, "Uf": uf},
        {"nom": "Montant gauche", "Af": mg, "Uf": uf},
        {"nom": "Montant droit", "Af": md, "Uf": uf},
    ]


# ---------------------------------------------------------------------------
# 1 vantail
# ---------------------------------------------------------------------------

class TestGeo1Vantail:
    def test_basic(self):
        """Fenêtre 1m × 1m, profilés de 0.07m."""
        geo = compute_geometry(1.0, 1.0, "1_vantail", _pieces_4())
        assert geo.surface_totale == pytest.approx(1.0)
        assert len(geo.zones) == 1
        # Ag = (1 - 0.07 - 0.07) × (1 - 0.07 - 0.07) = 0.86 × 0.86
        assert geo.zones[0].Ag == pytest.approx(0.86 * 0.86, rel=1e-4)

    def test_surface_conservation(self):
        """Af_total + Ag_total = surface_totale (à la précision float près)."""
        geo = compute_geometry(1.2, 0.8, "1_vantail", _pieces_4())
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)

    def test_perimeter(self):
        geo = compute_geometry(1.0, 1.0, "1_vantail", _pieces_4())
        # lg = (1-0.14)*2 + (1-0.14)*2 = 0.86*4 = 3.44
        assert geo.zones[0].lg == pytest.approx(3.44, rel=1e-4)


# ---------------------------------------------------------------------------
# 2 vantaux
# ---------------------------------------------------------------------------

class TestGeo2Vantaux:
    def test_two_zones(self):
        geo = compute_geometry(1.4, 1.2, "2_vantaux", _pieces_5())
        assert len(geo.zones) == 2

    def test_surface_conservation(self):
        geo = compute_geometry(1.4, 1.2, "2_vantaux", _pieces_5())
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)

    def test_symmetric_pieces(self):
        """Avec des profilés identiques, les 2 zones doivent être égales."""
        geo = compute_geometry(1.4, 1.2, "2_vantaux", _pieces_5())
        assert geo.zones[0].Ag == pytest.approx(geo.zones[1].Ag, rel=1e-4)


# ---------------------------------------------------------------------------
# 3 vantaux
# ---------------------------------------------------------------------------

class TestGeo3Vantaux:
    def test_three_zones(self):
        geo = compute_geometry(1.4, 1.8, "3_vantaux", _pieces_6())
        assert len(geo.zones) == 3

    def test_surface_conservation(self):
        geo = compute_geometry(1.4, 1.8, "3_vantaux", _pieces_6())
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)


# ---------------------------------------------------------------------------
# 4 vantaux
# ---------------------------------------------------------------------------

class TestGeo4Vantaux:
    def test_four_zones(self):
        geo = compute_geometry(1.4, 2.4, "4_vantaux", _pieces_6())
        assert len(geo.zones) == 4

    def test_surface_conservation(self):
        geo = compute_geometry(1.4, 2.4, "4_vantaux", _pieces_6())
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)


# ---------------------------------------------------------------------------
# Porte soubassement
# ---------------------------------------------------------------------------

class TestGeoPorteSoubassement:
    def test_two_zones(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.07, "Uf": 2.0},
            {"nom": "Traverse basse", "Af": 0.07, "Uf": 2.0},
            {"nom": "Traverse intermédiaire", "Af": 0.07, "Uf": 2.0},
            {"nom": "Montant crémone", "Af": 0.07, "Uf": 2.0},
            {"nom": "Montant ferrage", "Af": 0.07, "Uf": 2.0},
        ]
        geo = compute_geometry(2.15, 0.9, "porte_soubassement", pieces)
        assert len(geo.zones) == 2  # vitrage + panneau

    def test_surface_conservation(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.07, "Uf": 2.0},
            {"nom": "Traverse basse", "Af": 0.07, "Uf": 2.0},
            {"nom": "Traverse intermédiaire", "Af": 0.07, "Uf": 2.0},
            {"nom": "Montant crémone", "Af": 0.07, "Uf": 2.0},
            {"nom": "Montant ferrage", "Af": 0.07, "Uf": 2.0},
        ]
        geo = compute_geometry(2.15, 0.9, "porte_soubassement", pieces)
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)

    def test_custom_hauteur_soubassement(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.07, "Uf": 2.0},
            {"nom": "Traverse basse", "Af": 0.07, "Uf": 2.0},
            {"nom": "Traverse intermédiaire", "Af": 0.07, "Uf": 2.0},
            {"nom": "Montant crémone", "Af": 0.07, "Uf": 2.0},
            {"nom": "Montant ferrage", "Af": 0.07, "Uf": 2.0},
        ]
        geo_default = compute_geometry(2.15, 0.9, "porte_soubassement", pieces)
        geo_custom = compute_geometry(2.15, 0.9, "porte_soubassement", pieces,
                                      {"hauteur_soubassement": 0.7})
        # Plus grand soubassement → vitrage plus petit, panneau plus grand
        assert geo_custom.zones[0].Ag < geo_default.zones[0].Ag
        assert geo_custom.zones[1].Ag > geo_default.zones[1].Ag
        assert geo_custom.Af_total + geo_custom.Ag_total == pytest.approx(
            geo_custom.surface_totale, rel=1e-3)


# ---------------------------------------------------------------------------
# Coulissant
# ---------------------------------------------------------------------------

class TestGeoCoulissant:
    def test_default_two_zones(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.05, "Uf": 3.0},
            {"nom": "Traverse basse", "Af": 0.08, "Uf": 3.0},
            {"nom": "Chicane", "Af": 0.06, "Uf": 3.0},
            {"nom": "Montant gauche", "Af": 0.07, "Uf": 3.0},
            {"nom": "Montant droite", "Af": 0.07, "Uf": 3.0},
        ]
        geo = compute_geometry(2.15, 2.0, "coulissant", pieces)
        assert len(geo.zones) == 2

    def test_three_zones(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.05, "Uf": 3.0},
            {"nom": "Traverse basse", "Af": 0.08, "Uf": 3.0},
            {"nom": "Chicane", "Af": 0.06, "Uf": 3.0},
            {"nom": "Montant gauche", "Af": 0.07, "Uf": 3.0},
            {"nom": "Montant droite", "Af": 0.07, "Uf": 3.0},
        ]
        geo = compute_geometry(2.15, 3.0, "coulissant", pieces, {"nb_zones": 3})
        assert len(geo.zones) == 3

    def test_surface_conservation(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.05, "Uf": 3.0},
            {"nom": "Traverse basse", "Af": 0.08, "Uf": 3.0},
            {"nom": "Chicane", "Af": 0.06, "Uf": 3.0},
            {"nom": "Montant gauche", "Af": 0.07, "Uf": 3.0},
            {"nom": "Montant droite", "Af": 0.07, "Uf": 3.0},
        ]
        geo = compute_geometry(2.15, 2.0, "coulissant", pieces)
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)


# ---------------------------------------------------------------------------
# Galandage
# ---------------------------------------------------------------------------

class TestGeoGalandage:
    def test_one_zone(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.05, "Uf": 3.0},
            {"nom": "Traverse basse", "Af": 0.08, "Uf": 3.0},
            {"nom": "Montant galandage", "Af": 0.07, "Uf": 3.0},
            {"nom": "Montant refoulement", "Af": 0.07, "Uf": 3.0},
        ]
        geo = compute_geometry(2.15, 1.0, "galandage", pieces)
        assert len(geo.zones) == 1

    def test_surface_conservation(self):
        pieces = [
            {"nom": "Traverse haute", "Af": 0.05, "Uf": 3.0},
            {"nom": "Traverse basse", "Af": 0.08, "Uf": 3.0},
            {"nom": "Montant galandage", "Af": 0.07, "Uf": 3.0},
            {"nom": "Montant refoulement", "Af": 0.07, "Uf": 3.0},
        ]
        geo = compute_geometry(2.15, 1.0, "galandage", pieces)
        assert geo.Af_total + geo.Ag_total == pytest.approx(geo.surface_totale, rel=1e-3)


# ---------------------------------------------------------------------------
# Dispatch & erreurs
# ---------------------------------------------------------------------------

class TestComputeGeometryDispatch:
    def test_unsupported_type_raises(self):
        with pytest.raises(NotImplementedError, match="non implémenté"):
            compute_geometry(1.0, 1.0, "type_inconnu", _pieces_4())

    def test_all_types_dispatchable(self):
        """Vérifie que tous les types déclarés dans GEOMETRY_DISPATCH sont appelables."""
        from app.core.geometry import GEOMETRY_DISPATCH
        assert len(GEOMETRY_DISPATCH) >= 9


# ---------------------------------------------------------------------------
# Ufi moyen
# ---------------------------------------------------------------------------

class TestUfiMoyen:
    def test_uniform_uf(self):
        """Si tous les Uf sont identiques, Ufi_moyen = ce Uf."""
        geo = compute_geometry(1.0, 1.0, "1_vantail", _pieces_4(uf=3.5))
        assert geo.Ufi_moyen == pytest.approx(3.5, rel=1e-4)

    def test_weighted_average(self):
        """Ufi_moyen doit être la moyenne pondérée par Af."""
        pieces = [
            {"nom": "Traverse haute", "Af": 0.10, "Uf": 2.0},
            {"nom": "Traverse basse", "Af": 0.05, "Uf": 4.0},
            {"nom": "Montant gauche", "Af": 0.05, "Uf": 4.0},
            {"nom": "Montant droit", "Af": 0.10, "Uf": 2.0},
        ]
        geo = compute_geometry(1.0, 1.0, "1_vantail", pieces)
        # (0.10*2 + 0.05*4 + 0.05*4 + 0.10*2) / (0.10+0.05+0.05+0.10) = 0.80/0.30 ≈ 2.667
        assert geo.Ufi_moyen == pytest.approx(0.80 / 0.30, rel=1e-3)
