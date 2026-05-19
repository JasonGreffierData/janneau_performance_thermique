"""
Tests des endpoints API (routes.py).
"""

import pytest


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Familles
# ---------------------------------------------------------------------------

def test_get_familles(client):
    r = client.get("/api/familles")
    assert r.status_code == 200
    familles = r.json()
    assert isinstance(familles, list)
    assert len(familles) >= 4
    assert "FENETRES A FRAPPE" in familles


# ---------------------------------------------------------------------------
# Chassis
# ---------------------------------------------------------------------------

class TestChassisEndpoint:
    def test_list_all(self, client):
        r = client.get("/api/chassis")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        assert "nom" in data[0]
        assert "supporte" in data[0]

    def test_filter_by_famille(self, client):
        r = client.get("/api/chassis", params={"famille": "FENETRES A FRAPPE"})
        data = r.json()
        assert all(c["famille"] == "FENETRES A FRAPPE" for c in data)

    def test_no_colors_in_chassis(self, client):
        """Régression : les couleurs ne doivent pas apparaître dans les châssis."""
        r = client.get("/api/chassis")
        data = r.json()
        color_keywords = ["ral ", "impression blanche", "ifh"]
        for c in data:
            nom = c["nom"].lower()
            # Un vrai châssis a un type identifiable
            has_type = any(kw in nom for kw in [
                "fixe", "française", "vantail", "vantaux", "porte",
                "oscillo", "soufflet", "coulissant", "galandage", "battante",
            ])
            if not has_type:
                for kw in color_keywords:
                    assert kw not in nom, f"Couleur trouvée dans châssis : {c['nom']}"

    def test_chassis_info(self, client):
        r = client.get("/api/chassis/1/info")
        assert r.status_code == 200
        data = r.json()
        assert "geo_type" in data
        assert "pieces" in data

    def test_chassis_info_not_found(self, client):
        r = client.get("/api/chassis/999999/info")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Vitrages
# ---------------------------------------------------------------------------

def test_get_vitrages(client):
    r = client.get("/api/vitrages")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    assert "composition" in data[0]
    assert "Ug" in data[0]


# ---------------------------------------------------------------------------
# Intercalaires
# ---------------------------------------------------------------------------

def test_get_intercalaires(client):
    r = client.get("/api/intercalaires")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ---------------------------------------------------------------------------
# Couleurs
# ---------------------------------------------------------------------------

def test_get_couleurs(client):
    r = client.get("/api/couleurs")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    assert "nom" in data[0]
    assert "alpha" in data[0]


# ---------------------------------------------------------------------------
# Volets
# ---------------------------------------------------------------------------

def test_get_volets(client):
    r = client.get("/api/volets")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Calculer
# ---------------------------------------------------------------------------

class TestCalculerEndpoint:
    def test_success(self, client):
        r = client.post("/api/calculer", json={
            "famille": "FENETRES A FRAPPE",
            "chassis": "BOIS - Fixe",
            "couleur": "Blanc - RAL 9010",
            "hauteur_mm": 1200,
            "largeur_mm": 800,
        })
        assert r.status_code == 200
        data = r.json()
        assert "menuiserie_seule" in data
        assert data["menuiserie_seule"]["Uw"] > 0

    def test_invalid_chassis_400(self, client):
        r = client.post("/api/calculer", json={
            "famille": "FENETRES A FRAPPE",
            "chassis": "Inexistant",
            "couleur": "Blanc - RAL 9010",
            "hauteur_mm": 1200,
            "largeur_mm": 800,
        })
        assert r.status_code == 400

    def test_missing_fields_422(self, client):
        r = client.post("/api/calculer", json={
            "famille": "FENETRES A FRAPPE",
        })
        assert r.status_code == 422

    def test_zero_height_422(self, client):
        r = client.post("/api/calculer", json={
            "famille": "FENETRES A FRAPPE",
            "chassis": "BOIS - Fixe",
            "couleur": "Blanc - RAL 9010",
            "hauteur_mm": 0,
            "largeur_mm": 800,
        })
        assert r.status_code == 422

    def test_with_vitrage(self, client):
        r = client.post("/api/calculer", json={
            "famille": "FENETRES A FRAPPE",
            "chassis": "BOIS - Fixe",
            "couleur": "Blanc - RAL 9010",
            "hauteur_mm": 1200,
            "largeur_mm": 800,
            "vitrages": [
                {"zone": "G1", "composition": "4FE/16argon/4", "intercalaire": "Warm-Edge"},
            ],
        })
        assert r.status_code == 200
        assert len(r.json()["details"]["zones_vitrage"]) >= 1

    def test_with_hauteur_soubassement(self, client):
        r = client.post("/api/calculer", json={
            "famille": "PORTES CREMONE-SERRURE-SERVICE",
            "chassis": "BOIS - Porte crémone 1 vantail avec soubassement",
            "couleur": "Blanc - RAL 9010",
            "hauteur_mm": 2150,
            "largeur_mm": 900,
            "hauteur_soubassement_mm": 600,
        })
        assert r.status_code == 200
        assert r.json()["menuiserie_seule"]["Uw"] > 0

    def test_invalid_hauteur_soubassement_422(self, client):
        r = client.post("/api/calculer", json={
            "famille": "PORTES CREMONE-SERRURE-SERVICE",
            "chassis": "BOIS - Porte crémone 1 vantail avec soubassement",
            "couleur": "Blanc - RAL 9010",
            "hauteur_mm": 2150,
            "largeur_mm": 900,
            "hauteur_soubassement_mm": 50,
        })
        assert r.status_code == 422
