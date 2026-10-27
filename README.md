# JVM Technologies AI Platform

An independent AI chat and coding assistant starter project for JVM Technologies. It supports:
- OpenAI-compatible API providers (set your API key and base URL)
- A local Ollama model
- User registration/login with hashed passwords and JWT
- Chat history
- Admin role (first registered user becomes admin by default)
- FastAPI backend and responsive HTML/CSS/JavaScript frontend
- SQLite by default for easy local testing; PostgreSQL can be configured with `DATABASE_URL`

> This is a new, independent application. It does not access OpenAI private systems or provide paid-provider access for free. Provider API usage may incur charges.

## 1. Requirements
- Python 3.11+
- Optional: Docker + Docker Compose
- For local AI: Ollama installed and a model downloaded, e.g. `ollama pull llama3.2`
- For API AI: an API key from your chosen provider

## 2. Run locally (quick start)
From this folder:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# macOS/Linux: cp .env.example .env

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

The app defaults to the `ollama` provider at `http://localhost:11434`, model `llama3.2`.
To use it, start Ollama and run `ollama pull llama3.2`.

## 3. Configure API provider instead
Edit `.env`:
```env
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=replace_with_your_api_key
AI_MODEL=replace_with_a_model_available_to_your_account
```
Use the exact base URL and model name provided by your chosen provider. Keep API keys in `.env` on the server; never put them in frontend JavaScript or commit them to source control.

For another OpenAI-compatible provider, change `AI_BASE_URL` and `AI_MODEL` according to that provider's documentation.

## 4. PostgreSQL (optional)
The default database is SQLite and requires no database server.
To use PostgreSQL, set `DATABASE_URL` in `.env`, for example:
`postgresql+psycopg://jvm_user:change_this_password@localhost:5432/jvm_ai`

Then install/start PostgreSQL and create the database/user. `docker-compose.yml` includes a PostgreSQL service for local development:
```bash
docker compose up --build
```
The Compose service uses the `.env` file. Change the example password before using it beyond local development.

## 5. Admin access
The first user registered becomes an admin. Subsequent registrations are regular users.
For a real deployment, set a strong `JWT_SECRET`, configure HTTPS, and review registration/admin policies before going live.

## 6. Deployment notes
This project requires a Python backend, so a static-only Netlify deployment will not run the entire app by itself. Deploy the FastAPI app to a Python-capable host or Docker host, and point your domain/subdomain to it. A managed PostgreSQL database is recommended for production.
Set environment variables in your host's dashboard rather than uploading `.env`.

## 7. Included endpoints
- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/chats`
- `POST /api/chats`
- `GET /api/chats/{chat_id}`
- `DELETE /api/chats/{chat_id}`
- `POST /api/chat`

## Security checklist before public launch
- Replace `JWT_SECRET` with a long random secret.
- Use HTTPS.
- Use a managed database and backups.
- Set CORS to your actual frontend origin if hosting frontend separately.
- Add rate limiting, monitoring, email verification and password reset before public production use.
- Do not expose local Ollama or database ports publicly.
