"""
AI Service — Groq LLM integration for insights, Q&A, and report generation.
Only sends summarised metadata to the LLM (never raw data).
"""

import os
from groq import Groq

# Initialise the Groq client once
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set")
        _client = Groq(api_key=api_key)
    return _client


def _chat(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
    """Send a chat completion request to Groq and return the text."""
    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


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

def answer_question(question: str, summary: str) -> str:
    """Answer a user question about the dataset using the summary as context."""
    system = (
        "You are a senior data analyst assistant. The user will ask a question about "
        "their dataset. Use the dataset summary provided as context to answer. "
        "Be precise, cite column names and values where possible, and use markdown. "
        "If you cannot answer from the summary, say so."
    )
    user = (
        f"Dataset summary:\n{summary}\n\n"
        f"User question: {question}"
    )
    return _chat(system, user)


# ── Report Content ─────────────────────────────────────────────────────────

def generate_report_content(summary: str, insights: str) -> str:
    """Generate full report text from the AI."""
    system = (
        "You are a senior data analyst preparing a professional report. "
        "Write a comprehensive, well-structured report in markdown format "
        "with the following sections:\n"
        "1. Executive Summary\n"
        "2. Dataset Overview\n"
        "3. Key Statistics\n"
        "4. Detailed Analysis\n"
        "5. Insights & Findings\n"
        "6. Recommendations\n"
        "7. Conclusion\n\n"
        "Be professional, specific, and reference actual data."
    )
    user = (
        f"Dataset summary:\n{summary}\n\n"
        f"Previously generated insights:\n{insights}"
    )
    return _chat(system, user, max_tokens=4096)
