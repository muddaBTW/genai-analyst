"""
AI Service — configurable Gemini or Groq integration for insights, Q&A, and reports.
Only sends summarised metadata to the LLM (never raw data).
"""

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from groq import Groq
from services.data_service import build_llm_summary
from routers.upload import get_current_df

# Initialise the Groq client
_client: Groq | None = None
_last_key_used: str | None = None
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _settings() -> tuple[str, str, str]:
    """Load the selected provider and credentials from backend/.env."""
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    # Explicit configuration wins. Existing Groq-only installations keep working
    # until a Gemini key is added, at which point Gemini becomes the default.
    provider = (os.getenv("AI_PROVIDER") or ("gemini" if os.getenv("GEMINI_API_KEY") else "groq")).strip().lower()
    if provider == "gemini":
        key = (os.getenv("GEMINI_API_KEY") or "").strip().strip("\"'")
        model = (os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        return provider, key, model
    if provider == "groq":
        key = (os.getenv("GROQ_API_KEY") or "").strip().strip("\"'")
        model = (os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile").strip()
        if not key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set")
        return provider, key, model
    raise RuntimeError("AI_PROVIDER must be either 'gemini' or 'groq'")


def _get_client() -> Groq:
    global _client, _last_key_used
    
    provider, api_key, _ = _settings()
    if provider != "groq":
        raise RuntimeError("Groq client requested while AI_PROVIDER is not 'groq'")
    
    # If key changed or client not created, re-initialise
    if _client is None or api_key != _last_key_used:
        _client = Groq(api_key=api_key)
        _last_key_used = api_key
        
    return _client


def _chat(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
    """Send a completion through the configured provider and return its text."""
    provider, api_key, model = _settings()
    if provider == "groq":
        client = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.5,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": max_tokens},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        response = httpx.post(url, params={"key": api_key}, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned no text")
        return text
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        detail = response.text[:400] if "response" in locals() else str(exc)
        raise RuntimeError(f"Gemini request failed: {detail}") from exc


# ── AI Insights ────────────────────────────────────────────────────────────

def generate_insights(summary: str) -> str:
    """Ask the LLM to produce key insights from the dataset summary."""
    system = (
        "You are a senior data analyst. Based on the dataset summary provided, "
        "generate a detailed analysis with the following sections:\n"
        "1. **Key Insights** — the most important findings\n"
        "2. **Trends & Patterns** — recurring patterns in the data\n"
        "3. **Possible Anomalies** — anything unusual or suspicious\n"
        "4. **Business Recommendations** — actionable advice\n"
        "5. **Plain English Summary** — a non-technical explanation\n\n"
        "Use markdown formatting. Be specific and reference actual column names and values."
    )
    return _chat(system, f"Here is the dataset summary:\n\n{summary}")


# ── Natural Language Q&A ───────────────────────────────────────────────────

def answer_question(question: str, summary: str, history: list[dict[str, str]] | None = None) -> str:
    """Answer a user question about the dataset using the summary as context."""
    system = (
        "You are a senior data analyst assistant. The user will ask a question about "
        "their dataset. Use the dataset summary provided as context to answer. "
        "Be conversational and helpful, like a polished ChatGPT reply. Keep answers concise: lead with the answer, "
        "then add at most three short bullets only when useful. Avoid large headings, long preambles, and repeated context. "
        "Be precise, cite column names and values where possible. If you cannot answer from the summary, say so plainly."
    )
    user = (
        f"Dataset summary:\n{summary}\n\n"
        f"Recent conversation:\n{_format_history(history)}\n\nUser question: {question}"
    )
    return _chat(system, user)


def answer_with_rag(question: str, retrieved: list[dict], history: list[dict[str, str]] | None = None) -> str:
    """Answer a question using retrieved passages as context (RAG).

    `retrieved` should be a list of dicts with keys `row_index`, `text`, and `row`.
    """
    # Build a richer context: include dataset-level summary if available
    context_lines = []
    row_ids = []
    for item in retrieved:
        row_ids.append(str(item.get("row_index")))
        # include a compact row representation
        context_lines.append(f"[row {item.get('row_index')}] {item.get('text')}")

    context = "\n".join(context_lines)

    # Try to include a dataset summary (missing counts, column names) so the model
    # can answer dataset-level questions even if retrieved rows don't contain that info.
    summary_text = None
    try:
        df = get_current_df()
        if df is not None:
            summary_text = build_llm_summary(df)
    except Exception:
        summary_text = None

    system = (
        "You are a senior data analyst assistant. Answer the user's question using the provided dataset summary and retrieved rows. "
        "Always prefer explicit dataset-level statistics (e.g., missing-value counts, column types) when the question asks about dataset properties. "
        "Cite row indices in your answer like [row 12] when referring to specific rows. Be concise and conversational; avoid large headings. "
        "Do not invent facts; if the information is not present, say you don't know."
    )

    user_parts = []
    if summary_text:
        user_parts.append("Dataset summary:\n" + summary_text)
    if context:
        user_parts.append("Retrieved rows:\n" + context)
    user_parts.append("Recent conversation:\n" + _format_history(history))
    user_parts.append("User question: " + question)

    user = "\n\n".join(user_parts)

    return _chat(system, user)


def _format_history(history: list[dict[str, str]] | None) -> str:
    """Use a small, sanitized history window so follow-up questions remain contextual."""
    if not history:
        return "(No prior messages.)"
    lines = []
    for message in history[-8:]:
        role = "Assistant" if message.get("role") == "ai" else "User"
        text = str(message.get("text", "")).strip()
        if text:
            lines.append(f"{role}: {text[:1200]}")
    return "\n".join(lines) or "(No prior messages.)"


def explain_visualization(chart: dict[str, Any], summary: str) -> str:
    """Explain a chart choice on demand without sending raw dataset rows to the model."""
    system = (
        "You are a data visualization expert. Explain why this chart was chosen for this dataset. "
        "Give a concise, user-friendly answer in two short paragraphs or up to three bullets. "
        "Mention the relationships or distributions it helps investigate, and do not claim findings not in the metadata."
    )
    chart_context = {
        "type": chart.get("type"),
        "title": chart.get("figure", {}).get("layout", {}).get("title", {}).get("text"),
        "columns": chart.get("columns"),
        "ai_suggestion": chart.get("suggestion"),
    }
    return _chat(system, f"Dataset summary:\n{summary}\n\nChart metadata:\n{chart_context}", max_tokens=350)


# ── Report Content ─────────────────────────────────────────────────────────

def generate_report_content(summary: str, insights: str) -> str:
    """Generate full report text from the AI."""
    system = (
        "You are a senior data analyst preparing a professional report. "
        "Write a concise, professional report in markdown format with short sections and light narrative. "
        "Use the following structure exactly:\n"
        "1. Executive Summary\n"
        "2. Dataset Overview\n"
        "3. Key Statistics\n"
        "4. Key Findings\n"
        "5. Recommendations\n"
        "6. Conclusion\n\n"
        "Rules:\n"
        "- Keep each section brief and easy to scan.\n"
        "- Use bullets where possible instead of long paragraphs.\n"
        "- Refer to the dataset summary and insights only; do not invent facts.\n"
        "- Include simple markdown tables when comparing numbers, categories, or top relationships.\n"
        "- Prefer 3 to 5 bullets per section."
    )
    user = (
        f"Dataset summary:\n{summary}\n\n"
        f"Previously generated insights:\n{insights}\n\n"
        "Formatting guidance:\n"
        "- Add at least one compact markdown table if you can summarize metrics cleanly.\n"
        "- Keep recommendations actionable and specific.\n"
        "- Avoid essay-style paragraphs."
    )
    return _chat(system, user, max_tokens=4096)


# ── Smart Visualizations ────────────────────────────────────────────────────

def suggest_visualizations(summary: str) -> list[dict]:
    """Suggest 3-5 complex and insightful visualizations based on metadata."""
    import json
    import re

    system = (
        "You are a senior data visualization expert. "
        "Your goal is to suggest 3-5 high-impact, complex visualizations that reveal deep insights. "
        "Avoid simple histograms or single-variable bar charts unless they are exceptional. "
        "Focus on multivariate relationships (e.g., scatter with color/size, faceted plots).\n\n"
        "Return ONLY a JSON list of objects with these keys:\n"
        "- 'type': String (one of: 'scatter', 'bar', 'box', 'violin', 'line', 'histogram')\n"
        "- 'kwargs': Dictionary of Plotly Express keyword arguments (e.g., x, y, color, facet_col, marginal_x, marginal_y, trendline, etc.)\n"
        "- 'title': String (descriptive title for the chart)\n\n"
        "Rules:\n"
        "1. Only use column names present in the summary.\n"
        "2. Ensure the code is 'complex' and professional (use color for categories, trendlines for correlations).\n"
        "3. Do not include markdown code blocks, just raw JSON."
    )
    
    response = _chat(system, f"Suggest visualizations for this dataset summary:\n\n{summary}")
    
    # Try to extract JSON if the model included conversational filler
    try:
        # Look for the first '[' and last ']'
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(response)
    except Exception as e:
        print(f"AI Viz Suggestion Error: {e}\nResponse: {response}")
        return []
