"""Point d'extension Pronote.

La connexion réelle sera activée quand l'URL et le mode d'authentification de
l'établissement seront connus. Les secrets restent dans les variables
d'environnement et ne sont jamais écrits dans la base ni dans Git.
"""

from .settings import settings


def pronote_is_configured() -> bool:
    return bool(settings.pronote_url and settings.pronote_username and settings.pronote_password)


def sync_pronote() -> dict:
    if not pronote_is_configured():
        return {"connected": False, "reason": "Configuration Pronote manquante"}
    # TODO: intégrer pronotepy après validation de l'URL ENT et du type de connexion.
    return {"connected": False, "reason": "Connecteur Pronote à configurer"}
