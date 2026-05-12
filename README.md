# Calculateur de Performances Thermiques JANNEAU

Application web remplaçant le fichier Excel `Calculateur de performances thermiques JANNEAU.xlsm`.

**Backend** : Python 3.12 · FastAPI · Pydantic v2  
**Frontend** : React 18 · TypeScript · Vite · Tailwind CSS  
**Conteneurisation** : Docker Compose

Normes implémentées :
- **EN ISO 10077-1** (Uw / Ud, Ujn, Ubb.jn)
- **XP P50-777** (Sw, Tlw)

---

## Démarrage rapide (Docker)

```bash
# Construire et démarrer les deux services
docker compose up --build

# Frontend : http://localhost:3000
# Backend API : http://localhost:8000
# Documentation API (Swagger) : http://localhost:8000/docs
```

---

## Développement local

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 (proxy vers backend:8000)
```

Pour le proxy local, modifier `frontend/vite.config.ts` :
```ts
proxy: {
  "/api": { target: "http://localhost:8000", ... }
}
```

---

## Structure du projet

```
├── backend/
│   ├── app/
│   │   ├── api/routes.py        # Endpoints FastAPI
│   │   ├── core/
│   │   │   ├── calculator.py    # Moteur de calcul (EN ISO 10077-1, XP P50-777)
│   │   │   └── geometry.py      # Décomposition géométrique par type de châssis
│   │   ├── data/                # JSON extraits du fichier Excel
│   │   │   ├── chassis.json
│   │   │   ├── chassis_geometry.json
│   │   │   ├── vitrages.json
│   │   │   ├── psi_g.json
│   │   │   ├── couleurs.json
│   │   │   └── volets.json
│   │   ├── models/
│   │   │   ├── inputs.py        # Schémas Pydantic (requête)
│   │   │   └── outputs.py       # Schémas Pydantic (réponse)
│   │   └── main.py              # App FastAPI + CORS
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Client fetch vers /api/*
│   │   ├── components/          # Select, NumberInput, VitrageRow, ResultCard
│   │   ├── hooks/               # useReferentiels (data loading)
│   │   ├── types/               # Types TypeScript (CalculInput, CalculResult, …)
│   │   ├── App.tsx              # Page principale
│   │   └── main.tsx             # Point d'entrée React
│   ├── nginx.conf               # Proxy /api → backend + SPA fallback
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── extract_bdd.py           # Extraction BDD Excel → JSON
│   └── extract_geometry.py      # Extraction géométrie châssis → JSON
├── docker-compose.yml
└── prd.md                       # Product Requirements Document
```

---

## API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/familles` | Liste des familles de produits |
| GET | `/api/chassis?famille=...` | Liste des châssis (+ flag `supporte`) |
| GET | `/api/vitrages` | Compositions de vitrage disponibles |
| GET | `/api/intercalaires` | Types d'intercalaires |
| GET | `/api/couleurs` | Couleurs extérieures (avec coefficient α) |
| GET | `/api/volets?gamme_code=...` | Volets compatibles |
| POST | `/api/calculer` | **Calcul thermique** → Uw/Ud, Sw, Tlw, Ujn, Ubb.jn |
| GET | `/health` | Healthcheck |

Documentation interactive : `http://localhost:8000/docs`

### Exemple de requête POST `/api/calculer`

```json
{
  "famille": "FENETRES A FRAPPE",
  "chassis": "CARLIS.J Française 2 vantaux",
  "couleur": "Blanc",
  "hauteur_mm": 1150,
  "largeur_mm": 1200,
  "volet": { "actif": false, "type": null, "isolation_acoustique": "T" },
  "vitrages": [
    { "zone": "G1", "composition": "4/16Ar/4 Planitherm", "intercalaire": "Warm-Edge" },
    { "zone": "G2", "composition": "4/16Ar/4 Planitherm", "intercalaire": "Warm-Edge" }
  ],
  "panneaux": []
}
```

---

## Mise à jour des données de référence

Si le fichier Excel source est mis à jour :

```bash
# Depuis la racine du projet
python3 scripts/extract_bdd.py
python3 scripts/extract_geometry.py
# → Regénère les fichiers JSON dans backend/app/data/
```

---

## Types géométriques supportés (MVP)

| Code | Description |
|------|-------------|
| `1_vantail` | Fixe / 1 vantail / Soufflet |
| `2_vantaux` | Française 2 vantaux |
| `3_vantaux` | Française 3 vantaux |
| `4_vantaux` | Française 4 vantaux |
| `2_vantaux_1_fixe_lateral` | 2 vantaux + 1 fixe latéral |
| `2_vantaux_2_fixes_lateraux` | 2 vantaux + 2 fixes latéraux |
| `porte_soubassement` | Portes crémone / serrure / service |

Types hors MVP (non calculés) : coulissants, galandage, portes CAPITALES, imposte.
