# Swasthya Reader — Agentic Replication & Incremental Build Plan

> **Purpose:** Rebuild the uploaded Swasthya Reader project with coding agents while understanding every change, keeping commits small, and maintaining a runnable application after each milestone.
>
> **Project type:** Hackathon prototype — medical lab-report image → structured extraction → deterministic range checks → plain Nepali explanations → audio playback.
>
> **Important:** This is a decision-support/demo tool, not a diagnosis system. Reference ranges vary by laboratory, age, sex, pregnancy status, and other factors. Do not present its output as medical advice or tell users to start/stop treatment. Make uncertainty visible and recommend discussing results with a qualified clinician.

---

## 1. Understand the existing project first

The uploaded archive contains a Streamlit app and a small Python skill module.

### Current pipeline

1. User uploads a JPG/PNG report or selects one of two sample reports.
2. A vision-capable model attempts to extract patient name, date, test names, values, and units into JSON.
3. `skills/swasthyalabchecker/checker.py` parses that JSON.
4. The checker compares supported test values against `reference_ranges.py`.
5. Streamlit displays high/low/normal/unverified findings.
6. Nepali text is sent to text-to-speech and played in the UI.

### Main existing files

```text
swastha-reader/
├── app.py
├── requirements.txt
├── generate_file.py
├── sample_sugar_high.png
├── sample_cbc_anemia.png
└── skills/
    └── swasthyalabchecker/
        ├── __init__.py
        ├── SKILL.md
        ├── checker.py
        └── reference_ranges.py
```

### Important cleanup before building

- **Do not commit `.env`, API keys, `.venv/`, `__pycache__/`, or machine-specific files.** The supplied ZIP appears to contain a `.env` and a virtual environment. Inspect `.env` locally without printing or sharing secret values; rotate any key that was accidentally exposed.
- Add `.gitignore` before the first source commit.
- `app.py` imports `gTTS`, but the provided `requirements.txt` lists `edge-tts` instead. Resolve this mismatch deliberately: either add `gTTS` if keeping the current implementation, or change the code to use `edge-tts`.
- `ollama` is imported by the app but is not listed in `requirements.txt`. Decide whether local Ollama support is in the hackathon MVP; if yes, document that Ollama must be installed and running separately.
- Verify the selected Gemini model identifier and API response shape against the current SDK/model access available to your account. Do not assume the model name in the old code is valid.
- The checker uses a small, fixed set of thresholds. Do not imply those ranges are universally appropriate. Show the source/context and mark unsupported or ambiguous tests as **Unverified**.
- Keep sample reports synthetic; do not use real patient records in demos, logs, or tests.

---

## 2. MVP definition

### Must work in the hackathon demo

- [ ] Run locally using a documented setup.
- [ ] Upload a report image and show a preview.
- [ ] Extract structured data with a clearly displayed success/error state.
- [ ] Validate model output against a strict schema before evaluation.
- [ ] Compare only known tests with configured reference ranges.
- [ ] Preserve unknown tests as unverified instead of guessing.
- [ ] Show values, units, status, and a plain Nepali explanation.
- [ ] Provide audio only when generation succeeds; display a useful fallback message otherwise.
- [ ] Include a clear medical limitation notice.
- [ ] Run automated tests for the deterministic checker without requiring an API key.

### Defer until the MVP is stable

- Login/accounts, database, patient history, cloud deployment, complex agent frameworks, multi-agent orchestration, and elaborate UI redesign.
- Do not add a framework just to call the project “agentic.” A reliable pipeline with clear component boundaries, validation, and observable steps is better than unnecessary agents.

---

## 3. Agent operating rules

Use one coding agent at a time for a task unless work is truly independent. The human developer owns architecture and accepts every change.

### Required workflow for every task

1. **Inspect:** Read relevant files and report what the current code does. Do not edit yet.
2. **Plan:** Propose the smallest change, the files affected, and a test.
3. **Implement:** Make only that change. Avoid unrelated refactors.
4. **Verify:** Run the stated test or command and report exact results. Never claim a test passed if it was not run.
5. **Review:** Explain the diff, trade-offs, and any remaining risk.
6. **Commit:** The human reviews and commits the change with one meaningful commit message.

### Global agent prompt

Copy this prompt into your coding agent at the beginning of a session:

> You are helping me rebuild Swasthya Reader for a hackathon. First inspect the repository and the task. Do not rewrite the whole application. Work in small, reviewable increments and edit only the files needed for the current task. Before editing, explain the problem and propose a minimal plan. Preserve working behavior unless the task explicitly changes it. Add or update tests where appropriate, run the relevant tests, and report commands and actual outcomes. Do not invent test results, API capabilities, clinical facts, or reference ranges. Never expose secrets. Do not commit on my behalf. After the change, summarize the diff, explain the important code in beginner-friendly language, list known limitations, and suggest the next smallest step. Treat medical output as informational and uncertain, not as diagnosis or treatment advice.

### Commit discipline

- One commit = one understandable change.
- Prefer 1–5 files per commit where practical.
- Do not mix formatting, refactoring, features, and dependency upgrades in one commit.
- Do not commit broken code knowingly; if a step is intentionally incomplete, keep it on a short-lived branch and label it clearly.
- After each milestone, check `git status`, inspect `git diff`, run tests, then commit.
- If an agent produces a huge diff, ask it to split the work before accepting it.

---

## 4. Incremental milestones and commit checklist

Follow the sequence. Skip a step only if you verify that it is already done correctly.

## Milestone 0 — Repository hygiene and baseline

### Task 0.1 — Inspect and record the baseline

**Agent task:** Inspect the project structure and summarize entry points, dependencies, data flow, and known bugs. No edits.

**Human checks:**
- [ ] I can explain the pipeline in my own words.
- [ ] I know which parts require network/API access.
- [ ] I have not shared `.env` contents with the agent or committed secrets.

### Task 0.2 — Add `.gitignore`

Add ignores for at least:

```gitignore
.env
.env.*
!.env.example
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.DS_Store
.streamlit/secrets.toml
```

**Verify:**
```bash
git status --short
git check-ignore .env .venv/
```

**Commit:**
```bash
git add .gitignore
git commit -m "chore: ignore local secrets and Python artifacts"
```

### Task 0.3 — Clean dependencies

Compare imports with `requirements.txt`. Resolve `gTTS` versus `edge-tts` and decide whether Ollama is an MVP dependency. Avoid adding packages that are not used.

**Verify in a fresh virtual environment** rather than relying on the supplied `.venv`.

**Commit:** `chore: align dependencies with application imports`

---

## Milestone 1 — Make the deterministic skill trustworthy

Build and test the deterministic core before spending time on model integrations.

### Task 1.1 — Add checker tests

Create tests for:
- Valid known result above the configured maximum.
- Valid known result below the configured minimum.
- A value at each boundary.
- A normal value.
- An unknown test name.
- Missing `results`, empty `results`, missing value, and non-numeric value.
- Malformed JSON.
- A non-object JSON value and malformed result entries.

Use synthetic inputs only. Do not call an LLM in unit tests.

**Suggested commands:**
```bash
python -m pytest -q
```

If `pytest` is not installed, add it as a development dependency or use the test framework already in the project.

**Commit:** `test: cover lab checker boundary and invalid inputs`

### Task 1.2 — Validate input shape

Add explicit validation before evaluation. Check that the top-level input is an object, `results` is a list, and each result has a test name, numeric value, and unit as appropriate. Return actionable validation errors instead of crashing or silently dropping important data.

Avoid silently interpreting booleans as numeric lab values. Do not invent missing values or units.

**Verify:** Run the complete checker test suite.

**Commit:** `feat: validate extracted lab result structure`

### Task 1.3 — Make test matching safer

Review how test names are matched. Avoid a broad substring match accidentally matching the wrong test. Add explicit aliases for common spelling/format variations only when justified, and test them. Unknown names must remain unverified.

**Commit:** `fix: match supported lab tests without ambiguous guesses`

### Task 1.4 — Clarify range and medical limitations

Ensure each result clearly separates:
- Extracted value and unit.
- Configured reference interval and its unit.
- Status (`High`, `Low`, `Normal`, or `Unverified`).
- A cautious explanation and next-step suggestion.

The reference ranges currently in the project are demo configuration, not universal clinical truth. Document their source and intended population before using them for real-world interpretation. If the source cannot be verified, label them as demo ranges and avoid strong treatment instructions.

**Commit:** `docs: clarify reference range and medical limitations`

---

## Milestone 2 — Define the extraction contract

### Task 2.1 — Create a schema for model output

Define a small, explicit data contract for:

```json
{
  "patient_name": null,
  "test_date": null,
  "results": [
    {
      "test_name": "Fasting Blood Sugar",
      "value": 138.0,
      "unit": "mg/dL"
    }
  ]
}
```

Treat this as an example shape, not a guaranteed model response. The actual validator should handle null/unknown patient metadata, empty results, unexpected fields, wrong types, and invalid numbers safely.

Keep extraction separate from clinical evaluation: the vision model reads the report; deterministic Python code validates and classifies supported values.

**Commit:** `feat: define structured lab extraction schema`

### Task 2.2 — Add parsing and normalization helpers

Move model-output parsing out of the Streamlit button handler into a small, independently testable module. Handle common wrappers such as fenced JSON only if needed, reject malformed JSON, and return useful errors.

Do not “repair” ambiguous numeric readings by guessing. Preserve uncertainty and ask for a clearer image when necessary.

**Commit:** `refactor: isolate extraction response parsing`

### Task 2.3 — Test parsing without network access

Use representative synthetic strings:
- Valid JSON.
- JSON surrounded by Markdown fences.
- Truncated JSON.
- Missing required fields.
- String value where a number is expected.
- Empty results.

**Commit:** `test: cover extraction parsing and validation`

---

## Milestone 3 — Isolate the vision provider

### Task 3.1 — Create one provider interface

Create a small extraction function/module with a clear contract, for example:

```python
def extract_lab_report(image_bytes: bytes) -> dict:
    """Return validated structured report data or raise a clear provider error."""
```

The provider should do only model communication and output parsing. It should not render Streamlit UI, classify medical values, or generate audio.

### Task 3.2 — Make API-key handling safe

Read secrets from environment variables or Streamlit secrets. Keep manual key entry only if needed for the demo, use a password field, and never print/log the key. Add `.env.example` with placeholder names only.

### Task 3.3 — Add clear provider errors

Distinguish at least:
- Missing API key.
- Provider/network failure.
- Unsupported model or permission error.
- Empty response.
- Invalid model JSON.
- Image could not be decoded.

Avoid displaying raw tracebacks or secret-bearing request details to end users. Keep detailed errors in local development logs only after checking they contain no secrets.

### Task 3.4 — Verify a real extraction manually

Use a synthetic sample report first. Compare extracted values and units with the image manually. Record failure cases; do not assume a successful API response means accurate OCR.

**Commit suggestions:**
- `feat: isolate vision extraction provider`
- `fix: handle extraction provider errors safely`
- `test: add mocked extraction provider tests`

---

## Milestone 4 — Make the UI a clear pipeline

### Task 4.1 — Separate UI from business logic

Keep `app.py` as a thin Streamlit entry point. Move logic into focused modules only when that makes testing or reading easier. Suggested structure:

```text
swastha-reader/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── tests/
│   ├── test_checker.py
│   ├── test_parsing.py
│   └── test_pipeline.py
└── skills/
    └── swasthyalabchecker/
        ├── SKILL.md
        ├── checker.py
        └── reference_ranges.py
```

Do not move every function into a separate file just for architectural appearance.

### Task 4.2 — Show pipeline stages

Use clear UI states:
1. Image selected.
2. Extracting text/data.
3. Validating extracted data.
4. Evaluating supported tests.
5. Preparing audio.
6. Complete or failed.

Show a helpful message for each stage. Never show “verified” if the schema or extraction failed.

### Task 4.3 — Improve findings display

For every test, display:
- Test name.
- Observed value and unit.
- Configured reference interval, where available.
- Status and plain-language explanation.
- A visible “not verified” state for unknown tests.

Show the medical disclaimer before or alongside results, not only at the bottom.

**Commit:** `feat: display extraction and evaluation stages clearly`

---

## Milestone 5 — Add Nepali audio reliably

### Task 5.1 — Test text sanitization

Unit-test `clean_text_for_speech()` for Markdown symbols, empty input, unit replacements, Devanagari text, and punctuation. Avoid deleting meaningful characters from patient explanations.

### Task 5.2 — Isolate text-to-speech

Create a function that receives text and returns audio bytes or a clear failure. Keep it independent of Streamlit. Confirm the selected library and language code work in the target environment.

**Important:** Network-based TTS may fail or send text to an external service. Tell users when audio generation uses a remote provider, and do not send unnecessary identifying information. Consider omitting the patient name from audio by default.

### Task 5.3 — Avoid duplicate expensive work

Generate audio only when requested, or cache it carefully for the current session. Do not call the TTS provider repeatedly just because Streamlit reruns the script. Do not persist medical content in a cache without a clear privacy decision.

**Commit suggestions:**
- `test: cover Nepali speech text cleanup`
- `feat: isolate Nepali text-to-speech generation`
- `fix: handle audio generation failures gracefully`

---

## Milestone 6 — End-to-end verification

### Task 6.1 — Add mocked pipeline tests

Test the flow using:
- A known synthetic report.
- A report with an unknown test.
- Invalid extraction output.
- Provider error.
- TTS error.

Mock external providers so the test suite works without API keys, internet access, or a running Ollama server.

### Task 6.2 — Run a manual demo checklist

- [ ] App starts from a fresh environment.
- [ ] Sample report selection works.
- [ ] JPG upload works.
- [ ] Unsupported file type is rejected.
- [ ] Missing API key gives a clear message.
- [ ] Extraction output is validated before evaluation.
- [ ] Unknown tests are not classified as normal.
- [ ] Invalid model output does not crash the app.
- [ ] Audio playback works or fails gracefully.
- [ ] No secrets appear in terminal output, UI, logs, or Git.
- [ ] Disclaimer is visible.
- [ ] Demo works with a clean browser session.

**Commit:** `test: add mocked end-to-end pipeline coverage`

---

## Milestone 7 — Demo readiness and documentation

### README checklist

Document:
- What the project does and does not do.
- Architecture/data flow.
- Prerequisites.
- Installation and startup commands.
- Required environment variables, with no real secrets.
- How to configure the vision provider.
- How to run tests.
- Known limitations and privacy considerations.
- Demo scenarios and expected results.

Example setup (adjust for the final dependency set):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If a test dependency is separate, document how to install it. If Ollama is supported, document its separate installation, model download, and startup requirements. Do not claim offline mode works unless it has been tested without network access.

**Commit:** `docs: document setup architecture and demo limitations`

---

## 5. Optional agent roles (only after the core works)

These can be separate prompts, but they should not all edit the same files concurrently.

### A. Repository analyst
> Read the repository only. Map the current data flow, identify bugs and risks, and propose the smallest next task. Do not edit files.

### B. Test engineer
> Inspect the current deterministic checker and write focused tests for one behavior at a time. Do not change production code to make tests pass unless I explicitly assign a fix task. Explain each test and run it.

### C. Backend/refactoring engineer
> Implement one small, testable extraction or validation task. Keep model communication separate from clinical evaluation and UI. Do not refactor unrelated code.

### D. UI engineer
> Improve one UI interaction or display state at a time. Do not change the evaluation logic or add new dependencies unless asked. Verify that failure states are understandable.

### E. Reviewer / safety reviewer
> Review the current diff without editing. Look for incorrect assumptions, unsafe medical wording, ambiguous matching, missing validation, privacy leaks, exposed secrets, unhandled exceptions, and missing tests. Return findings ordered by severity, with file/line references where possible.

### F. Demo coach
> Use only the actual current implementation. Produce a 2-minute demo script, identify likely judge questions, and list which claims are demonstrated versus planned. Do not claim unsupported accuracy or clinical validity.

---

## 6. Suggested Git rhythm

For each task:

```bash
git status --short
git diff --check
git diff
python -m pytest -q
```

Then commit only the intended files:

```bash
git add path/to/changed_file.py path/to/test_file.py
git commit -m "test: cover invalid lab result input"
```

Useful commit prefixes:
- `chore:` repository or dependency maintenance
- `docs:` documentation
- `test:` tests only
- `fix:` bug fix
- `feat:` user-visible or functional capability
- `refactor:` behavior-preserving code structure change

Use a task branch if experimenting:

```bash
git switch -c feat/validated-extraction
```

Do not run `git add .` blindly when secrets, generated files, sample artifacts, or unrelated changes may exist.

---

## 7. Hackathon time-boxing

If time is short, prioritize in this order:

1. **Run reliably:** clean setup and dependencies.
2. **Trust the deterministic core:** tests, schema validation, unknown-test handling.
3. **Prove one end-to-end path:** synthetic image → extraction → evaluation.
4. **Make failure states clear:** missing key, bad JSON, unreadable image, provider timeout.
5. **Add audio only after the core flow works.**
6. **Polish the demo and README.**

Do not sacrifice input validation, privacy, or clear uncertainty to add extra “agents.” If the team has multiple people, assign independent work such as tests, README/demo script, and UI review, then integrate through small reviewed commits.

---

## 8. Definition of done

The hackathon MVP is ready when:

- [ ] A new developer can set it up from the README.
- [ ] The app runs without relying on the ZIP's pre-existing virtual environment.
- [ ] Deterministic checker tests pass.
- [ ] External providers are mockable and failures are handled.
- [ ] Model output is validated before any classification.
- [ ] Unsupported or ambiguous tests remain unverified.
- [ ] The interface does not claim to diagnose or prescribe treatment.
- [ ] Secrets and private patient data are not committed or logged.
- [ ] The full demo has been run from a clean environment.
- [ ] You can explain every committed change and its test.

**Final rule:** Ask the coding agent to implement only the next unchecked task. Review, run, understand, and commit it before moving on.
