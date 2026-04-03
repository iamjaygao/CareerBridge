#!/usr/bin/env python3
"""
Standalone resume matcher test script.
Uses the main venv (openai is already installed there).
Loads OPENAI_API_KEY from gateai/.env automatically.

Usage:
    python test_resume_match.py <resume_file> <jd_file>

    resume_file : path to a .txt or .pdf resume file
    jd_file     : path to a .txt file containing the job description
"""

import sys
import json
import asyncio
from pathlib import Path

# ── Load .env from gateai/ ────────────────────────────────────────────────────
_env_path = Path(__file__).parent / "gateai" / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            import os; os.environ.setdefault(key.strip(), val.strip())

import os
from openai import AsyncOpenAI


# ── Helpers ───────────────────────────────────────────────────────────────────

def read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    suffix = p.suffix.lower()

    if suffix == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(p) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except ImportError:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(str(p))
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                print("[ERROR] PDF file detected but no PDF library found.")
                print("        Install one of: pip install pdfplumber  OR  pip install PyPDF2")
                sys.exit(1)

    # .txt or anything else — read as plain text
    return p.read_text(encoding="utf-8", errors="ignore")


def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Core matching logic ───────────────────────────────────────────────────────

async def get_semantic_score(client: AsyncOpenAI, resume: str, jd: str) -> float:
    print("  [1/3] Computing embedding similarity ...")
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=[resume[:8000], jd[:8000]],
    )
    raw = _cosine_similarity(
        response.data[0].embedding,
        response.data[1].embedding,
    )
    return (raw + 1) / 2  # normalize [-1,1] → [0,1]


async def get_gpt_analysis(client: AsyncOpenAI, resume: str, jd: str, semantic_score: float) -> dict:
    print("  [2/3] Running GPT-4o-mini gap analysis ...")

    system_prompt = (
        "You are an expert technical recruiter and career coach. "
        "Analyze the resume against the job description and return a JSON object "
        "with EXACTLY this structure — no extra keys, no markdown fences:\n\n"
        "{\n"
        '  "match_score": <integer 0-100>,\n'
        '  "hard_gaps": [\n'
        '    {"issue": "<missing requirement>", "reason": "<why it matters for this JD>"}\n'
        "  ],\n"
        '  "soft_gaps": [\n'
        '    {"issue": "<weakness>", "suggestion": "<specific rewrite or action>"}\n'
        "  ],\n"
        '  "strengths": [\n'
        '    {"point": "<strength>", "why": "<why this JD values it>"}\n'
        "  ],\n"
        '  "recommendations": [\n'
        '    {"action": "<specific actionable step>", "priority": "high|medium|low"}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- match_score: realistic hiring probability (0=no chance, 100=perfect fit)\n"
        "- hard_gaps: requirements explicitly in the JD that are absent from the resume\n"
        "- soft_gaps: things that exist but are weak, vague, or unquantified\n"
        "- strengths: genuine advantages this candidate has for THIS specific role\n"
        "- recommendations: ordered by priority, each action must be specific and executable\n"
        "- Be honest and direct. Do not pad the response."
    )

    user_prompt = (
        f"## RESUME\n{resume[:6000]}\n\n"
        f"## JOB DESCRIPTION\n{jd[:4000]}\n\n"
        f"(Embedding similarity score for context: {round(semantic_score * 100, 1)}%)"
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    return json.loads(response.choices[0].message.content)


async def run(resume_path: str, jd_path: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found.")
        print(f"        Checked gateai/.env at: {_env_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  CareerBridge Resume Matcher — Live Test")
    print(f"{'='*60}")
    print(f"  Resume : {resume_path}")
    print(f"  JD     : {jd_path}")
    print(f"{'='*60}\n")

    resume_text = read_file(resume_path)
    jd_text     = read_file(jd_path)

    print(f"  Resume  : {len(resume_text):,} chars loaded")
    print(f"  JD      : {len(jd_text):,} chars loaded\n")

    client = AsyncOpenAI(api_key=api_key)

    semantic_score = await get_semantic_score(client, resume_text, jd_text)

    analysis = await get_gpt_analysis(client, resume_text, jd_text, semantic_score)

    print("  [3/3] Done.\n")

    # ── Print results ─────────────────────────────────────────────────────────
    ms = analysis.get("match_score", "N/A")
    print(f"{'='*60}")
    print(f"  MATCH SCORE      : {ms} / 100")
    print(f"  Semantic similarity: {round(semantic_score * 100, 1)}%")
    print(f"{'='*60}\n")

    def section(title, items, key1, key2=None):
        print(f"── {title} {'─'*(54-len(title))}")
        if not items:
            print("  (none)\n")
            return
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item.get(key1, '')}")
            if key2 and item.get(key2):
                print(f"     → {item[key2]}")
        print()

    section("HARD GAPS (must fix)",
            analysis.get("hard_gaps", []),    "issue", "reason")
    section("SOFT GAPS (should improve)",
            analysis.get("soft_gaps", []),    "issue", "suggestion")
    section("STRENGTHS",
            analysis.get("strengths", []),    "point", "why")

    print("── RECOMMENDATIONS ─────────────────────────────────────")
    for r in analysis.get("recommendations", []):
        priority = r.get("priority", "").upper()
        pad = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "•")
        print(f"  {pad} [{priority}] {r.get('action', '')}")
    print()

    print("── RAW JSON ─────────────────────────────────────────────")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_resume_match.py <resume_file> <jd_file>")
        print("")
        print("  resume_file : .txt or .pdf")
        print("  jd_file     : .txt file with the job description")
        sys.exit(1)

    asyncio.run(run(sys.argv[1], sys.argv[2]))
