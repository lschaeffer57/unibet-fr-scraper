# unibet-fr-scraper

Scrape **prématch** [Unibet.fr](https://www.unibet.fr) (tennis, foot, basket, hockey) → un JSON type `output.json` (`generated_at`, `sports`, `competitions`, `markets`, `props`, `url` par match).

## En local

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python unibet_all_json.py              # écrit output.json à la racine
python unibet_all_json.py --pretty   # JSON indenté
```

## Railway

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub** → choisir **ce repo**.
2. Pas de *root directory* à configurer : le `Dockerfile` est à la racine.
3. Variables optionnelles :
   - `OUTPUT_PATH` (défaut `/app/output.json`)
   - `SCRAPE_INTERVAL_SECONDS` : `0` = un run puis arrêt ; `3600` = scrape toutes les heures en boucle.
   - **`HTTPS_PROXY` / `HTTP_PROXY`** : si tu vois des **HTTP 403** sur `zones/v3/sportnode/markets.json`, c’est souvent le **WAF / anti-bot** qui bloque les IP de datacenter (Railway, AWS, etc.). Le client HTTP utilise `trust_env=True` : défini un proxy **résidentiel ou mobile** (FR de préférence), par ex. `HTTPS_PROXY=http://user:pass@host:port`.

Avant la première requête API, une visite de `https://www.unibet.fr/` récupère les cookies usuel du site ; sans proxy, le blocage peut malgré tout persister depuis le cloud.

Le fichier JSON est produit **dans le conteneur** ; pour l’exploiter ailleurs, ajoute upload (S3, webhook, etc.) selon ton flux.

## Licence / usage

Usage responsable, respect des CGU Unibet et du cadre légal du pays.
