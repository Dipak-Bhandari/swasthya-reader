<div align="center">

<a href="https://https://www.mlh.io"><img src="public/asset/mlh-logo-color.svg" alt="Major League Hacking" height="70"></a>
&nbsp;&nbsp;&nbsp;
<a href="https://hacktoberfest.com/"><img src="public/asset/hacktober.svg" alt="Hacktoerfest" height="70"></a>
&nbsp;&nbsp;&nbsp;
<a href= "https://sunway.edu.np"> <img src="public/asset/download.png" alt="Sunway College Kathmandu" height="100"></a>
# Swasthya Reader (स्वास्थ्य रिडर)

**Hacktoberfest Hack Day Kathmandu 2026 · Track 01: Best Use of Gemma 4**

Organized by **Major League Hacking (MLH)** · Hosted at **Sunway College, Kathmandu**

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-DE5FE9?logo=uv&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?logo=nodedotjs&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?logo=supabase&logoColor=white)
![Capacitor](https://img.shields.io/badge/Capacitor-119EFF?logo=capacitor&logoColor=white)
![Android](https://img.shields.io/badge/Android-3DDC84?logo=android&logoColor=white)
![Gemma 4](https://img.shields.io/badge/Gemma_4-4285F4?logo=googlegemini&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

---

Patients often hold a lab report full of English medical jargon they cannot read.
Swasthya Reader lets them upload a photo or PDF of the report and get:

1. The values read from the report by **Gemma 4 (vision)**
2. A **simple Nepali explanation** with general diet, lifestyle and behaviour tips
3. The explanation **spoken aloud in Nepali**
4. A chat box for follow-up questions about their own report

> **Medical disclaimer:** This is an assistive tool that gives general health information only.
> It does not diagnose, prescribe medicines or replace a doctor. Always show your report to a doctor.

## About the event

Swasthya Reader was built at **Hacktoberfest Hack Day Kathmandu 2026**, run by
[Major League Hacking](https://mlh.io) at **Sunway College, Kathmandu**, as part of
[Hacktoberfest](https://hacktoberfest.com). It was entered in **Track 01: Best Use of Gemma 4**.

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

## Tech stack

| Layer | Technology |
|---|---|
| AI model | Gemma 4 via the Gemini API (Google AI Studio) |
| Backend language | Python 3.10+ |
| Python package and environment manager | [uv](https://docs.astral.sh/uv/) |
| Backend framework | FastAPI, served with Uvicorn |
| PDF handling | PyMuPDF |
| Nepali text-to-speech | edge-tts / gTTS |
| Frontend | React + Vite (Node 18+) |
| Mobile | Capacitor (Android, built with Android Studio) |
| Database | Supabase (Postgres + PostgREST), optional |
| Config | `.env` files for secrets |

## Models and third-party pieces

| Piece | Used for | License |
|---|---|---|
| Gemma 4 via Gemini API (`GEMMA_MODEL`) | Report reading, Nepali summary, chat | Gemma terms of use. See the model card |
| PyMuPDF | Rendering PDF pages to images | AGPL-3.0 / commercial |
| edge-tts / gTTS | Nepali text-to-speech | LGPL-3.0 / MIT |
| FastAPI, React, Vite, Supabase | App stack | MIT / Apache-2.0 |
| uv | Python package and environment management | MIT / Apache-2.0 |
| Capacitor | Android packaging | MIT |

The license on this code (MIT) does not change the terms of the model weights or the libraries above.

## Run it locally

Prerequisites: Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node 18+, a Gemini API key from Google AI Studio.

```bash
# 1. Secrets
cp .env.example .env            # then fill in GEMINI_API_KEY
cp frontend/.env.example frontend/.env

# 2. Backend
cd backend
uv venv                                  # creates .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 8000

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

## Acknowledgements

Thanks to **Major League Hacking**, the **Hacktoberfest** community, and **Sunway College, Kathmandu**
for organizing and hosting Hack Day Kathmandu 2026.

Hacktoberfest and MLH names and logos belong to their respective owners and are used here only to
credit the event.

## License

MIT. See [LICENSE](LICENSE).
