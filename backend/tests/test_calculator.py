"""
Tests du moteur de calcul thermique (calculator.py).
"""

import pytest

from app.core.calculator import (
    _calc_sw,
    _calc_tlw,
    _calc_uw,
    _calc_volet,
    _get_alpha,
    _get_chassis,
    _get_psi_g,
    _get_vitrage,
    calculer,
    HE,
    PSI_P,
)
from app.core.geometry import GeometryResult, Piece, ZoneVitrage
from app.models.inputs import CalculInput, VitragInput, VoletInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_geo(Ag=0.5, lg=3.0, Af_total=0.3, Ufi_moyen=2.0) -> GeometryResult:
    """Géométrie simplifiée pour tester les formules de calcul."""
    return GeometryResult(
        pieces=[Piece("test", Af_total, Ufi_moyen)],
        zones=[ZoneVitrage(Ag=Ag, lg=lg, index=0)],
        Af_total=Af_total,
        Ag_total=Ag,
        surface_totale=Ag + Af_total,
        Ufi_moyen=Ufi_moyen,
    )


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

class TestLookups:
    def test_get_chassis_known(self):
        c = _get_chassis("BOIS - Fixe")
        assert c["id"] == 1
        assert c["famille"] == "FENETRES A FRAPPE"

    def test_get_chassis_unknown(self):
        with pytest.raises(ValueError, match="inconnu"):
            _get_chassis("Chassis Inexistant XYZ")

    def test_get_vitrage_known(self):
        v = _get_vitrage("4FE/16argon/4")
        assert v["Ug"] > 0

    def test_get_vitrage_unknown(self):
        with pytest.raises(ValueError, match="inconnu"):
            _get_vitrage("vitrage_inexistant")

    def test_get_alpha_known(self):
        alpha = _get_alpha("Blanc - RAL 9010")
        assert 0 < alpha < 1

    def test_get_alpha_unknown_returns_default(self):
        alpha = _get_alpha("Couleur Imaginaire 12345")
        assert alpha == 0.6

    def test_get_psi_g_fallback(self):
        """Psi_g doit retourner 0.08 si la combinaison n'existe pas."""
        psi = _get_psi_g("GAMME_INEXISTANTE", "Warm-Edge", 1.1)
        assert psi == 0.08


# ---------------------------------------------------------------------------
# Calcul Uw
# ---------------------------------------------------------------------------

class TestCalcUw:
    def test_formula(self):
        """Uw = (Ug*Ag + Psi_g*lg + Uf_moyen*Af_total) / (Ag + Af_total)"""
        geo = _simple_geo(Ag=0.5, lg=3.0, Af_total=0.3, Ufi_moyen=2.0)
        vd = [{"Ug": 1.1, "Psi_g": 0.08, "Sg": 0.65, "Tlg": 0.82}]
        uw = _calc_uw(geo, vd)
        expected = (1.1 * 0.5 + 0.08 * 3.0 + 2.0 * 0.3) / (0.5 + 0.3)
        assert uw == pytest.approx(expected, rel=1e-6)

    def test_zero_area_returns_zero(self):
        geo = _simple_geo(Ag=0, lg=0, Af_total=0, Ufi_moyen=0)
        uw = _calc_uw(geo, [{"Ug": 1.1, "Psi_g": 0.08}])
        assert uw == 0.0


# ---------------------------------------------------------------------------
# Calcul Sw
# ---------------------------------------------------------------------------

class TestCalcSw:
    def test_formula(self):
        """Sw = (Af*Sf + Ag*Sg) / (Ag + Af), Sf = alpha * Uf / HE"""
        geo = _simple_geo(Ag=0.5, lg=3.0, Af_total=0.3, Ufi_moyen=2.0)
        vd = [{"Ug": 1.1, "Psi_g": 0.08, "Sg": 0.65, "Tlg": 0.82}]
        alpha = 0.4
        sw = _calc_sw(geo, vd, alpha)
        Sf = alpha * 2.0 / HE
        expected = (0.3 * Sf + 0.5 * 0.65) / (0.5 + 0.3)
        assert sw == pytest.approx(expected, rel=1e-6)

    def test_dark_color_higher_sw(self):
        """Une couleur foncée (alpha haut) donne un Sw plus élevé."""
        geo = _simple_geo()
        vd = [{"Ug": 1.1, "Psi_g": 0.08, "Sg": 0.65, "Tlg": 0.82}]
        sw_light = _calc_sw(geo, vd, 0.3)
        sw_dark = _calc_sw(geo, vd, 0.9)
        assert sw_dark > sw_light


# ---------------------------------------------------------------------------
# Calcul Tlw
# ---------------------------------------------------------------------------

class TestCalcTlw:
    def test_formula(self):
        """Tlw = (Ag * Tlg) / (Ag + Af) * 100"""
        geo = _simple_geo(Ag=0.5, Af_total=0.3)
        vd = [{"Tlg": 0.82}]
        tlw = _calc_tlw(geo, vd)
        expected = (0.5 * 0.82) / (0.5 + 0.3) * 100
        assert tlw == pytest.approx(expected, rel=1e-6)

    def test_result_is_percentage(self):
        geo = _simple_geo(Ag=0.8, Af_total=0.2)
        vd = [{"Tlg": 0.82}]
        tlw = _calc_tlw(geo, vd)
        assert 0 < tlw <= 100


# ---------------------------------------------------------------------------
# Calcul volet
# ---------------------------------------------------------------------------

class TestCalcVolet:
    def test_ujn(self):
        """Ujn = (Uw + 1/(1/Uw + rR)) / 2"""
        volet = {
            "rR": 0.15,
            "hauteur_coffre": 0.2,
            "uc_coefficients": {"T": {"a": 1.0, "b": 0.5}},
        }
        result = _calc_volet(1.5, volet, 1.0, 1.4, "T")
        expected_ujn = (1.5 + 1 / (1 / 1.5 + 0.15)) / 2
        assert result.Ujn == pytest.approx(expected_ujn, rel=1e-3)
        assert result.rR == pytest.approx(0.15)

    def test_uc_formula(self):
        """Uc = a + b/L"""
        volet = {
            "rR": 0.15,
            "hauteur_coffre": 0.2,
            "uc_coefficients": {"T": {"a": 1.0, "b": 0.5}},
        }
        result = _calc_volet(1.5, volet, 1.2, 1.4, "T")
        expected_uc = 1.0 + 0.5 / 1.2
        assert result.Uc == pytest.approx(expected_uc, rel=1e-3)


# ---------------------------------------------------------------------------
# Calcul intégré (calculer)
# ---------------------------------------------------------------------------

class TestCalculer:
    def test_fenetre_simple(self):
        """Test de bout en bout : fenêtre 1 vantail BOIS."""
        inp = CalculInput(
            famille="FENETRES A FRAPPE",
            chassis="BOIS - Fixe",
            couleur="Blanc - RAL 9010",
            hauteur_mm=1200,
            largeur_mm=800,
        )
        result = calculer(inp)
        assert result.menuiserie_seule.Uw > 0
        assert result.menuiserie_seule.Sw > 0
        assert 0 < result.menuiserie_seule.Tlw <= 100
        assert result.menuiserie_seule.label_uw == "Uw"
        assert result.avec_volet is None

    def test_porte_label_ud(self):
        """Les portes doivent avoir le label 'Ud' au lieu de 'Uw'."""
        inp = CalculInput(
            famille="PORTES CREMONE-SERRURE-SERVICE",
            chassis="BOIS - Porte crémone 1 vantail avec soubassement",
            couleur="Blanc - RAL 9010",
            hauteur_mm=2150,
            largeur_mm=900,
        )
        result = calculer(inp)
        assert result.menuiserie_seule.label_uw == "Ud"

    def test_with_vitrage_input(self):
        """Test avec saisie explicite du vitrage."""
        inp = CalculInput(
            famille="FENETRES A FRAPPE",
            chassis="BOIS - Fixe",
            couleur="Blanc - RAL 9010",
            hauteur_mm=1200,
            largeur_mm=800,
            vitrages=[VitragInput(zone="G1", composition="4FE/16argon/4", intercalaire="Warm-Edge")],
        )
        result = calculer(inp)
        assert result.menuiserie_seule.Uw > 0
        assert len(result.details.zones_vitrage) >= 1

    def test_chassis_unknown_raises(self):
        with pytest.raises(ValueError):
            calculer(CalculInput(
                famille="FENETRES A FRAPPE",
                chassis="Châssis Inexistant",
                couleur="Blanc - RAL 9010",
                hauteur_mm=1200,
                largeur_mm=800,
            ))

    def test_result_details_populated(self):
        inp = CalculInput(
            famille="FENETRES A FRAPPE",
            chassis="BOIS - Fixe",
            couleur="Blanc - RAL 9010",
            hauteur_mm=1200,
            largeur_mm=800,
        )
        result = calculer(inp)
        d = result.details
        assert d.chassis_id > 0
        assert d.geo_type == "1_vantail"
        assert d.Uf_moyen > 0
        assert d.Af_total > 0
        assert d.Ag_total > 0
        assert d.surface_totale == pytest.approx(1.2 * 0.8, rel=1e-3)


# ---------------------------------------------------------------------------
# Panneaux (Up / Psi_p)
# ---------------------------------------------------------------------------

class TestPanneaux:
    def test_psi_p_constant(self):
        """Psi_p doit valoir 0.019 pour toutes les gammes."""
        assert PSI_P == 0.019

    def test_porte_soubassement_uses_psi_p(self):
        """La zone panneau d'une porte soubassement doit utiliser Psi_p, pas Psi_g."""
        inp = CalculInput(
            famille="PORTES CREMONE-SERRURE-SERVICE",
            chassis="BOIS - Porte crémone 1 vantail avec soubassement",
            couleur="Blanc - RAL 9010",
            hauteur_mm=2150,
            largeur_mm=900,
            vitrages=[VitragInput(zone="G1", composition="4FE/16argon/4", intercalaire="Warm-Edge")],
            panneaux=[VitragInput(zone="P1", composition="Plate bande 28", intercalaire="Warm-Edge")],
        )
        result = calculer(inp)
        zones = result.details.zones_vitrage
        # Zone G1 = vitrage, Zone P1 = panneau
        g1 = next(z for z in zones if z.zone == "G1")
        p1 = next(z for z in zones if z.zone == "P1")
        assert g1.Psi_g != PSI_P  # vitrage uses dynamic Psi_g
        assert p1.Psi_g == pytest.approx(PSI_P)  # panneau uses fixed Psi_p
        assert p1.Ug == pytest.approx(2.4)  # Up of Plate bande 28

    def test_panneau_zone_labels(self):
        """Les zones panneaux doivent être labellées P1, P2, etc."""
        inp = CalculInput(
            famille="PORTES CREMONE-SERRURE-SERVICE",
            chassis="BOIS - Porte crémone 1 vantail avec soubassement",
            couleur="Blanc - RAL 9010",
            hauteur_mm=2150,
            largeur_mm=900,
        )
        result = calculer(inp)
        labels = [z.zone for z in result.details.zones_vitrage]
        assert "G1" in labels
        assert "P1" in labels

    def test_panneau_sw_uses_sp(self):
        """Sw avec panneau doit utiliser Sp = alpha*Up/he, pas Sg=0."""
        geo = _simple_geo(Ag=0.5, lg=3.0, Af_total=0.3, Ufi_moyen=2.0)
        # Add a panneau zone
        geo.zones.append(ZoneVitrage(Ag=0.2, lg=2.0, index=1))
        geo.Ag_total += 0.2
        geo.surface_totale += 0.2
        vd = [
            {"Ug": 1.1, "Psi_g": 0.08, "Sg": 0.65, "Tlg": 0.82},
            {"Ug": 2.4, "Psi_g": PSI_P, "Sg": 0, "Tlg": 0, "is_panneau": True},
        ]
        alpha = 0.4
        sw = _calc_sw(geo, vd, alpha)
        Sf = alpha * 2.0 / HE
        Sp = alpha * 2.4 / HE
        expected = (0.3 * Sf + 0.5 * 0.65 + 0.2 * Sp) / (0.5 + 0.2 + 0.3)
        assert sw == pytest.approx(expected, rel=1e-6)
        # Sw must be > 0 because panneau contributes via Sp
        assert sw > 0

    def test_panneau_default_values(self):
        """Sans saisie panneau, les valeurs par défaut doivent être Up=2.4, Psi_p=0.019."""
        inp = CalculInput(
            famille="PORTES CREMONE-SERRURE-SERVICE",
            chassis="BOIS - Porte crémone 1 vantail avec soubassement",
            couleur="Blanc - RAL 9010",
            hauteur_mm=2150,
            largeur_mm=900,
            # Pas de vitrages/panneaux saisis
        )
        result = calculer(inp)
        p1 = next(z for z in result.details.zones_vitrage if z.zone == "P1")
        assert p1.Ug == pytest.approx(2.4)
        assert p1.Psi_g == pytest.approx(PSI_P)


# ---------------------------------------------------------------------------
# Hauteur soubassement configurable
# ---------------------------------------------------------------------------

class TestHauteurSoubassement:
    def test_explicit_450_matches_default(self):
        """450mm explicite doit donner le même résultat que sans le champ."""
        base = dict(
            famille="PORTES CREMONE-SERRURE-SERVICE",
            chassis="BOIS - Porte crémone 1 vantail avec soubassement",
            couleur="Blanc - RAL 9010",
            hauteur_mm=2150,
            largeur_mm=900,
        )
        r_default = calculer(CalculInput(**base))
        r_explicit = calculer(CalculInput(**base, hauteur_soubassement_mm=450))
        assert r_default.menuiserie_seule.Uw == pytest.approx(r_explicit.menuiserie_seule.Uw)

    def test_custom_hauteur_changes_uw(self):
        """Une hauteur soubassement différente doit changer Uw."""
        base = dict(
            famille="PORTES CREMONE-SERRURE-SERVICE",
            chassis="BOIS - Porte crémone 1 vantail avec soubassement",
            couleur="Blanc - RAL 9010",
            hauteur_mm=2150,
            largeur_mm=900,
        )
        r_default = calculer(CalculInput(**base))
        r_custom = calculer(CalculInput(**base, hauteur_soubassement_mm=700))
        assert r_default.menuiserie_seule.Uw != pytest.approx(r_custom.menuiserie_seule.Uw, abs=1e-4)

    def test_ignored_for_fenetre(self):
        """Pour une fenêtre, le champ est ignoré (pas de crash)."""
        inp = CalculInput(
            famille="FENETRES A FRAPPE",
            chassis="BOIS - Fixe",
            couleur="Blanc - RAL 9010",
            hauteur_mm=1200,
            largeur_mm=800,
            hauteur_soubassement_mm=600,
        )
        result = calculer(inp)
        assert result.menuiserie_seule.Uw > 0
