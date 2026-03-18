"""
AI Service — Groq LLM integration for insights, Q&A, and report generation.
Only sends summarised metadata to the LLM (never raw data).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Initialise the Groq client
_client: Groq | None = None
_last_key_used: str | None = None
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _get_client() -> Groq:
    global _client, _last_key_used
    
    # Reload backend/.env so changes apply regardless of the current working directory.
    load_dotenv(dotenv_path=ENV_FILE, override=True)

    api_key = (os.getenv("GROQ_API_KEY") or "").strip().strip("\"'")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")
    
    # If key changed or client not created, re-initialise
    if _client is None or api_key != _last_key_used:
        _client = Groq(api_key=api_key)
        _last_key_used = api_key
        
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
