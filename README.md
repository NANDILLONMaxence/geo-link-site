<div align="center">

# 🌍 Geo Link Site

**Génération automatique et manuelle de liaisons réseau entre sites géographiques**
**Automatic and manual network link generation between geographic sites**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🇫🇷 [Français](#-français)** · **🇬🇧 [English](#-english)**

</div>

---

# 🇫🇷 Français

## 📋 Table des matières

- [À propos du projet](#-à-propos-du-projet)
- [Objectifs pédagogiques](#-objectifs-pédagogiques)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Algorithmes implémentés](#-algorithmes-implémentés)
- [Installation et lancement](#-installation-et-lancement)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [Formats de données](#-formats-de-données)
- [Collaboration avec l'IA](#-collaboration-avec-lia)
- [Contribuer](#-contribuer)
- [Licence](#-licence)

## 🎯 À propos du projet

**Geo Link Site** est une application web permettant de :

1. **Placer des sites** sur une carte interactive à partir de coordonnées géographiques (au format DMS — degrés, minutes, secondes — ou décimal WGS84).
2. **Générer automatiquement des liaisons réseau** entre ces sites en respectant des contraintes de degré (nombre minimum et maximum de liaisons par site) et une distance maximale optionnelle.
3. **Créer manuellement des liaisons** spécifiques quand l'utilisateur veut forcer certaines connexions.
4. **Exclure / réactiver / supprimer** des liaisons individuelles, visualiser des cercles de couverture autour des sites et exporter le résultat dans plusieurs formats (CSV, GeoJSON, HTML autonome).

Le projet vise à fournir un outil pratique pour la **planification de réseaux maillés** (télécommunications, capteurs IoT, réseaux radio, etc.) où la géographie et les contraintes physiques imposent des choix de topologie.

## 🎓 Objectifs pédagogiques

Au-delà de son utilité pratique, ce projet a été conçu comme un **support d'apprentissage multi-domaines**. Il poursuit plusieurs objectifs :

### Travailler sur plusieurs domaines techniques

- **Backend Python / Flask** : conception d'une API REST, gestion d'état applicatif, routage HTTP, sérialisation JSON.
- **Frontend JavaScript / HTML / CSS** : interface utilisateur réactive, cartographie interactive avec Leaflet, gestion d'événements et de modaux.
- **Géomatique** : conversion de coordonnées DMS ↔ WGS84, calculs de distances géodésiques avec `pyproj`, manipulation de GeoJSON.
- **Conteneurisation** : packaging avec Docker et orchestration via Docker Compose pour une exécution reproductible.

### Intégrer des algorithmes connus de réseau et de théorie des graphes

Le projet implémente trois algorithmes classiques utilisés dans la conception de réseaux :

- **Arbre couvrant minimal (MST)** — algorithme de Kruskal / Prim via NetworkX
- **Algorithme glouton (Greedy)** sous contraintes de degré
- **Approximation k-connectivity** — augmentation progressive de la connectivité du graphe

Ces algorithmes sont au cœur de problématiques réelles : conception de backbones, réseaux ad-hoc, tolérance aux pannes, etc.

### Apprendre à travailler avec plusieurs langages de programmation

Le projet combine plusieurs technologies dans un même produit cohérent :

| Langage / Techno | Rôle dans le projet                                |
|------------------|----------------------------------------------------|
| **Python**       | Logique métier, API REST, algorithmes de graphes   |
| **JavaScript**   | Interactivité, appels API, gestion d'état côté UI  |
| **HTML / Jinja** | Structure des pages et templating                  |
| **CSS**          | Mise en forme, layouts responsives                 |
| **Dockerfile**   | Définition de l'environnement d'exécution          |
| **YAML**         | Configuration Docker Compose                       |

L'idée est de pratiquer l'**intégration entre langages** (sérialisation, contrat d'API, gestion d'erreurs traversant le front et le back) plutôt que de rester confiné à un seul écosystème.

### Apprendre à collaborer avec une IA

Ce projet a aussi été l'occasion d'**expérimenter le pair-programming avec une IA générative** (voir la section [Collaboration avec l'IA](#-collaboration-avec-lia)). L'objectif n'est pas de déléguer mais d'apprendre à formuler des problèmes, relire du code généré, détecter les bugs introduits par l'IA, et faire des choix d'architecture éclairés.

## ✨ Fonctionnalités

- 🗺️ Carte interactive (OpenStreetMap via Leaflet)
- 📍 Ajout de sites par coordonnées DMS (`47°50'44.56''N`) ou décimales
- 🔗 Génération automatique de liaisons selon 3 algorithmes au choix
- ✋ Création manuelle de liaisons par simple clic sur 2 sites
- ⚙️ Contraintes par site : nombre min et max de liaisons
- 📏 Distance maximale paramétrable
- ❌ Exclusion / réactivation / suppression individuelle de liaisons
- 🔵 Cercles de couverture autour des sites (rayon paramétrable)
- 📥 Import CSV et GeoJSON
- 📤 Export CSV, GeoJSON (compatible QGIS / ArcGIS) et HTML autonome
- 🔄 Reset complet de l'application
- ⚠️ Limite de **55 sites** maximum (configurable dans `app/app.py`)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          Navigateur (Frontend)          │
│  ┌───────────────────────────────────┐  │
│  │  HTML + CSS + Leaflet             │  │
│  │  api.js  →  map.js  →  ui.js      │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │  HTTP / JSON (REST)
┌─────────────────▼───────────────────────┐
│         Serveur Flask (Backend)         │
│  ┌───────────────────────────────────┐  │
│  │  app.py        (routes REST)      │  │
│  │  services/                        │  │
│  │   ├─ convert.py   (DMS, geodesic) │  │
│  │   ├─ compute.py   (distances,     │  │
│  │   │                adjacence)     │  │
│  │   └─ storage.py   (CSV / GeoJSON) │  │
│  │  algorithms/                      │  │
│  │   ├─ mst_aug.py   (MST + aug.)    │  │
│  │   ├─ greedy.py    (glouton)       │  │
│  │   └─ kconnect.py  (k-connectivity)│  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

L'état de l'application est conservé **en mémoire côté serveur** — c'est volontaire pour garder le projet simple. Pour une utilisation multi-utilisateur ou persistante, il faudrait ajouter une base de données.

## 🧮 Algorithmes implémentés

### 1. MST + Augmentation (`mst_aug`)

Construit d'abord un **arbre couvrant minimal** (Minimum Spanning Tree) via NetworkX, garantissant la connectivité avec un coût total minimum. Puis ajoute des arêtes supplémentaires pour satisfaire les contraintes `min_links` de chaque site.

- ✅ Optimal pour minimiser la longueur totale des liaisons
- ✅ Garantit que le graphe est connexe
- ⚠️ Vulnérable à la panne d'un seul nœud (degré 1 fréquent)

### 2. Greedy (`greedy`)

Approche **gloutonne** : trie les arêtes par distance croissante et les ajoute une à une si elles respectent les contraintes de degré et n'introduisent pas de relation parent-enfant interdite.

- ✅ Rapide et intuitif
- ✅ Bon pour des cas simples
- ⚠️ Pas de garantie d'optimalité globale

### 3. K-Connectivity Approximation (`kconnect`)

Vise une **k-connectivité de nœud** (le graphe reste connexe même après suppression de `k-1` nœuds). Part d'un MST puis augmente progressivement la connectivité jusqu'à atteindre `k=3` quand c'est possible.

- ✅ Réseau plus robuste (tolérance aux pannes)
- ⚠️ Plus coûteux en arêtes
- ⚠️ Calcul de `node_connectivity` quadratique sur grands graphes

## 🚀 Installation et lancement

### Prérequis

- **Soit** Docker + Docker Compose (recommandé)
- **Soit** Python 3.11+ avec pip

### Option 1 — Docker (recommandé)

```bash
git clone https://github.com/<your-username>/geo-link-site.git
cd geo-link-site
docker compose up --build
```

Puis ouvre [http://localhost:5000](http://localhost:5000) dans ton navigateur.

Pour arrêter :

```bash
docker compose down
```

### Option 2 — Installation locale Python

```bash
git clone https://github.com/<your-username>/geo-link-site.git
cd geo-link-site

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
export FLASK_APP=app.app           # Linux / macOS
# set FLASK_APP=app.app            # Windows cmd
# $env:FLASK_APP="app.app"         # Windows PowerShell

flask run --host=0.0.0.0 --port=5000
```

Puis ouvre [http://localhost:5000](http://localhost:5000).

## 🕹️ Utilisation

### Ajouter un site

1. Clique sur **« + Ajouter un site »** dans le panneau de gauche.
2. Renseigne un identifiant unique, les coordonnées DMS et les contraintes `min_links` / `max_links`.
3. Le site apparaît sur la carte.

### Générer des liaisons automatiques

1. Choisis un **algorithme** (MST+Aug, Greedy ou K-Connect).
2. Optionnel : fixe une **distance maximale** en km.
3. Clique sur **« Générer liaisons »**.

### Créer une liaison manuelle

1. Active le mode **« Créer liaison manuelle »**.
2. Clique sur deux sites successivement.
3. Confirme dans la fenêtre qui apparaît.

Les liaisons manuelles s'affichent en **bleu**, les automatiques en **noir**, les exclues en **rouge pointillé**.

### Exclure / supprimer une liaison

Clique sur une liaison sur la carte pour ouvrir sa fenêtre de détails, puis **Exclure** (réversible) ou **Supprimer définitivement**.

### Importer / Exporter

- **CSV** : format combiné sites + liaisons (lisible par Excel / LibreOffice)
- **GeoJSON** : compatible avec QGIS, ArcGIS, et tous les SIG modernes
- **HTML** : carte interactive autonome utilisable hors-ligne

## 📁 Structure du projet

```
geo-link-site/
├── app/
│   ├── __init__.py
│   ├── app.py                    # Application Flask et routes REST
│   ├── services/
│   │   ├── __init__.py
│   │   ├── convert.py            # Conversions DMS / WGS84 et distances
│   │   ├── compute.py            # Calculs de graphes
│   │   └── storage.py            # Import/Export CSV, GeoJSON, HTML
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── mst_aug.py            # MST + Augmentation
│   │   ├── greedy.py             # Greedy avec contraintes
│   │   └── kconnect.py           # K-Connectivity approximation
│   ├── templates/
│   │   └── index.html            # Page principale (Jinja2)
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── api.js            # Client HTTP vers le backend
│           ├── map.js            # Gestion carte Leaflet
│           └── ui.js             # Logique UI
├── docs/                         # (réservé pour documentation future)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## 📄 Formats de données

### CSV combiné

```csv
type,id,lat_dms,lng_dms,lat,lng,min_links,max_links,site_a,site_b,distance_km,status,link_type
site,A,47°50'44.56''N,2°20'30.00''E,47.8457,2.3417,1,3,,,,,,
site,B,48°51'24.00''N,2°21'07.00''E,48.8567,2.3522,1,3,,,,,,
link,edge_a1b2,,,,,,,A,B,112.347,active,auto
```

### GeoJSON (export complet)

Compatible **QGIS**, **ArcGIS**, **Leaflet** et tout outil SIG suivant la [spécification RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946).

Les sites sont stockés comme `Feature` de type `Point`, les liaisons comme `Feature` de type `LineString`. Les métadonnées (paramètres, exclusions, statistiques) sont placées dans `properties` au niveau racine.

## 🤖 Collaboration avec l'IA

Ce projet a été développé en **collaboration avec une intelligence artificielle générative** (assistant de type LLM). Cette approche a permis :

- **D'accélérer la mise en place** du squelette (boilerplate Flask, configuration Docker, structure des fichiers).
- **D'explorer plusieurs algorithmes** plus rapidement, en faisant générer des variantes que j'ai ensuite comparées, débuggées et adaptées.
- **D'apprendre par revue de code** : relire et comprendre du code produit par l'IA est un excellent exercice pour identifier les anti-patterns, les bugs subtils et les choix discutables.
- **D'expérimenter le prompting** : formuler clairement un besoin technique est en soi une compétence transférable.

⚠️ **Important** : l'IA n'a pas été utilisée comme oracle. Chaque morceau de code généré a été **relu, testé et souvent réécrit** manuellement. L'IA est ici un outil d'apprentissage et de productivité, pas un substitut à la compréhension du code que l'on publie.

Cette transparence fait partie de la démarche pédagogique du projet : montrer qu'on peut tirer parti de l'IA tout en gardant la maîtrise de son code.

## 🤝 Contribuer

Les contributions sont les bienvenues ! Pour proposer une amélioration :

1. Fork le projet
2. Crée une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Commit tes changements (`git commit -m 'Ajout de ...'`)
4. Push la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvre une Pull Request

Idées d'améliorations à explorer :
- Persistance des données (SQLite, PostgreSQL / PostGIS)
- Support de plus de 55 sites
- Tests unitaires (pytest)
- CI/CD (GitHub Actions)
- Internationalisation (i18n) FR / EN
- Algorithme supplémentaire (Steiner tree, par exemple)

## 📜 Licence

Ce projet est distribué sous licence **MIT** — voir le fichier [LICENSE](LICENSE) pour les détails.

---

# 🇬🇧 English

## 📋 Table of contents

- [About the project](#-about-the-project)
- [Educational goals](#-educational-goals)
- [Features](#-features)
- [Architecture](#-architecture-1)
- [Implemented algorithms](#-implemented-algorithms)
- [Installation and launch](#-installation-and-launch)
- [Usage](#-usage)
- [Project structure](#-project-structure)
- [Data formats](#-data-formats)
- [Collaboration with AI](#-collaboration-with-ai)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 About the project

**Geo Link Site** is a web application that lets you:

1. **Place sites** on an interactive map using geographic coordinates (DMS format — degrees, minutes, seconds — or WGS84 decimal).
2. **Automatically generate network links** between these sites while respecting degree constraints (minimum and maximum number of links per site) and an optional maximum distance.
3. **Manually create specific links** when the user wants to force certain connections.
4. **Exclude / re-enable / delete** individual links, display coverage circles around sites and export the result in several formats (CSV, GeoJSON, standalone HTML).

The project aims to provide a practical tool for **mesh network planning** (telecommunications, IoT sensors, radio networks, etc.) where geography and physical constraints drive topology choices.

## 🎓 Educational goals

Beyond its practical use, this project was designed as a **multi-domain learning vehicle**. It pursues several goals:

### Working across multiple technical domains

- **Python / Flask backend**: REST API design, application state management, HTTP routing, JSON serialization.
- **JavaScript / HTML / CSS frontend**: reactive UI, interactive mapping with Leaflet, event and modal handling.
- **Geomatics**: DMS ↔ WGS84 coordinate conversion, geodesic distance computations with `pyproj`, GeoJSON manipulation.
- **Containerization**: packaging with Docker and orchestration via Docker Compose for reproducible execution.

### Integrating well-known network and graph theory algorithms

The project implements three classic algorithms used in network design:

- **Minimum Spanning Tree (MST)** — Kruskal / Prim algorithm via NetworkX
- **Greedy algorithm** under degree constraints
- **K-Connectivity approximation** — progressive augmentation of graph connectivity

These algorithms sit at the core of real-world problems: backbone design, ad-hoc networks, fault tolerance, etc.

### Learning to work with several programming languages

The project combines several technologies into one coherent product:

| Language / Tech  | Role in the project                                |
|------------------|----------------------------------------------------|
| **Python**       | Business logic, REST API, graph algorithms         |
| **JavaScript**   | Interactivity, API calls, client-side state        |
| **HTML / Jinja** | Page structure and templating                      |
| **CSS**          | Styling, responsive layouts                        |
| **Dockerfile**   | Runtime environment definition                     |
| **YAML**         | Docker Compose configuration                       |

The point is to practice **cross-language integration** (serialization, API contracts, error handling spanning front and back) rather than staying confined to a single ecosystem.

### Learning to collaborate with an AI

This project was also an opportunity to **experiment with pair-programming with a generative AI** (see [Collaboration with AI](#-collaboration-with-ai)). The goal is not to delegate but to learn how to formulate problems, review AI-generated code, spot the bugs the AI introduces, and make informed architectural choices.

## ✨ Features

- 🗺️ Interactive map (OpenStreetMap via Leaflet)
- 📍 Site placement using DMS coordinates (`47°50'44.56''N`) or decimal
- 🔗 Automatic link generation using one of 3 algorithms
- ✋ Manual link creation by simply clicking 2 sites
- ⚙️ Per-site constraints: min and max number of links
- 📏 Configurable maximum distance
- ❌ Individual link exclusion / re-enable / deletion
- 🔵 Coverage circles around sites (configurable radius)
- 📥 CSV and GeoJSON import
- 📤 CSV, GeoJSON (QGIS / ArcGIS compatible) and standalone HTML export
- 🔄 Full application reset
- ⚠️ **55 site** maximum limit (configurable in `app/app.py`)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          Browser (Frontend)             │
│  ┌───────────────────────────────────┐  │
│  │  HTML + CSS + Leaflet             │  │
│  │  api.js  →  map.js  →  ui.js      │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │  HTTP / JSON (REST)
┌─────────────────▼───────────────────────┐
│         Flask Server (Backend)          │
│  ┌───────────────────────────────────┐  │
│  │  app.py        (REST routes)      │  │
│  │  services/                        │  │
│  │   ├─ convert.py   (DMS, geodesic) │  │
│  │   ├─ compute.py   (distances,     │  │
│  │   │                adjacency)     │  │
│  │   └─ storage.py   (CSV / GeoJSON) │  │
│  │  algorithms/                      │  │
│  │   ├─ mst_aug.py   (MST + aug.)    │  │
│  │   ├─ greedy.py    (greedy)        │  │
│  │   └─ kconnect.py  (k-connectivity)│  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

Application state is kept **in memory on the server side** — intentionally, to keep the project simple. For multi-user or persistent usage, a database layer would be needed.

## 🧮 Implemented algorithms

### 1. MST + Augmentation (`mst_aug`)

First builds a **Minimum Spanning Tree** via NetworkX, guaranteeing connectivity at minimum total cost. Then adds extra edges to satisfy the `min_links` constraint of each site.

- ✅ Optimal for minimizing total link length
- ✅ Guarantees the graph is connected
- ⚠️ Vulnerable to single-node failure (degree-1 nodes common)

### 2. Greedy (`greedy`)

**Greedy** approach: sorts edges by increasing distance and adds them one by one provided they respect degree constraints and don't introduce a forbidden parent-child relationship.

- ✅ Fast and intuitive
- ✅ Good for simple cases
- ⚠️ No global optimality guarantee

### 3. K-Connectivity Approximation (`kconnect`)

Targets **node k-connectivity** (the graph stays connected even after removing `k-1` nodes). Starts from an MST and progressively augments connectivity, aiming for `k=3` when possible.

- ✅ More robust network (fault tolerance)
- ⚠️ More expensive in number of edges
- ⚠️ `node_connectivity` is quadratic on large graphs

## 🚀 Installation and launch

### Prerequisites

- **Either** Docker + Docker Compose (recommended)
- **Or** Python 3.11+ with pip

### Option 1 — Docker (recommended)

```bash
git clone https://github.com/<your-username>/geo-link-site.git
cd geo-link-site
docker compose up --build
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

To stop:

```bash
docker compose down
```

### Option 2 — Local Python install

```bash
git clone https://github.com/<your-username>/geo-link-site.git
cd geo-link-site

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Launch the application
export FLASK_APP=app.app           # Linux / macOS
# set FLASK_APP=app.app            # Windows cmd
# $env:FLASK_APP="app.app"         # Windows PowerShell

flask run --host=0.0.0.0 --port=5000
```

Then open [http://localhost:5000](http://localhost:5000).

## 🕹️ Usage

### Add a site

1. Click **"+ Ajouter un site"** in the left panel.
2. Fill in a unique identifier, the DMS coordinates and the `min_links` / `max_links` constraints.
3. The site appears on the map.

### Generate automatic links

1. Pick an **algorithm** (MST+Aug, Greedy or K-Connect).
2. Optional: set a **maximum distance** in km.
3. Click **"Générer liaisons"**.

### Create a manual link

1. Enable **"Créer liaison manuelle"** mode.
2. Click on two sites in sequence.
3. Confirm in the dialog that appears.

Manual links display in **blue**, automatic ones in **black**, excluded ones in **dashed red**.

### Exclude / delete a link

Click on a link on the map to open its details dialog, then **Exclure** (reversible) or **Supprimer définitivement** (permanent).

### Import / Export

- **CSV**: combined sites + links format (readable in Excel / LibreOffice)
- **GeoJSON**: compatible with QGIS, ArcGIS and all modern GIS tools
- **HTML**: standalone interactive map usable offline

> Note: the UI itself is currently in French. Internationalization (i18n) is listed in the roadmap.

## 📁 Project structure

```
geo-link-site/
├── app/
│   ├── __init__.py
│   ├── app.py                    # Flask application and REST routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── convert.py            # DMS / WGS84 conversions and distances
│   │   ├── compute.py            # Graph computations
│   │   └── storage.py            # Import/Export CSV, GeoJSON, HTML
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── mst_aug.py            # MST + Augmentation
│   │   ├── greedy.py             # Greedy under constraints
│   │   └── kconnect.py           # K-Connectivity approximation
│   ├── templates/
│   │   └── index.html            # Main page (Jinja2)
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── api.js            # HTTP client to backend
│           ├── map.js            # Leaflet map management
│           └── ui.js             # UI logic
├── docs/                         # (reserved for future documentation)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## 📄 Data formats

### Combined CSV

```csv
type,id,lat_dms,lng_dms,lat,lng,min_links,max_links,site_a,site_b,distance_km,status,link_type
site,A,47°50'44.56''N,2°20'30.00''E,47.8457,2.3417,1,3,,,,,,
site,B,48°51'24.00''N,2°21'07.00''E,48.8567,2.3522,1,3,,,,,,
link,edge_a1b2,,,,,,,A,B,112.347,active,auto
```

### GeoJSON (full export)

Compatible with **QGIS**, **ArcGIS**, **Leaflet** and any GIS tool following [RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946).

Sites are stored as `Point` features, links as `LineString` features. Metadata (parameters, exclusions, statistics) live in the root-level `properties`.

## 🤖 Collaboration with AI

This project was developed in **collaboration with a generative AI** (LLM-style assistant). This approach allowed:

- **Faster scaffolding** (Flask boilerplate, Docker configuration, file structure).
- **Faster algorithm exploration**, by having the AI generate variants that I then compared, debugged and adapted.
- **Learning through code review**: reading and understanding AI-generated code is a great exercise to spot anti-patterns, subtle bugs and questionable choices.
- **Practicing prompting**: clearly formulating a technical need is itself a transferable skill.

⚠️ **Important**: the AI was not used as an oracle. Every piece of generated code was **reviewed, tested and often rewritten** by hand. The AI is a learning and productivity tool here, not a substitute for understanding the code you publish.

This transparency is part of the educational stance of the project: showing that you can leverage AI while keeping ownership of your code.

## 🤝 Contributing

Contributions are welcome! To propose an improvement:

1. Fork the project
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add ...'`)
4. Push the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

Ideas to explore:
- Data persistence (SQLite, PostgreSQL / PostGIS)
- Support for more than 55 sites
- Unit tests (pytest)
- CI/CD (GitHub Actions)
- UI internationalization (i18n) FR / EN
- Additional algorithm (Steiner tree, for instance)

## 📜 License

This project is distributed under the **MIT** License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

## 🎓 Projet d'apprentissage avec IA / AI-assisted learning project

**FR —** Ce dépôt est avant tout un **projet d'apprentissage réalisé avec l'aide d'une IA générative**.
Il n'a pas vocation à être un produit fini ou prêt pour la production : son but est d'explorer plusieurs domaines techniques, des algorithmes connus de réseau et plusieurs langages de programmation, tout en expérimentant la collaboration humain-IA dans un workflow de développement.

**EN —** This repository is first and foremost a **learning project built with the help of a generative AI**.
It is not meant to be a finished or production-ready product: its purpose is to explore several technical domains, well-known network algorithms and multiple programming languages, while experimenting with human-AI collaboration in a development workflow.

</div>
