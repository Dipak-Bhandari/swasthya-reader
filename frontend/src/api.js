const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function handle(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export async function uploadReport(file) {
  const form = new FormData();
  form.append("file", file);
  return handle(await fetch(`${BASE}/api/reports`, { method: "POST", body: form }));
}

export async function askQuestion(reportId, question) {
  return handle(
    await fetch(`${BASE}/api/reports/${reportId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
  );
}
