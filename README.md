# Swasthya Reader (स्वास्थ्य रिडर)

Hacktoberfest Hack Day Kathmandu 2026 · **Track 01: Best Use of Gemma 4**

Patients often hold a lab report full of English medical jargon they cannot read.
Swasthya Reader lets them upload a photo or PDF of the report and get:

1. The values read from the report by **Gemma 4 (vision)**
2. A **simple Nepali explanation** with general diet, lifestyle and behaviour tips
3. The explanation **spoken aloud in Nepali**
4. A chat box for follow-up questions about their own report

> **Medical disclaimer:** This is an assistive tool that gives general health information only.
> It does not diagnose, prescribe medicines or replace a doctor. Always show your report to a doctor.

## How it works

```
photo / PDF
   │  (PDF pages rendered to images with PyMuPDF)
   ▼
Gemma 4 vision ──► JSON: test, value, unit, reference range
   ▼
Python flagging  ──► low / normal / high   (decided by code, never by the model)
   ▼
Gemma 4 text    ──► Nepali summary + diet / lifestyle / behaviour tips
   ▼
Nepali TTS      ──► mp3 audio
   ▼
React UI (browser + Capacitor Android app) + chat using report JSON and recent messages
```

Gemma 4 is central: without its vision step nothing can be read, and without its Nepali writing
there is no explanation.

## Models and third-party pieces

| Piece | Used for | License |
|---|---|---|
| Gemma 4 via Gemini API (`GEMMA_MODEL`) | Report reading, Nepali summary, chat | Gemma terms of use. See the model card |
| PyMuPDF | Rendering PDF pages to images | AGPL-3.0 / commercial |
| edge-tts / gTTS | Nepali text-to-speech | LGPL-3.0 / MIT |
| FastAPI, React, Vite, Supabase | App stack | MIT / Apache-2.0 |

The license on this code (MIT) does not change the terms of the model weights or the libraries above.

## Run it locally

Prerequisites: Python 3.10+, Node 18+, a Gemini API key from Google AI Studio.

```bash
# 1. Secrets
cp .env.example .env            # then fill in GEMINI_API_KEY
cp frontend/.env.example frontend/.env

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

**Check the Gemma 4 model ID** in AI Studio / the Gemini API docs and set `GEMMA_MODEL` in `.env`.
Supabase is optional: without `SUPABASE_URL` the backend keeps data in memory.
To use it, run `supabase/schema.sql` in the Supabase SQL editor and fill in the two Supabase variables.
If report uploads return `Could not find the table 'public.reports' in the schema cache`, run that SQL
in the Supabase project configured by `SUPABASE_URL`; the script asks PostgREST to reload its schema.
This is a database setup error, not a CORS error. The API's development CORS policy already allows
browser origins; check the backend response/traceback for the underlying failure.

## Android app (Capacitor), do this last

The React app is mobile-first, so the browser version on a phone already works for the demo.

```bash
cd frontend
npm i @capacitor/core @capacitor/cli @capacitor/android
npx cap add android
npm run cap:sync && npm run cap:open     # opens Android Studio, then Run
```

The app cannot call `localhost`. Set `VITE_API_URL` to a public **https** backend URL
(Render, Railway or an ngrok tunnel), rebuild, and sync again.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/reports` | Multipart upload `file` (png, jpg, webp, pdf). Returns tests, Nepali summary, tips, audio URL |
| POST | `/api/reports/{id}/chat` | Body `{"question": "..."}`. Returns a Nepali answer |
| GET | `/health` | Liveness check |

## Safety rules built in

- Abnormal flags come from comparing values with the report's printed range in code.
- The model is told never to name medicines or doses and never to diagnose.
- Marked deviations trigger a "see a doctor soon" banner. The model can raise that flag but never lower it.
- Use **synthetic or anonymized reports only**. No real patient data.
- API keys live only in the backend `.env`, which is git-ignored.

## Team roles

| Person | Owns |
|---|---|
| 1 | Extraction prompt and JSON schema (`backend/app/prompts.py`, `gemma.py`) |
| 2 | Nepali summary quality and speech (`prompts.py`, `tts.py`) |
| 3 | FastAPI, flagging and Supabase (`main.py`, `flagging.py`, `db.py`) |
| 4 | React UI, README, LICENSE, demo script (`frontend/`) |

## License

MIT. See [LICENSE](LICENSE).
