/**
 * API Client — centralised HTTP helpers for the backend.
 */

// Use VITE_API_BASE_URL if set, otherwise use relative path so it hits Vercel's /api internally, otherwise fallback to localhost for dev
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
export async function askQuestion(question) {
  const res = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Query failed");
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
