/**
 * API Client — centralised HTTP helpers for the backend.
 */

// Use VITE_API_BASE_URL if set, otherwise use relative path so it hits Vercel's /api internally, otherwise fallback to localhost for dev
// Default dev backend port changed to 8000 (local FastAPI default)
const BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? "/api" : "http://localhost:8000/api");

/**
 * Upload a dataset file.
 * @param {File} file
 * @returns {Promise<object>} { filename, metadata, preview }
 */
export async function uploadDataset(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
  return res.json();
}

/**
 * Fetch automated analysis results.
 */
export async function fetchAnalysis() {
  const res = await fetch(`${BASE}/analyze`);
  if (!res.ok) throw new Error((await res.json()).detail || "Analysis failed");
  return res.json();
}

/**
 * Fetch Plotly chart specs.
 */
export async function fetchVisualizations() {
  const res = await fetch(`${BASE}/visualizations`);
  if (!res.ok) throw new Error((await res.json()).detail || "Viz failed");
  return res.json();
}

/**
 * Fetch AI insights.
 */
export async function fetchInsights() {
  const res = await fetch(`${BASE}/insights`);
  if (!res.ok) throw new Error((await res.json()).detail || "Insights failed");
  return res.json();
}

/**
 * Ask a natural-language question about the dataset.
 * @param {string} question
 */
export async function askQuestion(question, history = [], datasetId = null) {
  const res = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history, dataset_id: datasetId }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Query failed");
  return res.json();
}

/** Get a concise AI explanation of why a chart was generated. */
export async function explainVisualization(chart) {
  const res = await fetch(`${BASE}/visualizations/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chart }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Explanation failed");
  return res.json();
}

/**
 * Build or rebuild the vector index (RAG) on the backend.
 */
export async function buildIndex(datasetId = null) {
  const res = await fetch(`${BASE}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Index build failed");
  return res.json();
}

/**
 * Download a generated report.
 * @param {"markdown"|"pdf"} format
 */
export async function downloadReport(format = "markdown") {
  const res = await fetch(`${BASE}/report?format=${format}`);
  if (!res.ok) throw new Error("Report generation failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = format === "pdf" ? "report.pdf" : "report.md";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
