# 🌸 Bloom Roadmaps

Streamlit frontend · FastAPI backend · PostgreSQL (SQLite for local dev).
Sign-in is Google OIDC via Streamlit's built-in `st.login()`, so there are no passwords to store
and the login survives page refreshes (Streamlit keeps an identity cookie for ~30 days).

## How login works
1. `st.login()` sends the user to Google; Streamlit verifies the result and sets its identity cookie.
2. On each new browser session the Streamlit server calls `POST /auth/sso` with the verified email and a
   shared `SERVICE_KEY`. The API creates the user on first visit and returns a 1-day API token.
3. If that token expires, the app silently asks for a new one while the Google session is still valid.

## One-time Google setup
1. Google Cloud Console → APIs & Services → Credentials → Create OAuth client ID → Web application.
2. Authorized redirect URI: `http://localhost:8501/oauth2callback` (add your deployed URL later).
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in client id/secret,
   `cookie_secret`, and `SERVICE_KEY`.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill JWT_SECRET and SERVICE_KEY (same SERVICE_KEY as secrets.toml)
export $(grep -v '^#' .env | xargs)
python -m backend.seed
uvicorn backend.main:app --reload      # API on :8000
streamlit run frontend/app.py          # UI on :8501
```
If you ran an earlier version, delete `bloom.db` once (the users table no longer has passwords).

## Deploy (free tiers)
Neon → `DATABASE_URL`. Render/Fly.io → API (`uvicorn backend.main:app --host 0.0.0.0`) with `DATABASE_URL`,
`JWT_SECRET`, `SERVICE_KEY`. Streamlit Community Cloud → paste secrets.toml into app settings, with
`redirect_uri = https://<your-app>.streamlit.app/oauth2callback` (also add it in Google Console)
and `API_URL` pointing at the deployed API.

## Add a roadmap
Copy `roadmaps/devops.yaml`, edit, run `python -m backend.seed`.

## Next steps
Stable topic IDs on re-seed, prerequisites between topics, more roadmaps, rate-limiting `/auth/sso`.
