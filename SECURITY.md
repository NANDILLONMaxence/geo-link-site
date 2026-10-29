# Politique de sécurité / Security policy

## Versions supportées

Seule la dernière version publiée reçoit des correctifs de sécurité.

## Signaler une vulnérabilité

Merci de **ne pas ouvrir d'issue publique**. Utilise le signalement privé de GitHub :
onglet **Security → Report a vulnerability** du dépôt.

Please **do not open a public issue**. Use GitHub private vulnerability reporting:
**Security → Report a vulnerability**.

## Mesures automatiques

- Dependabot : mises à jour hebdomadaires (pip, GitHub Actions, image Docker) et alertes de sécurité.
- CI : `pip-audit` (CVE des dépendances), `bandit` (analyse statique Python), CodeQL (Python, JavaScript, workflows), dependency review sur chaque PR.

## Avertissement

L'application ne gère ni authentification ni multi-utilisateur : l'état est en mémoire et partagé.
Ne l'expose pas sur Internet sans reverse proxy authentifiant.
