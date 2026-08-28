# JARVIS Scolaire & Quotidien

Un deuxième cerveau personnel pour l'emploi du temps, les devoirs, les rappels et le sport.

## Démarrage local

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API disponible sur http://127.0.0.1:8000 et documentation sur http://127.0.0.1:8000/docs.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Configuration

Copier `backend/.env.example` vers `backend/.env`. Pour la première version, l'application fonctionne sans Pronote : elle contient des données de démonstration rechargeables depuis le tableau de bord.

## Déploiement gratuit

Le backend peut être déployé comme Web Service Render avec la commande `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Pour une vraie mise en ligne, remplacer SQLite par PostgreSQL via `DATABASE_URL` avant le déploiement.

Les identifiants Pronote ne doivent jamais être commités dans Git.

