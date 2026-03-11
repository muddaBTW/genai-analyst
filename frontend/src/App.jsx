/**
 * App.jsx — main application shell with sidebar navigation and section routing.
 * Manages global state: uploaded dataset, analysis, charts, insights.
 */
import { useState, useCallback } from "react";
import "./App.css";
import {
  uploadDataset,
  fetchAnalysis,
  fetchVisualizations,
  fetchInsights,
} from "./api/client";

import FileUpload from "./components/FileUpload";
import DatasetOverview from "./components/DatasetOverview";
import Visualizations from "./components/Visualizations";
import AiInsights from "./components/AiInsights";
import AskQuestions from "./components/AskQuestions";
import LoadingSpinner from "./components/LoadingSpinner";
import GenerateReport from "./components/GenerateReport";

const SECTIONS = [
  { id: "upload", label: "Upload", icon: "📂" },
  { id: "overview", label: "Dataset Overview", icon: "📊" },
  { id: "visualizations", label: "Visualizations", icon: "📈" },
  { id: "insights", label: "AI Insights", icon: "🧠" },
  { id: "ask", label: "Ask Questions", icon: "💬" },
  { id: "report", label: "Export Report", icon: "📝" },
];

export default function App() {
  const [section, setSection] = useState("upload");

  // Dataset state
  const [metadata, setMetadata] = useState(null);
  const [preview, setPreview] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [charts, setCharts] = useState(null);
  const [insights, setInsights] = useState(null);

  // Loading state
  const [uploadLoading, setUploadLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [chartsLoading, setChartsLoading] = useState(false);
  const [insightsLoading, setInsightsLoading] = useState(false);

  const hasDataset = !!metadata;

  /**
   * Handle file upload — after successful upload, automatically
   * kick off analysis, visualization generation, and AI insights.
   */
  const handleUpload = useCallback(async (file) => {
    setUploadLoading(true);
    try {
      const data = await uploadDataset(file);
      setMetadata(data.metadata);
      setPreview(data.preview);
      setSection("overview");

      // Fire parallel background tasks
      setAnalysisLoading(true);
      setChartsLoading(true);
      setInsightsLoading(true);

      fetchAnalysis()
        .then((res) => setAnalysis(res))
        .catch(console.error)
        .finally(() => setAnalysisLoading(false));

      fetchVisualizations()
        .then((res) => setCharts(res))
        .catch(console.error)
        .finally(() => setChartsLoading(false));

      fetchInsights()
        .then((res) => setInsights(res.insights))
        .catch(console.error)
        .finally(() => setInsightsLoading(false));
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploadLoading(false);
    }
  }, []);

  // Render active section
  const renderSection = () => {
    switch (section) {
      case "upload":
        return <FileUpload onUpload={handleUpload} isLoading={uploadLoading} />;
      case "overview":
        return analysisLoading && !analysis ? (
          <LoadingSpinner text="Analyzing dataset…" />
        ) : (
          <DatasetOverview metadata={metadata} preview={preview} analysis={analysis} />
        );
      case "visualizations":
        return <Visualizations charts={charts} isLoading={chartsLoading} />;
      case "insights":
        return <AiInsights insights={insights} isLoading={insightsLoading} />;
      case "ask":
        return <AskQuestions hasDataset={hasDataset} />;
      case "report":
        return <GenerateReport hasDataset={hasDataset} />;
      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      {/* ── Sidebar ──────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">⚡</div>
          <h1>GenAI Analyst</h1>
        </div>

        <nav className="sidebar-nav">
          {SECTIONS.map((s) => {
            const disabled = s.id !== "upload" && !hasDataset;
            return (
              <button
                key={s.id}
                className={`nav-item ${section === s.id ? "active" : ""} ${disabled ? "disabled" : ""}`}
                onClick={() => !disabled && setSection(s.id)}
              >
                <span className="nav-icon">{s.icon}</span>
                <span>{s.label}</span>
              </button>
            );
          })}
        </nav>

        {hasDataset && (
          <div style={{ padding: "12px 14px", fontSize: 11, color: "var(--text-muted)", borderTop: "1px solid var(--border-glass)", marginTop: "auto" }}>
            Dataset loaded • {metadata.rows.toLocaleString()} rows × {metadata.columns} cols
          </div>
        )}
      </aside>

      {/* ── Main Content ─────────────────────────────── */}
      <main className="main-content">
        {renderSection()}
      </main>
    </div>
  );
}
