# Security Policy

*[Français ci-dessous ⬇️](#politique-de-sécurité)*

## Supported versions

MyAppsLibrary is pre-1.0 and does not yet maintain parallel release
branches. Security fixes target the latest commit on `main`; there is
currently no long-term-support version.

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| older tagged releases | ❌ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, report it privately using one of these channels:

1. **Preferred**: [GitHub Security Advisories](https://github.com/rodolphe37/my-apps-library/security/advisories/new) for this repository (private by default, and lets us collaborate on a fix before disclosure).
2. Alternatively, a private message to the maintainer, [**@rodolphe37**](https://github.com/rodolphe37), via GitHub or the email listed on that profile.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal repro is ideal)
- The affected version/commit, OS, and Python version
- Any suggested mitigation, if you have one

## What to expect

- **Acknowledgement**: within a few days of the report.
- **Assessment & fix**: timeline depends on severity and complexity; we'll keep you updated.
- **Disclosure**: coordinated with you once a fix is available — you'll be credited unless you prefer otherwise.

## Scope and context

MyAppsLibrary is a local desktop application:

- It stores only local folder references and app settings, in a per-user app-data directory (via `platformdirs`) — no server, no accounts, no telemetry.
- The core app makes **no network calls** on its own; the one exception is the user-triggered **"Browse Marketplace…"** action, which opens a URL in the system's default browser.
- **Plugins run with full application privileges and are not sandboxed** — this is documented, known behavior (see the [README](README.md#the-plugin-system) and [Roadmap](README.md#roadmap)), not something to report as a new finding. Only install plugins from sources you trust. Genuine sandbox-escape or privilege-escalation issues *within* the plugin API contract itself are still worth reporting.

Out of scope: vulnerabilities that require an attacker to already have arbitrary code execution on the user's machine, and social-engineering attacks against users to get them to install a malicious plugin.

---

# Politique de sécurité

*[English above ⬆️](#security-policy)*

## Versions supportées

MyAppsLibrary est en pré-version 1.0 et ne maintient pas encore de branches
de version parallèles. Les correctifs de sécurité ciblent le dernier commit
sur `main` ; il n'existe pour l'instant pas de version à support long terme.

| Version | Supportée |
|---|---|
| `main` (dernière) | ✅ |
| anciennes versions taguées | ❌ |

## Signaler une vulnérabilité

**Merci de ne pas ouvrir d'issue GitHub publique pour une vulnérabilité de sécurité.**

Signalez-la plutôt en privé via l'un de ces canaux :

1. **Préféré** : [GitHub Security Advisories](https://github.com/rodolphe37/my-apps-library/security/advisories/new) pour ce dépôt (privé par défaut, et permet de collaborer sur un correctif avant toute divulgation).
2. Alternativement, un message privé au mainteneur, [**@rodolphe37**](https://github.com/rodolphe37), via GitHub ou l'email indiqué sur ce profil.

Merci d'inclure :

- Une description de la vulnérabilité et de son impact potentiel
- Les étapes de reproduction (un cas minimal est idéal)
- La version/commit affecté, l'OS et la version de Python
- Une piste de correction, si vous en avez une

## À quoi s'attendre

- **Accusé de réception** : sous quelques jours après le signalement.
- **Évaluation & correctif** : le délai dépend de la gravité et de la complexité ; nous vous tiendrons informé.
- **Divulgation** : coordonnée avec vous une fois un correctif disponible — vous serez crédité, sauf préférence contraire de votre part.

## Périmètre et contexte

MyAppsLibrary est une application de bureau locale :

- Elle ne stocke que des références de dossiers locales et des paramètres d'application, dans un répertoire de données par utilisateur (via `platformdirs`) — pas de serveur, pas de comptes, pas de télémétrie.
- Le cœur de l'application n'effectue **aucun appel réseau** de sa propre initiative ; la seule exception est l'action **« Parcourir la Marketplace… »**, déclenchée par l'utilisateur, qui ouvre une URL dans le navigateur par défaut du système.
- **Les plugins tournent avec tous les privilèges de l'application et ne sont pas isolés (sandbox)** — c'est un comportement documenté et connu (voir le [README](README.fr.md#le-système-de-plugins) et la [feuille de route](README.fr.md#feuille-de-route)), pas un problème à signaler comme une nouvelle découverte. N'installez que des plugins provenant de sources de confiance. De vrais problèmes d'évasion de sandbox ou d'élévation de privilèges *au sein même* du contrat de l'API plugin restent en revanche pertinents à signaler.

Hors périmètre : les vulnérabilités qui nécessitent qu'un attaquant dispose déjà d'une exécution de code arbitraire sur la machine de l'utilisateur, et les attaques d'ingénierie sociale visant à faire installer un plugin malveillant par un utilisateur.
