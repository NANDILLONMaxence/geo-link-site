# Changelog

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnement [SemVer](https://semver.org/lang/fr/).

## [2.1.0] - 2026-10-29

### Sécurité
- Export HTML : un nom de site contenant `</script>` ne peut plus injecter de code (XSS) ; les noms sont échappés dans les infobulles et popups.
- Interface : les noms de sites et de liaisons venant d'un fichier importé sont échappés avant affichage (XSS stocké).
- Leaflet chargé avec contrôle d'intégrité (SRI).
- Les erreurs internes ne renvoient plus leur détail au client (journalisées côté serveur).
- En-têtes `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- Docker : utilisateur non privilégié, serveur gunicorn, débogueur Flask désactivé par défaut (il permettait l'exécution de code à distance) ; mode debug déplacé dans `docker-compose.dev.yml`, publié sur `127.0.0.1` uniquement.

### Corrigé
- `/export_csv` renvoyait une erreur 500 dès qu'un site existait.
- Import CSV/JSON : une liaison manuelle sans identifiant `manual_N` provoquait une erreur 500 ; fichier avec BOM (Excel) accepté ; fichier non UTF-8 → 400.
- Import JSON : structure validée (id, coordonnées, contraintes, liaisons) avant chargement.
- Entrées invalides (`min_links`, `max_links`, `radius_km`, `distance_max_km`, corps non JSON) → 400 au lieu de 500.
- `edit_site` ne modifie plus partiellement le site quand une valeur est invalide.
- `delete_link` retire correctement les exclusions du lien supprimé ; lien inconnu → 404.
- Caractères corrompus (`âœ“`) dans les boutons de l'interface.

### Modifié
- Python 3.12 minimum (pyproj 3.8 a abandonné 3.11) ; CI testée sur 3.12 → 3.15 ; image Docker sur `python:3.15-slim-trixie`.
- Dépendances inutilisées retirées : `pandas`, `geopy`, `geojson`.
- CI : audit des dépendances (pip-audit), analyse statique (bandit, CodeQL), revue des dépendances sur PR, build + test de fumée Docker, seuil de couverture 80 %.
- L'auto-merge Dependabot attend désormais que la CI soit verte (job requis `CI OK`).
- Release : tests et audit avant publication, vérification tag = `VERSION`, image avec SBOM et provenance ; actions tierces épinglées par SHA (alerte CodeQL `actions/unpinned-tag`).
- 37 tests ajoutés (139 au total), couverture 63 % → 86 %.

## [2.0.0] - 2026-05-11

- Première version publiée.
