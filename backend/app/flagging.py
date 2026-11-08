"""Deterministic abnormal-value flagging. The model never decides low/normal/high.

Handles the range formats seen on real Nepali lab reports:
  "13.0 - 17.0"                      plain range
  "<37" / "less than 240" / ">40"    one-sided
  "Adult: 98 - 279"                  labelled
  "Male: 13-17 Female: 12-15"        sex-specific (uses patient sex if known)
  "Normal: <150, Borderline high: 150-199, High: 200-499, Very High: >/=500"
    tiered (uses the Normal/Optimal band, remembers the other bands)
"""
import re

_NUM = r"(\d+(?:\.\d+)?)"

_RANGE = re.compile(rf"{_NUM}\s*(?:-|to)\s*{_NUM}", re.I)
_GT_AFTER = re.compile(rf"{_NUM}\s*%?\s*(?:and|or)\s*(?:above|more|greater|higher)", re.I)
_LT = re.compile(
    rf"(?:<\s*/?\s*=|<=|≤|<|up\s*to|upto|less\s+than|below|not\s+more\s+than)\s*{_NUM}", re.I
)
_GT = re.compile(rf"(?:>\s*/?\s*=|>=|≥|>|more\s+than|greater\s+than|above)\s*{_NUM}", re.I)

# split tiers on ';', newlines, ', <Letter>' and before 'Male:' / 'Female:' style labels
_SPLIT = re.compile(r";|\n|,(?=\s*[A-Za-z])|\s+(?=(?:male|female|men|women)\s*:)", re.I)

_NORMAL_LABEL = re.compile(r"normal|optimal|desirable|adult|reference|non[- ]?diabetic|healthy", re.I)
_FEMALE = re.compile(r"\b(female|women|f)\b", re.I)
_MALE = re.compile(r"\b(male|men|m)\b", re.I)


def _to_float(text):
    m = re.search(_NUM, str(text).replace(",", ""))
    return float(m.group(1)) if m else None


def _bounds(body: str):
    s = body.replace(",", "").replace("–", "-").replace("—", "-")
    m = _RANGE.search(s)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _GT_AFTER.search(s)
    if m:
        return float(m.group(1)), None
    m = _LT.search(s)
    if m:
        return None, float(m.group(1))
    m = _GT.search(s)
    if m:
        return float(m.group(1)), None
    return None


def _segments(text: str):
    """Return [(label, (low, high))] for every parseable segment."""
    out = []
    for seg in _SPLIT.split(str(text or "")):
        seg = seg.strip()
        if not seg:
            continue
        if ":" in seg:
            label, body = seg.split(":", 1)
        else:
            label, body = "", seg
        b = _bounds(body)
        if b:
            out.append((label.strip(), b))
    return out


def _union(bands):
    lows = [b[0] for _, b in bands if b[0] is not None]
    highs = [b[1] for _, b in bands if b[1] is not None]
    return (min(lows) if lows else None, max(highs) if highs else None)


def parse_reference(text: str, sex: str | None = None):
    """Return (normal_range, all_bands). normal_range is (low, high) or None if unclear."""
    bands = _segments(text)
    if not bands:
        return None, []

    sexed = [(l, b) for l, b in bands if _FEMALE.search(l) or _MALE.search(l)]
    if sexed:
        chosen = None
        if sex == "F":
            chosen = next((x for x in sexed if _FEMALE.search(x[0])), None)
        elif sex == "M":
            chosen = next((x for x in sexed if _MALE.search(x[0]) and not _FEMALE.search(x[0])), None)
        normal = chosen[1] if chosen else _union(sexed)
        return normal, bands

    for label, b in bands:
        if label == "" or _NORMAL_LABEL.search(label):
            return b, bands
    return None, bands  # only risk bands listed (e.g. "Diabetic: >126"): do not guess


def _tolerance(name: str) -> set:
    """Directions that are usually not a health worry for this test. Starter list: have a doctor review it."""
    n = name.lower()
    if re.search(r"\bhdl\b", n):
        return {"high"}  # higher HDL is not a concern
    if re.search(
        r"triglycerid|\bldl\b|\bvldl\b|cholesterol|\bsgot\b|\bast\b|\bsgpt\b|\balt\b|gamma|\bggt\b|bilirubin|alkaline|\balp\b",
        n,
    ):
        return {"low"}  # low values of these are usually harmless
    return set()


def _band_label(value, bands):
    for label, (lo, hi) in bands:
        if (lo is None or value >= lo) and (hi is None or value <= hi):
            return label
    return ""


def flag_test(test: dict, sex: str | None = None) -> dict:
    value = _to_float(test.get("value", ""))
    normal, bands = parse_reference(test.get("reference_range", ""), sex)

    status = "unknown"
    if value is not None and normal is not None:
        low, high = normal
        if low is not None and value < low:
            status = "low"
        elif high is not None and value > high:
            status = "high"
        else:
            status = "normal"

    concern = status in ("low", "high") and status not in _tolerance(test.get("name", ""))

    severity = "none"
    if concern:
        bound = normal[0] if status == "low" else normal[1]
        if bound:
            deviation = abs(value - bound) / abs(bound)
            severity = "marked" if deviation > 0.25 else "mild"

    band = ""
    if status in ("low", "high"):
        band = _band_label(value, bands)
        if _NORMAL_LABEL.search(band) or _FEMALE.search(band) or _MALE.search(band):
            band = ""

    # If the report itself labels the value "High", "Very High" or "Diabetic", treat it as marked.
    if concern and re.match(r"(very high|high|diabet\w*|severe|critical)\b", band, re.I):
        severity = "marked"

    return {**test, "status": status, "concern": concern, "severity": severity, "band": band}


def _norm_sex(sex):
    s = str(sex or "").strip().upper()[:1]
    return s if s in ("M", "F") else None


def flag_all(tests: list[dict], sex: str | None = None) -> list[dict]:
    s = _norm_sex(sex)
    return [flag_test(t, s) for t in tests]


def needs_doctor_soon(flagged: list[dict]) -> bool:
    return any(t["severity"] == "marked" for t in flagged)