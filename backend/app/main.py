import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, flagging, gemma, ingest, tts
from .config import CHAT_HISTORY_LIMIT, MAX_UPLOAD_MB, MEDIA_DIR
from .prompts import DISCLAIMER_EN, DISCLAIMER_NE

app = FastAPI(title="Swasthya Reader API", version="0.1.0")

# Open CORS for the hackathon (browser, Capacitor Android WebView at https://localhost). Tighten later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/reports")
async def create_report(file: UploadFile = File(...)):
    """Upload a lab report (image or PDF) -> extracted values, Nepali summary + tips, audio."""
    t0 = time.perf_counter()
    last = [t0]

    def lap(stage: str) -> None:
        now = time.perf_counter()
        print(f"[timing] {stage}: {now - last[0]:.1f}s (total {now - t0:.1f}s)")
        last[0] = now

    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {MAX_UPLOAD_MB} MB)")

    try:
        images = await run_in_threadpool(ingest.to_images, data, file.content_type)
    except ValueError as e:
        raise HTTPException(415, str(e))
    lap(f"render {len(images)} page image(s)")

    try:
        extracted = await run_in_threadpool(gemma.extract_report, images)
    except Exception as e:
        raise HTTPException(502, f"Could not read the report: {e}")

    lap(f"gemma extraction ({len(extracted['tests'])} tests)")
    sex = (extracted.get("patient") or {}).get("sex")
    tests = flagging.flag_all(extracted["tests"], sex)
    if not tests:
        raise HTTPException(422, "No test results found. Try a clearer photo or a different page.")

    try:
        summary = await run_in_threadpool(gemma.summarize_nepali, tests)
    except Exception as e:
        raise HTTPException(502, f"Could not write the Nepali summary: {e}")

    lap("gemma nepali summary")
    # Code decides urgency as well; the model's flag can only raise it, never lower it.
    see_doctor = flagging.needs_doctor_soon(tests) or summary["see_doctor_soon"]

    audio_url = None
    try:
        speech = tts.tts_text(summary["summary_ne"], summary["tips_ne"])
        audio_url = await run_in_threadpool(tts.synthesize, speech)
    except Exception as e:
        print(f"TTS failed: {e}")  # text still works if speech fails

    lap("text-to-speech")
    record = {
        "extracted_json": {"patient": extracted.get("patient"), "report_date": extracted.get("report_date"), "tests": tests},
        "nepali_summary": summary["summary_ne"],
        "tips_json": summary["tips_ne"],
        "see_doctor_soon": see_doctor,
        "audio_url": audio_url,
    }
    report_id = db.save_report(record)
    lap("save to database")

    return {
        "report_id": report_id,
        "tests": tests,
        "summary_ne": summary["summary_ne"],
        "tips_ne": summary["tips_ne"],
        "see_doctor_soon": see_doctor,
        "audio_url": audio_url,
        "skipped_pages": extracted.get("skipped_pages", 0),
        "disclaimer_ne": DISCLAIMER_NE,
        "disclaimer_en": DISCLAIMER_EN,
    }


@app.post("/api/reports/{report_id}/chat")
def chat(report_id: str, body: ChatRequest):
    report = db.get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    question = body.question.strip()
    if not question:
        raise HTTPException(400, "Empty question")

    history = db.get_messages(report_id, CHAT_HISTORY_LIMIT)
    tests = report["extracted_json"]["tests"]
    try:
        answer = gemma.chat_answer(tests, history, question)
    except Exception as e:
        raise HTTPException(502, f"Chat failed: {e}")

    db.add_message(report_id, "user", question)
    db.add_message(report_id, "assistant", answer)

    audio_url = None
    try:
        audio_url = tts.synthesize(answer)
    except Exception as e:
        print(f"TTS failed: {e}")

    return {"answer": answer, "audio_url": audio_url, "disclaimer_ne": DISCLAIMER_NE}