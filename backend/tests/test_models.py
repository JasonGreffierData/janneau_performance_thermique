"""
Tests de validation des modèles Pydantic.
"""

import pytest
from pydantic import ValidationError

from app.models.inputs import CalculInput, VitragInput, VoletInput


class TestCalculInput:
    def test_valid_minimal(self):
        inp = CalculInput(
            famille="FENETRES A FRAPPE",
            chassis="BOIS - Fixe",
            couleur="Blanc",
            hauteur_mm=1200,
            largeur_mm=800,
        )
        assert inp.hauteur_mm == 1200

    def test_hauteur_must_be_positive(self):
        with pytest.raises(ValidationError):
            CalculInput(
                famille="F", chassis="C", couleur="B",
                hauteur_mm=0, largeur_mm=800,
            )

    def test_largeur_must_be_positive(self):
        with pytest.raises(ValidationError):
            CalculInput(
                famille="F", chassis="C", couleur="B",
                hauteur_mm=1200, largeur_mm=-1,
            )

    def test_default_volet(self):
        inp = CalculInput(
            famille="F", chassis="C", couleur="B",
            hauteur_mm=1200, largeur_mm=800,
        )
        assert inp.volet.actif is False
        assert inp.vitrages == []
        assert inp.panneaux == []


class TestVitragInput:
    def test_defaults(self):
        v = VitragInput(zone="G1", composition="4/16/4")
        assert v.intercalaire == "Warm-Edge"


class TestVoletInput:
    def test_defaults(self):
        v = VoletInput()
        assert v.actif is False
        assert v.type is None
        assert v.isolation_acoustique == "T"
