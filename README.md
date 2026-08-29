# JARVIS Scolaire

JARVIS est ton espace personnel pour regrouper ton emploi du temps, tes devoirs, tes rappels et bientôt ton tuteur IA. L’objectif est d’avoir un seul endroit simple, accessible depuis ton téléphone et ton ordinateur.

## Où en est le projet ?

### Déjà disponible

- Dashboard avec briefing du jour
- Date et calendrier dynamiques
- Pages séparées : accueil, calendrier, cours/devoirs, objectifs, profil
- Checklist du soir synchronisée
- Rappels enregistrés dans la base de données
- Tuteur IA connecté à Gemini
- Interface responsive avec animations et icônes
- Déploiement automatique depuis GitHub vers Vercel
- Base de données Supabase avec RLS activé

### En préparation

- Connexion réelle à Pronote via l’ENT Net’O Centre / EduConnect
- Import des cours, devoirs et notes Pronote
- Connexion Google Calendar
- Dépôt de cours et documents
- Fiches de révision, quiz et explications par l’IA
- Actions contrôlées par l’IA : créer un rappel, ajouter un devoir ou organiser une séance

## Architecture

```text
frontend React/Vite
        │
        ▼
Vercel Services
  ├── web : interface
  └── api : FastAPI
        │
        ├── Supabase : données
        ├── Gemini API : cerveau principal de JARVIS
        └── Pronote : synchronisation à venir
```

Le frontend ne contient jamais les clés secrètes. Les appels IA et les futures connexions Pronote passent par le backend FastAPI.

## Utiliser JARVIS en ligne

Le projet est relié à GitHub et Vercel.

1. Modifier le code sur GitHub.
2. Faire un commit sur la branche `main`.
3. Vercel lance automatiquement un nouveau déploiement.
4. Ouvrir l’URL Vercel et faire `Ctrl + F5` si l’ancien affichage reste en cache.

Le dossier `frontend` contient l’interface. Le dossier `backend` contient l’API.

## Variables d’environnement

À configurer dans Vercel, dans **Settings → Environment Variables** :

| Variable | Utilité |
|---|---|
| `DATABASE_URL` | Connexion PostgreSQL/Supabase |
| `GEMINI_API_KEY` | Clé secrète du cerveau Gemini |

Pour les futures connexions Pronote, les identifiants ne doivent pas être commités dans Git. Ils seront stockés de façon sécurisée, après validation du fonctionnement de l’ENT :

| Variable prévue | Utilité |
|---|---|
| `PRONOTE_URL` | URL directe de l’espace Pronote |
| `PRONOTE_ENT` | Type d’ENT, ici Net’O Centre / EduConnect |

Ne jamais mettre une clé API, un mot de passe ou un token dans `main.jsx`, `style.css`, un fichier public ou un commit GitHub.

## Lancer le projet sur l’ordinateur

### Backend FastAPI

Depuis la racine du projet :

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API locale : http://127.0.0.1:8000  
Documentation : http://127.0.0.1:8000/docs

### Frontend

Dans un autre terminal :

```powershell
cd frontend
npm install
npm run dev
```

Si le frontend doit parler à l’API locale, utiliser :

```text
VITE_API_URL=http://127.0.0.1:8000
```

## Connexion Pronote : plan prévu

L’établissement utilise un portail Net’O Centre avec EduConnect. L’URL directe Pronote à utiliser est :

```text
https://0280036m.index-education.net/pronote/eleve.html
```

Il ne faut pas conserver le paramètre `?identifiant=...` : il peut être temporaire.

La connexion sera construite en plusieurs étapes :

1. Vérifier que le lycée a publié l’espace Pronote.
2. Tester la connexion ENT avec l’adaptateur `ac_orleans_tours`.
3. Récupérer les cours, devoirs et notes.
4. Convertir ces données au format JARVIS.
5. Enregistrer les données dans Supabase.
6. Ajouter un bouton de synchronisation et une synchronisation automatique.

La bibliothèque utilisée sera testée avec prudence car l’API Pronote n’est pas une API publique officielle pour les comptes élèves. Si l’établissement modifie son accès, il faudra adapter le connecteur.

## Tuteur IA

Le cerveau principal utilise Gemini 2.5 Flash via l’API Gemini. Le frontend ne parle jamais directement à Google : le backend FastAPI protège la clé et ajoute le contexte quotidien autorisé.

Pour créer la clé :

1. Ouvrir [Google AI Studio](https://aistudio.google.com/apikey).
2. Cliquer sur **Create API key** et choisir le projet Google Cloud `JARVIS Scolaire`.
3. Dans Vercel, ajouter la variable secrète `GEMINI_API_KEY` pour **Production**.
4. Redéployer le projet.

Le frontend appelle :

Le frontend appelle :

```text
POST /api/ai/chat
```

Le backend envoie uniquement les messages nécessaires au modèle. Plus tard, l’IA pourra recevoir le contexte autorisé de l’élève : devoirs, cours du jour et documents sélectionnés.

Les actions de l’IA seront limitées et demanderont confirmation avant toute modification :

- créer un rappel ;
- ajouter un devoir ;
- modifier une tâche ;
- préparer une séance de révision ;
- synchroniser un calendrier.

## Ajouter une nouvelle fonctionnalité

Pour chaque fonctionnalité :

1. Ajouter ou modifier la route FastAPI.
2. Ajouter les données nécessaires dans Supabase.
3. Ajouter la vue correspondante dans `frontend/src/main.jsx`.
4. Ajouter le style dans `frontend/src/style.css` et `frontend/public/style.css`.
5. Tester localement.
6. Commit sur `main`.
7. Vérifier le déploiement Vercel.

## Dépannage rapide

### L’ancienne version s’affiche

Attendre la fin du déploiement, puis faire `Ctrl + F5). Vérifier que Vercel déploie bien la branche `main`.

### L’IA ne répond pas

Vérifier que `GEMINI_API_KEY` est bien présente dans Vercel, environnement **Production**, puis redéployer.

### L’API ne répond pas

Vérifier les logs Vercel et l’URL `/health`.

### Pronote affiche “site indisponible”

Ce message vient de l’établissement : l’espace Pronote n’est pas encore publié. Ce n’est pas une erreur de JARVIS.

## Règle importante

JARVIS est un projet personnel. Les mots de passe Pronote, EduConnect, Supabase et les clés IA restent privés et ne doivent jamais apparaître dans une capture d’écran, un message ou GitHub.


## Paramètres personnels du briefing

Le briefing est préparé pour :

- météo réelle : La Loupe (Open-Meteo, sans clé) ;
- trajet habituel : gare de La Loupe → gare de Nogent-le-Rotrou ;
- horaire cible : autour de 07:14.

Ces préférences sont exposées par `GET /api/preferences`. La météo réelle est disponible via `GET /api/weather`. Les horaires SNCF en temps réel nécessiteront ensuite une clé API SNCF et seront ajoutés derrière le backend.

## Préparation Gmail

La connexion Gmail se fera avec OAuth 2.0, jamais avec le mot de passe Gmail. L’application demandera d’abord uniquement la lecture des messages autorisés, avec un filtre possible sur les mails scolaires. Les variables prévues sont `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` et `GOOGLE_REDIRECT_URI`. Elles restent dans les variables secrètes Vercel.
