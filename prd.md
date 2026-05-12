# PRD — Calculateur de Performances Thermiques JANNEAU

**Version** : 1.0  
**Date** : 2026-05-11  
**Source** : `Calculateur de performances thermiques JANNEAU.xlsm` (v1.6K, 19/11/2024)

---

## 1. Contexte et objectif

JANNEAU Menuiseries utilise un fichier Excel `.xlsm` pour calculer les performances thermiques et lumineuses de ses menuiseries (fenêtres, portes, baies coulissantes). Ce fichier, riche en macros VBA et en feuilles de calcul imbriquées, est difficile à maintenir, à partager et à intégrer dans d'autres outils.

**Objectif** : Remplacer ce fichier Excel par une application web moderne composée d'un **backend Python** (API REST) et d'un **frontend React**, le tout conteneurisé via Docker pour faciliter les livraisons à une équipe de développement.

---

## 2. Périmètre fonctionnel

### 2.1 Ce que fait le calculateur Excel

Le fichier Excel contient :

| Feuille | Rôle |
|---|---|
| `PILOTE` | Saisie utilisateur + affichage des résultats |
| `BDD` | Base de données de référence (gammes, vitrages, volets, couleurs, intercalaires) |
| `Nomenclatures` | Données profilés (Af, Uf par pièce) |
| `Résultats` | Table de résultats pré-calculés indexés par N° d'onglet |
| `1` à `266` | Un onglet de calcul par type de châssis (géométrie + formules EN ISO 10077-1) |
| `IMPRESSION` | Fiche de résultat imprimable |

### 2.2 Flux utilisateur actuel (PILOTE)

```
1. Sélection famille produit  →  2. Sélection type châssis
3. Sélection couleur extérieure
4. Saisie dimensions (H x L en mm, dos de profil)
5. Saisie volet (oui/non → type → isolation acoustique coffre)
6. Saisie remplissages vitrages (G1..G6) : composition + intercalaire
   (Panneau P1..P4 pour les portes)
→  Calcul automatique : Uw/Ud, Sw, Tlw, Ujn, Ubb.jn, Uc, rR
→  Export PDF fiche de résultats
```

---

## 3. Données de référence (BDD)

### 3.1 Familles de produits et types de châssis

**4 grandes familles :**

| Famille | Code interne |
|---|---|
| Fenêtres à frappe | `FENE` |
| Portes crémone-serrure-service | `PORT` |
| Baies coulissantes | `BAIE` |
| Portes d'entrée | `PORT` |

**Gammes de châssis (exemples) :**

Fenêtres à frappe : BOIS, CARLIS.J / LITTORAL.J, PRIMELIS / ANTALIS, EVOLUTION, ESSENTIEL  
Baies coulissantes : SOLARIS II Coulissant, SOLARIS II Galandage, CG-ALU, BOIS Coulissant  
Portes d'entrée : CAPITALES, CAPITALES MD76, FLEUVES ET RIVIERES, HYLLIADE, LUMIS, ALLIS  
Portes crémone : BOIS, INNONOVA, CARLIS.J, PRIMELIS, EVOLUTION, ESSENTIEL

**Types d'ouverture (exemples) :**
- Fixe
- Française 1, 2, 3, 4 vantaux
- Française 2 vantaux + 1 ou 2 fixes latéraux
- Oscillo-battante 1, 2 vantaux
- Soufflet
- Coulissant 2R, 3R, Galandage
- Avec/sans ouvrant épaissi ou faux ouvrant

Chaque châssis est identifié par un **numéro d'onglet** (1 à 266+) qui indique la géométrie de calcul à utiliser.  
Propriétés par châssis : `nb_vitrages`, `nb_panneaux`.

### 3.2 Base vitrages (double et triple)

Champs par composition de vitrage :

| Champ | Description | Unité |
|---|---|---|
| `composition` | Ex. `4FE/20argon/4` | — |
| `Ug` | Coefficient de transmission thermique du vitrage | W/m².K |
| `Sg` | Facteur solaire total | — |
| `Sg1`, `Sg2`, `Sg3` | Facteurs solaires partiels | — |
| `Tlg` | Facteur de transmission lumineuse | — |

### 3.3 Base intercalaires (Psi g)

La valeur `Psi_g` (coefficient linéique de pont thermique en périphérie du vitrage) dépend de :
- La gamme du châssis (`BOIS`, `INNO`, `CARL`, `EXCL`, `SOLA`, etc.)
- Le type d'intercalaire (`Warm-Edge`, `Aluminium`, etc.)
- La valeur Ug du vitrage

Lookup : `CONCATENATE(gamme_code, intercalaire, Ug)` → `Psi_g` [W/(m·K)]

### 3.4 Base couleurs (coefficient d'absorption α)

4 catégories d'absorption :

| Code | Catégorie | α |
|---|---|---|
| 1 | Claire (blanc, jaune, orange, rouge clair) | 0.4 |
| 2 | Moyenne (rouge sombre, vert clair, bleu clair) | 0.6 |
| 3 | Sombre (brun, vert sombre, bleu vif) | 0.8 |
| 4 | Noire (noir, brun sombre, bleu sombre) | 1.0 |

Chaque couleur commerciale est mappée sur un code 1-4 selon la famille de produit.

### 3.5 Base volets (stores / shutters)

Champs par type de volet :

| Champ | Description | Unité |
|---|---|---|
| `designation` | Ex. `Bloc Baie - Coffre 170 - Tablier 8*40 PVC` | — |
| `compatible_gammes` | Liste des gammes compatibles (BOIS, INNO, CARL, EXCL, SOLA, SOII) | — |
| `rR` | Résistance thermique additionnelle du volet fermé | m².K/W |
| `hauteur_coffre` | Hauteur du coffre de volet | m |

**Coefficients UC du coffre de volet** (formule `Uc = a + b/L`) :

Par type de volet et par niveau d'isolation acoustique (`T`, `P0`, `P1`, `P2`, `P3`, `P4`) : paramètres `a` et `b`.

### 3.6 Données profilés (Nomenclatures)

Par pièce de profil (dormant, ouvrant principal, ouvrant SFX, meneau/traverse) :

| Champ | Description | Unité |
|---|---|---|
| `Af` | Largeur du nœud (largeur de la pièce de cadre visible) | m |
| `Uf` | Coefficient de transmission thermique du profilé | W/m².K |

Ces valeurs sont pré-définies pour chaque combinaison châssis/pièce dans les onglets de calcul.

---

## 4. Formules de calcul

Toutes les formules sont conformes aux normes :
- **EN ISO 10077-1** (juin 2012) : Uw, Ujn
- **XP P50-777** (décembre 2011) : Sw, Tlw

### 4.1 Uw — Transmission thermique de la menuiserie

```
Uw = ( Σ(Ug_i × Ag_i) + Σ(Ψg_i × lg_i) + Σ(Uf_j × Af_j) ) / ( Σ(Ag_i) + Σ(Af_j) )
```

- `Ug_i` : transmission thermique du vitrage i [W/m².K]
- `Ag_i` : aire du vitrage i [m²]  
- `Ψg_i` : coefficient linéique de pont thermique en périphérie du vitrage i [W/(m·K)]
- `lg_i` : périmètre développé du vitrage i [m]
- `Uf_j` : transmission thermique du profilé j [W/m².K]
- `Af_j` : aire du profilé j [m²]

**Pour les portes** : coefficient noté `Ud` (même formule, avec panneaux à la place des vitrages).

#### Calcul des aires et périmètres

La géométrie exacte (décomposition en traverse haute, traverse basse, montants, masse centrale, etc.) est spécifique à chaque type de châssis (onglets 1 à 266). Chaque onglet encode les formules de décomposition dimensionnelle en fonction de H (hauteur) et L (largeur) dos de profil.

**Uf moyen du cadre** :
```
Uf_moyen = SUMPRODUCT(Af_j, Uf_j) / SUM(Af_j)
```

### 4.2 Sw — Facteur solaire de la menuiserie

```
Sw = ( Σ(Af_j) × Sf + Σ(Ag_i × Sg_i) ) / ( Σ(Ag_i) + Σ(Af_j) )
```

Avec le facteur solaire du cadre :
```
Sf = α × Uf_moyen / he
```
- `α` : coefficient d'absorption de la couleur (0.4 / 0.6 / 0.8 / 1.0)
- `he` : coefficient d'échange superficiel extérieur = **25 W/(m².K)**

### 4.3 Tlw — Transmission lumineuse de la menuiserie

```
Tlw = Σ(Ag_i) / (Σ(Ag_i) + Σ(Af_j)) × ( Σ(Ag_i × Tlg_i) / Σ(Ag_i) )
```

- `Tlg_i` : facteur de transmission lumineuse du vitrage i

### 4.4 Ujn — Transmission thermique avec volet fermé (nuit)

```
Ujn = ( Uw + 1/(1/Uw + rR) ) / 2
```

- `rR` : résistance thermique additionnelle du volet [m².K/W]

### 4.5 Ubb.jn — Transmission thermique avec coffre de volet

```
Ubb.jn = ( Ujn × A_menuiserie + Uc × A_coffre ) / ( A_menuiserie + A_coffre )
```

Avec :
```
Uc = a + b / L
A_coffre = hauteur_coffre × L
```
- `L` : largeur de la menuiserie [m]
- `a`, `b` : paramètres du volet selon l'isolation acoustique choisie
- `A_menuiserie` = H × L

---

## 5. Spécifications techniques de l'application

### 5.1 Architecture cible

```
┌─────────────────────────────────────────────────────┐
│                    Docker Compose                    │
│                                                     │
│  ┌───────────────┐       ┌──────────────────────┐  │
│  │  frontend     │       │  backend             │  │
│  │  React + Vite │──────▶│  FastAPI (Python)    │  │
│  │  Port 3000    │       │  Port 8000           │  │
│  └───────────────┘       └──────────┬───────────┘  │
│                                     │              │
│                          ┌──────────▼───────────┐  │
│                          │  SQLite / JSON        │  │
│                          │  (base de données     │  │
│                          │   de référence BDD)   │  │
│                          └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 5.2 Backend Python (FastAPI)

**Stack :** Python 3.12, FastAPI, Pydantic v2, Uvicorn

#### Endpoints API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/familles` | Liste des familles de produits |
| `GET` | `/api/chassis` | Liste des types de châssis (filtrable par famille) |
| `GET` | `/api/couleurs` | Liste des couleurs par famille de produit |
| `GET` | `/api/vitrages` | Liste des compositions de vitrage disponibles |
| `GET` | `/api/intercalaires` | Liste des types d'intercalaires |
| `GET` | `/api/volets` | Liste des volets (filtrables par gamme de châssis) |
| `POST` | `/api/calculer` | Calcul des performances thermiques |
| `POST` | `/api/fiche/pdf` | Génération de la fiche PDF de résultats |

#### Corps de la requête `/api/calculer`

```json
{
  "famille": "FENETRES A FRAPPE",
  "chassis": "CARLIS.J - Française 2 vantaux",
  "couleur": "Gris AS1",
  "hauteur_mm": 1480,
  "largeur_mm": 1530,
  "volet": {
    "actif": true,
    "type": "Bloc Baie - Coffre 170 - Tablier 8*40 PVC",
    "isolation_acoustique": "T"
  },
  "vitrages": [
    {
      "zone": "G1",
      "composition": "4FE/20argon/4",
      "intercalaire": "Warm-Edge"
    },
    {
      "zone": "G2",
      "composition": "4FE/20argon/4",
      "intercalaire": "Warm-Edge"
    }
  ],
  "panneaux": []
}
```

#### Corps de la réponse `/api/calculer`

```json
{
  "menuiserie_seule": {
    "Uw": 1.271,
    "Sw": 0.448,
    "Tlw": 55.02
  },
  "avec_volet": {
    "rR": 0.187,
    "Ujn": 0.XXX,
    "Ubb_jn": 0.XXX,
    "Uc": 1.XXX
  },
  "details": {
    "chassis_id": 211,
    "Uf_moyen": 1.1,
    "aires": { "Af_total": 0.XXX, "Ag_total": 0.XXX },
    "normes": ["EN ISO 10077-1 (juin 2012)", "XP P50-777 (décembre 2011)"]
  }
}
```

#### Organisation du code backend

```
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── api/
│   │   ├── routes.py        # Définition des routes
│   ├── core/
│   │   ├── calculator.py    # Moteur de calcul (formules EN ISO 10077-1)
│   │   ├── geometry.py      # Décomposition géométrique par type de châssis
│   │   └── pdf_generator.py # Génération PDF fiche résultats
│   ├── data/
│   │   ├── chassis.json     # Données des types de châssis (géométrie)
│   │   ├── vitrages.json    # Base vitrages (Ug, Sg, Tlg)
│   │   ├── intercalaires.json # Psi_g par gamme/intercalaire/Ug
│   │   ├── couleurs.json    # Couleurs + coefficient α
│   │   └── volets.json      # Volets (rR, a, b par isolation)
│   └── models/
│       ├── inputs.py        # Pydantic input models
│       └── outputs.py       # Pydantic output models
├── requirements.txt
└── Dockerfile
```

### 5.3 Frontend React

**Stack :** React 18, Vite, TypeScript, TailwindCSS

#### Écrans / Vues

**Vue principale (formulaire de calcul) :**

```
┌──────────────────────────────────────────────────┐
│  JANNEAU — Calculateur de Performances Thermiques │
├──────────────┬───────────────────────────────────┤
│              │                                    │
│  MA FENÊTRE  │  RÉSULTATS                        │
│              │                                    │
│  Famille     │  TRANSMISSION THERMIQUE            │
│  [dropdown]  │  Uw = 1.271 W/m².K               │
│              │                                    │
│  Type châssis│  FACTEUR SOLAIRE                  │
│  [dropdown]  │  Sw = 0.448                       │
│              │                                    │
│  Couleur     │  TRANSMISSION LUMINEUSE           │
│  [dropdown]  │  Tlw = 55.0 %                    │
│              │                                    │
│  H: [____]mm │  ─────────────────                │
│  L: [____]mm │  AVEC VOLET FERMÉ                 │
│              │  Ujn   = X.XXX W/m².K            │
│  Volet       │  Ubb.jn = X.XXX W/m².K           │
│  [toggle]    │  Uc    = X.XXX W/m².K            │
│  → Type      │  rR    = 0.187 m².K/W            │
│  → Isolation │                                    │
│              │  [Télécharger fiche PDF]           │
│  REMPLISSAGES│                                    │
│  G1 [compo]  │                                    │
│     [interc] │                                    │
│  G2 [compo]  │                                    │
│     [interc] │                                    │
│  ...         │                                    │
└──────────────┴───────────────────────────────────┘
```

#### Comportement dynamique

- Les dropdowns sont **cascadants** : la liste des types de châssis se filtre selon la famille choisie
- Le nombre de zones de vitrage (G1..G6) s'affiche dynamiquement selon le châssis sélectionné (`nb_vitrages`)
- Les panneaux (P1..P4) s'affichent pour les portes (`nb_panneaux > 0`)
- Le champ volet n'apparaît pas pour les portes d'entrée
- Les résultats se mettent à jour **en temps réel** à chaque modification d'un champ (debounce 300ms)
- La section "Avec volet fermé" ne s'affiche que si un volet est sélectionné
- Indicateurs visuels de performance (couleurs selon seuils RE2020)

#### Organisation du code frontend

```
frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── FormFenetre.tsx       # Formulaire principal
│   │   ├── SelectChassis.tsx     # Sélecteur famille + châssis
│   │   ├── SelectVitrages.tsx    # Zones de vitrage dynamiques
│   │   ├── SelectVolet.tsx       # Sélecteur volet + isolation
│   │   └── ResultatsPanel.tsx    # Panneau de résultats
│   ├── hooks/
│   │   └── useCalculateur.ts     # Hook de calcul (appel API + debounce)
│   ├── api/
│   │   └── calculateur.ts        # Fonctions d'appel API
│   └── types/
│       └── index.ts              # Types TypeScript
├── package.json
├── vite.config.ts
└── Dockerfile
```

### 5.4 Conteneurisation (Docker)

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./backend/app/data:/app/data"]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on: [backend]
```

---

## 6. Extraction et migration des données Excel

La migration des données depuis le fichier `.xlsm` vers des fichiers JSON est une étape critique. Un script Python dédié (`scripts/extract_bdd.py`) doit :

1. **Extraire la BDD** (onglet `BDD`) :
   - Liste exhaustive des châssis (nom, id onglet, nb_vitrages, nb_panneaux)
   - Base vitrages (Ug, Sg, Tlg)
   - Table Psi_g par intercalaire
   - Table couleurs + α
   - Table volets (rR, hauteur coffre, paramètres a/b par isolation)

2. **Extraire la géométrie de chaque châssis** (onglets 1-266) :
   - Dimensions des profilés (Af_j, Uf_j par pièce)
   - Formules de décomposition géométrique (exprimées en fonction de H et L)

3. **Extraire les Nomenclatures** (onglet `Nomenclatures`) :
   - Données profilés par gamme et type de nœud

> **Note** : Les formules Excel des onglets individuels doivent être ré-implémentées en Python pur. Il ne s'agit pas de les exécuter via une bibliothèque Excel, mais de les traduire en code Python maintenable.

---

## 7. Fiche de résultats (hors scope MVP)

La fiche imprimable (actuellement l'onglet `IMPRESSION` du fichier Excel) sera réalisée comme une **page web dédiée** dans une version post-MVP. Elle contiendra :

- En-tête : Client, Commande, Devis, Chantier, Repère
- Composition de la menuiserie : famille, type, couleur, dimensions, volet
- Remplissages : liste des vitrages (composition, intercalaire, Ug)
- Résultats : Uw/Ud, Sw, Tlw (et Ujn, Ubb.jn si volet)
- Mentions normatives : EN ISO 10077-1, XP P50-777
- Disclaimer : *"Ce calcul de performance thermique et lumineuse ne vaut pas pour acceptation de faisabilité technique du produit."*
- Date et lieu : Loroux-Bottereau

---

## 8. Contraintes et exigences non-fonctionnelles

| Exigence | Détail |
|---|---|
| Fidélité des calculs | Les résultats doivent correspondre à ±0.001 près aux valeurs du fichier Excel pour chaque châssis |
| Couverture châssis | Tous les types de châssis du fichier Excel doivent être supportés (~266 types) |
| Normes | EN ISO 10077-1 (juin 2012), XP P50-777 (décembre 2011) |
| Temps de réponse | Calcul < 200ms, rendu PDF < 2s |
| Conteneurisation | Docker + Docker Compose, `docker compose up` doit suffire à démarrer l'app |
| Environnement | Compatible Linux/WSL2, macOS, Windows avec Docker Desktop |
| Données sensibles | Aucune authentification requise (usage interne Janneau) |
| Maintenance | Code lisible et documenté, les données de référence dans des JSON séparés du code métier |

---

## 9. Plan de développement MVP

> **Périmètre MVP** : prototype fonctionnel à remettre à l'équipe de développement qui prendra le relais pour la mise en production. Le PDF et les autres features avancées sont hors scope MVP.

### Phase 1 — Extraction et données (fondations)
1. Script `extract_bdd.py` : extraire les données BDD → JSON
2. Script `extract_geometry.py` : extraire la géométrie de chaque onglet châssis → JSON
3. Tests de validation : comparer les résultats Python avec l'Excel sur un panel de 10 châssis représentatifs

### Phase 2 — Backend
4. Modèles Pydantic (inputs/outputs)
5. Moteur de calcul (`calculator.py`) implémentant les formules §4
6. Module géométrie (`geometry.py`) : décomposition H×L par type de châssis
7. Routes FastAPI + Dockerfile backend
8. Tests unitaires moteur de calcul

### Phase 3 — Frontend
9. Structure React + Vite + TypeScript + Tailwind
10. Composants FormFenetre, SelectChassis, SelectVitrages, SelectVolet
11. Hook `useCalculateur` avec debounce
12. Panneau de résultats avec indicateurs visuels
13. Dockerfile frontend

### Phase 4 — Intégration et handoff
14. `docker-compose.yml` : `docker compose up` démarre l'app complète
15. README développeur : setup, architecture, comment ajouter un châssis, comment mettre à jour les données BDD
16. Tests end-to-end rapides (smoke tests)

---

## Hors scope MVP (features post-livraison)

- Génération PDF / fiche de résultats imprimable (sera une page web intégrée)
- Authentification / gestion des utilisateurs
- Historique des calculs
- Intégration dans un SI existant

---

## 10. Références

- Norme **EN ISO 10077-1:2012** — Performances thermiques des fenêtres, portes et fermetures
- Norme **XP P50-777:2011** — Calcul du facteur solaire et de la transmission lumineuse
- Fichier source : `Calculateur de performances thermiques JANNEAU.xlsm` (v1.6K, JANNEAU Menuiseries, Route d'Ancenis, 44430 Le Loroux-Bottereau)
