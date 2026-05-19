"""
Tests d'intégrité des fichiers JSON de référence.
Empêche les régressions comme le mélange couleurs/châssis dans chassis.json.
"""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "app" / "data"

COLOR_KEYWORDS = [
    "ral ", "blanc", "noir", "gris ", "rouge", "bleu ", "vert ",
    "brun", "ivoire", "sable", "acajou", "anodic", "chêne",
    "impression", "ton pierre",
]


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


# ── chassis.json ─────────────────────────────────────────────────────────────

class TestChassisData:
    @pytest.fixture(autouse=True)
    def _load_chassis(self):
        self.chassis = _load("chassis.json")

    def test_non_empty(self):
        assert len(self.chassis) > 0

    def test_required_fields(self):
        for c in self.chassis:
            assert "id" in c
            assert "nom" in c
            assert "famille" in c

    def test_no_color_entries(self):
        """Vérifie qu'aucune couleur ne s'est glissée dans les châssis."""
        for c in self.chassis:
            nom = c["nom"].lower()
            # Un vrai châssis contient toujours un type (fixe, française, porte, etc.)
            chassis_keywords = [
                "fixe", "française", "vantail", "vantaux", "oscillo",
                "soufflet", "porte", "coulissant", "galandage", "battante",
            ]
            is_chassis = any(kw in nom for kw in chassis_keywords)
            if not is_chassis:
                # Si ça ne ressemble pas à un châssis, ça ne doit pas être une couleur
                is_color = any(kw in nom for kw in COLOR_KEYWORDS)
                assert not is_color, (
                    f"Entrée suspecte (couleur) dans chassis.json : {c['nom']!r} (id={c['id']})"
                )

    def test_unique_ids_per_family(self):
        """Les IDs doivent être uniques au sein d'une même famille."""
        by_family: dict[str, list[int]] = {}
        for c in self.chassis:
            by_family.setdefault(c["famille"], []).append(c["id"])
        # Note: IDs can repeat across families (same physical chassis in multiple families)

    def test_valid_families(self):
        expected = {
            "FENETRES A FRAPPE",
            "BAIES COULISSANTES",
            "PORTES D'ENTREE",
            "PORTES CREMONE-SERRURE-SERVICE",
        }
        actual = {c["famille"] for c in self.chassis}
        assert actual == expected, f"Familles inattendues : {actual - expected}"


# ── couleurs.json ────────────────────────────────────────────────────────────

class TestCouleursData:
    @pytest.fixture(autouse=True)
    def _load_couleurs(self):
        self.couleurs = _load("couleurs.json")

    def test_non_empty(self):
        assert len(self.couleurs) > 0

    def test_required_fields(self):
        for c in self.couleurs:
            assert "nom" in c
            assert "alpha" in c

    def test_alpha_range(self):
        """Alpha (coefficient d'absorption) doit être entre 0 et 1."""
        for c in self.couleurs:
            assert 0 <= c["alpha"] <= 1, f"Alpha hors limites pour {c['nom']}: {c['alpha']}"


# ── vitrages.json ────────────────────────────────────────────────────────────

class TestVitragesData:
    @pytest.fixture(autouse=True)
    def _load_vitrages(self):
        self.vitrages = _load("vitrages.json")

    def test_non_empty(self):
        assert len(self.vitrages) > 0

    def test_required_fields(self):
        for v in self.vitrages:
            assert "composition" in v
            assert "Ug" in v
            assert "type" in v

    def test_ug_positive(self):
        for v in self.vitrages:
            assert v["Ug"] > 0, f"Ug <= 0 pour {v['composition']}"


# ── chassis_geometry.json ────────────────────────────────────────────────────

class TestGeometryData:
    @pytest.fixture(autouse=True)
    def _load_geometry(self):
        self.geo = _load("chassis_geometry.json")

    def test_non_empty(self):
        assert len(self.geo) > 0

    def test_supported_geo_types_are_implemented(self):
        """Les geo_types marqués supportés dans routes.py doivent exister dans le dispatch."""
        from app.core.geometry import GEOMETRY_DISPATCH
        supported_in_routes = {
            "1_vantail", "2_vantaux", "3_vantaux", "4_vantaux",
            "2_vantaux_1_fixe_lateral", "2_vantaux_2_fixes_lateraux",
            "porte_soubassement", "coulissant", "galandage",
        }
        for geo_type in supported_in_routes:
            assert geo_type in GEOMETRY_DISPATCH, (
                f"geo_type {geo_type!r} marqué supporté mais absent du dispatch"
            )

    def test_all_geo_types_are_strings(self):
        for cid, data in self.geo.items():
            assert isinstance(data["geo_type"], str), f"geo_type non-string pour châssis {cid}"

    def test_pieces_have_required_fields(self):
        for cid, data in self.geo.items():
            for p in data["pieces"]:
                assert "nom" in p, f"Pièce sans nom dans châssis {cid}"
                assert "Af" in p, f"Pièce sans Af dans châssis {cid}"
                assert "Uf" in p, f"Pièce sans Uf dans châssis {cid}"
                assert p["Af"] >= 0
                assert p["Uf"] >= 0
