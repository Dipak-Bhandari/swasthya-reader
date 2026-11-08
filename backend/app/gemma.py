"""All Gemma 4 calls: report extraction, Nepali summary, chat."""
import json
import re
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMMA_MODEL
from .prompts import CHAT_SYSTEM_PROMPT, EXTRACTION_PROMPT, SUMMARY_PROMPT

API_TIMEOUT_MS = 120_000  # fail after 2 minutes instead of hanging
MAX_PARALLEL_PAGES = 4

_client = None


def client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in.")
        _client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=API_TIMEOUT_MS),
        )
    return _client


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def _generate_json(contents, retries: int = 1) -> dict:
    last_err = None
    for _ in range(retries + 1):
        resp = client().models.generate_content(
            model=GEMMA_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        try:
            return _parse_json(resp.text or "")
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
    raise ValueError(f"Model did not return valid JSON: {last_err}")


def _clean_tests(tests) -> list[dict]:
    clean = []
    for t in tests or []:
        if not isinstance(t, dict) or not t.get("name") or t.get("value") in (None, ""):
            continue
        clean.append(
            {
                "name": str(t["name"]).strip(),
                "value": str(t["value"]).strip(),
                "unit": str(t.get("unit") or "").strip(),
                "reference_range": str(t.get("reference_range") or "").strip(),
            }
        )
    return clean


def _extract_page(image: tuple[bytes, str]):
    """One vision call for one page. Returns (result_or_None, error_or_None)."""
    data, mime = image
    try:
        return _generate_json([types.Part.from_bytes(data=data, mime_type=mime), EXTRACTION_PROMPT]), None
    except Exception as e:  # one bad page must not sink the whole report
        return None, e


def extract_report(images: list[tuple[bytes, str]]) -> dict:
    """Vision step: report page images -> structured JSON of tests.

    Pages are read in parallel (one request per page), which is much faster than one big request,
    and a single unreadable page does not fail the whole report.
    """
    if len(images) == 1:
        outcomes = [_extract_page(images[0])]
    else:
        with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_PAGES, len(images))) as pool:
            outcomes = list(pool.map(_extract_page, images))

    patient = {"age": None, "sex": None}
    report_date = None
    tests: list[dict] = []
    seen = set()
    errors = []

    for result, err in outcomes:
        if err is not None:
            errors.append(err)
            continue
        p = result.get("patient") or {}
        for k in ("age", "sex"):
            if patient[k] is None and p.get(k) is not None:
                patient[k] = p[k]
        report_date = report_date or result.get("report_date")
        for t in _clean_tests(result.get("tests")):
            key = (t["name"].lower(), t["value"], t["reference_range"])
            if key not in seen:
                seen.add(key)
                tests.append(t)

    if not tests and errors:
        raise ValueError(f"Could not read any page: {errors[0]}")
    if errors:
        print(f"[gemma] WARNING: {len(errors)} of {len(images)} page(s) failed and were skipped: {errors[0]}")

    return {"patient": patient, "report_date": report_date, "tests": tests, "skipped_pages": len(errors)}


def summarize_nepali(flagged_tests: list[dict]) -> dict:
    """Text step: verified, flagged results -> Nepali summary + tips."""
    prompt = SUMMARY_PROMPT.format(results_json=json.dumps(flagged_tests, ensure_ascii=False, indent=2))
    data = _generate_json([prompt])
    tips = data.get("tips_ne") or {}
    return {
        "summary_ne": str(data.get("summary_ne", "")).strip(),
        "tips_ne": {
            "diet": list(tips.get("diet") or []),
            "lifestyle": list(tips.get("lifestyle") or []),
            "behaviour": list(tips.get("behaviour") or []),
        },
        "see_doctor_soon": bool(data.get("see_doctor_soon", False)),
    }


def chat_answer(flagged_tests: list[dict], history: list[dict], question: str) -> str:
    system = CHAT_SYSTEM_PROMPT.format(results_json=json.dumps(flagged_tests, ensure_ascii=False))
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=question)]))
    # Gemma models may not accept a separate system instruction, so prepend it to the first turn.
    contents[0] = types.Content(
        role=contents[0].role,
        parts=[types.Part.from_text(text=system + "\n\n")] + list(contents[0].parts),
    )
    resp = client().models.generate_content(
        model=GEMMA_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return (resp.text or "").strip()