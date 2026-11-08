"""Supabase persistence with an in-memory safety net.

If Supabase is not configured, or a call to it fails, the app keeps working from memory
and prints a loud warning in the backend terminal. Always confirm rows appear in the
Supabase Table Editor before relying on persistence.
"""
import uuid
from datetime import datetime, timezone

from .config import SUPABASE_SERVICE_KEY, SUPABASE_URL

_sb = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    from supabase import create_client

    _sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

_mem_reports: dict[str, dict] = {}
_mem_messages: dict[str, list[dict]] = {}


def _warn(action: str, err: Exception) -> None:
    print(f"[db] WARNING: Supabase {action} failed, using in-memory storage instead: {err}")
    if "row-level security" in str(err).lower():
        print("[db] SUPABASE_SERVICE_KEY is not the secret / service_role key. Use that key, not the anon or publishable one.")


def save_report(record: dict) -> str:
    if _sb:
        try:
            return _sb.table("reports").insert(record).execute().data[0]["id"]
        except Exception as e:
            _warn("insert", e)
    rid = str(uuid.uuid4())
    _mem_reports[rid] = {"id": rid, "created_at": datetime.now(timezone.utc).isoformat(), **record}
    return rid


def get_report(report_id: str) -> dict | None:
    if report_id in _mem_reports:
        return _mem_reports[report_id]
    if _sb:
        try:
            data = _sb.table("reports").select("*").eq("id", report_id).limit(1).execute().data
            return data[0] if data else None
        except Exception as e:
            _warn("read", e)
    return None


def add_message(report_id: str, role: str, content: str) -> None:
    if report_id not in _mem_reports and _sb:
        try:
            _sb.table("chat_messages").insert({"report_id": report_id, "role": role, "content": content}).execute()
            return
        except Exception as e:
            _warn("message insert", e)
    _mem_messages.setdefault(report_id, []).append({"role": role, "content": content})


def get_messages(report_id: str, limit: int) -> list[dict]:
    if report_id not in _mem_reports and _sb:
        try:
            rows = (
                _sb.table("chat_messages")
                .select("role,content,created_at")
                .eq("report_id", report_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
                .data
            )
            return list(reversed(rows))
        except Exception as e:
            _warn("message read", e)
    return _mem_messages.get(report_id, [])[-limit:]