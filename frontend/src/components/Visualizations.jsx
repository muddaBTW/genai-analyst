/**
 * Visualizations — renders Plotly charts from backend JSON specs with fullscreen support.
 */
import { useState } from "react";
import Plot from "react-plotly.js";
import LoadingSpinner from "./LoadingSpinner";

function ChartModal({ chart, onClose }) {
    if (!chart) return null;

    const isAi = chart.type === "ai_smart";

    return (
        <div
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: "rgba(0, 0, 0, 0.95)",
                display: "flex",
                flexDirection: "column",
                zIndex: 9999,
            }}
        >
            {/* Header */}
            <div
                style={{
                    padding: "16px 24px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    borderBottom: "1px solid var(--border-color)",
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    {isAi && (
                        <span
                            style={{
                                fontSize: 12,
                                backgroundColor: "rgba(168, 85, 247, 0.2)",
                                padding: "4px 8px",
                                borderRadius: 4,
                                color: "#d8b4fe",
                            }}
                        >
                            🧠 AI Smart
                        </span>
                    )}
                    <h3 style={{ margin: 0, color: "var(--text-primary)" }}>
                        {chart.figure.layout.title?.text || "Expanded Chart"}
                    </h3>
                </div>
                <button
                    onClick={onClose}
                    style={{
                        background: "none",
                        border: "none",
                        fontSize: 24,
                        color: "var(--text-muted)",
                        cursor: "pointer",
                        padding: "4px 8px",
                    }}
                >
                    ✕
                </button>
            </div>

            {/* Chart Container */}
            <div
                style={{
                    flex: 1,
                    overflow: "auto",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "24px",
                }}
            >
                <div style={{ width: "100%", maxWidth: "1200px" }}>
                    <Plot
                        data={chart.figure.data}
                        layout={{
                            ...chart.figure.layout,
                            autosize: true,
                            height: "calc(100vh - 150px)",
                        }}
                        config={{
                            responsive: true,
                            displayModeBar: true,
                            displaylogo: false,
                            modeBarButtonsToRemove: ["lasso2d", "select2d"],
                        }}
                        useResizeHandler
                        style={{ width: "100%", height: "100%" }}
                    />
                </div>
            </div>
        </div>
    );
}

export default function Visualizations({ charts: rawData, isLoading }) {
    const [expandedChart, setExpandedChart] = useState(null);

    if (isLoading) return <LoadingSpinner text="Generating charts…" />;
    if (!rawData) return null;

    // Handle nested structure from version 2.1+
    const charts = rawData.charts || rawData;
    const version = rawData.version || "1.0";

    console.log(`Rendering Visualizations version: ${version}`);

    // Flatten all chart arrays into a renderable list
    const allCharts = [
        ...(charts.smart_visualizations || []),
        ...(charts.histograms || []),
        ...(charts.bar_charts || []),
        ...(charts.scatter_plots || []),
    ];

    return (
        <div className="fade-in">
            <div className="section-header">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                        <h2>📈 Visualizations</h2>
                        <p>Interactive charts generated from your dataset • Hover for tools • Click expand for fullscreen</p>
                    </div>
                    <span style={{ fontSize: 10, color: "var(--text-muted)", opacity: 0.5 }}>v{version}</span>
                </div>
            </div>

            {/* ── Correlation Heatmap (full width) ────────────── */}
            {charts.heatmap && (
                <div className="chart-card" style={{ marginBottom: 20, position: "relative" }}>
                    <button
                        onClick={() => setExpandedChart(charts.heatmap)}
                        style={{
                            position: "absolute",
                            top: 12,
                            right: 12,
                            background: "rgba(255, 255, 255, 0.1)",
                            border: "1px solid rgba(255, 255, 255, 0.2)",
                            color: "var(--text-muted)",
                            borderRadius: 4,
                            padding: "6px 12px",
                            cursor: "pointer",
                            fontSize: 12,
                            zIndex: 10,
                            transition: "all 0.2s",
                        }}
                        onMouseEnter={(e) => {
                            e.target.style.background = "rgba(255, 255, 255, 0.2)";
                            e.target.style.color = "var(--text-primary)";
                        }}
                        onMouseLeave={(e) => {
                            e.target.style.background = "rgba(255, 255, 255, 0.1)";
                            e.target.style.color = "var(--text-muted)";
                        }}
                    >
                        ↗ Expand
                    </button>
                    <Plot
                        data={charts.heatmap.figure.data}
                        layout={{
                            ...charts.heatmap.figure.layout,
                            autosize: true,
                            height: 500,
                        }}
                        config={{
                            responsive: true,
                            displayModeBar: true,
                            displaylogo: false,
                            modeBarButtonsToRemove: ["lasso2d", "select2d"],
                        }}
                        useResizeHandler
                        style={{ width: "100%" }}
                    />
                </div>
            )}

            {/* ── Other charts in a grid ─────────────────────── */}
            <div className="charts-grid">
                {allCharts.map((chart, i) => {
                    const isAi = chart.type === "ai_smart";
                    return (
                        <div key={i} className={`chart-card ${isAi ? "ai-highlight" : ""}`} style={{ position: "relative" }}>
                            <button
                                onClick={() => setExpandedChart(chart)}
                                style={{
                                    position: "absolute",
                                    top: 12,
                                    right: 12,
                                    background: "rgba(255, 255, 255, 0.1)",
                                    border: "1px solid rgba(255, 255, 255, 0.2)",
                                    color: "var(--text-muted)",
                                    borderRadius: 4,
                                    padding: "6px 12px",
                                    cursor: "pointer",
                                    fontSize: 12,
                                    zIndex: 10,
                                    transition: "all 0.2s",
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.background = "rgba(255, 255, 255, 0.2)";
                                    e.target.style.color = "var(--text-primary)";
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.background = "rgba(255, 255, 255, 0.1)";
                                    e.target.style.color = "var(--text-muted)";
                                }}
                            >
                                ↗ Expand
                            </button>
                            {isAi && (
                                <div className="ai-badge">
                                    <span>🧠 AI Smart Recommendation</span>
                                </div>
                            )}
                            <Plot
                                data={chart.figure.data}
                                layout={{
                                    ...chart.figure.layout,
                                    autosize: true,
                                    height: 360,
                                }}
                                config={{
                                    responsive: true,
                                    displayModeBar: true,
                                    displaylogo: false,
                                    modeBarButtonsToRemove: ["lasso2d", "select2d"],
                                }}
                                useResizeHandler
                                style={{ width: "100%" }}
                            />
                        </div>
                    );
                })}
            </div>

            {allCharts.length === 0 && !charts.heatmap && (
                <div className="glass-card" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                    No charts could be generated for this dataset.
                </div>
            )}

            {/* Fullscreen Modal */}
            {expandedChart && <ChartModal chart={expandedChart} onClose={() => setExpandedChart(null)} />}
        </div>
    );
}
