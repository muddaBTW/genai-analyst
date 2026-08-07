/**
 * Visualizations — renders Plotly charts from backend JSON specs with fullscreen support.
 */
import { useState } from "react";
import Plot from "react-plotly.js";
import LoadingSpinner from "./LoadingSpinner";
import ReactMarkdown from "react-markdown";
import { explainVisualization } from "../api/client";

function WhyThisChart({ chart, explanation, isLoading, onExplain, onClose }) {
    return (
        <div style={{ position: "absolute", left: 12, top: 12, zIndex: 10, maxWidth: "calc(100% - 120px)" }}>
            <button
                onClick={onExplain}
                disabled={isLoading}
                style={{
                    background: "rgba(99, 102, 241, 0.18)", border: "1px solid rgba(129, 140, 248, 0.45)",
                    color: "#c7d2fe", borderRadius: 4, padding: "6px 10px", cursor: isLoading ? "wait" : "pointer", fontSize: 12,
                }}
            >
                {isLoading ? "Explaining…" : explanation ? "Hide explanation" : "Why this chart?"}
            </button>
            {explanation && (
                <div className="glass-card" style={{ marginTop: 8, padding: "10px 12px", fontSize: 13, lineHeight: 1.45, position: "relative" }}>
                    <button
                        onClick={onClose}
                        aria-label="Close chart explanation"
                        title="Close explanation"
                        style={{ position: "absolute", top: 4, right: 6, background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: 18 }}
                    >
                        ×
                    </button>
                    <ReactMarkdown>{explanation}</ReactMarkdown>
                </div>
            )}
        </div>
    );
}

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
    const [explanations, setExplanations] = useState({});
    const [explaining, setExplaining] = useState({});

    const requestExplanation = async (key, chart) => {
        if (explaining[key]) return;
        if (explanations[key]) {
            setExplanations((current) => {
                const next = { ...current };
                delete next[key];
                return next;
            });
            return;
        }
        setExplaining((current) => ({ ...current, [key]: true }));
        try {
            const result = await explainVisualization(chart);
            setExplanations((current) => ({ ...current, [key]: result.explanation }));
        } catch (error) {
            setExplanations((current) => ({ ...current, [key]: `Unable to generate an explanation: ${error.message}` }));
        } finally {
            setExplaining((current) => ({ ...current, [key]: false }));
        }
    };

    const closeExplanation = (key) => setExplanations((current) => {
        const next = { ...current };
        delete next[key];
        return next;
    });

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
                    <WhyThisChart
                        chart={charts.heatmap}
                        explanation={explanations.heatmap}
                        isLoading={explaining.heatmap}
                        onExplain={() => requestExplanation("heatmap", charts.heatmap)}
                        onClose={() => closeExplanation("heatmap")}
                    />
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
                    const chartKey = `${chart.type}-${i}`;
                    return (
                        <div key={i} className={`chart-card ${isAi ? "ai-highlight" : ""}`} style={{ position: "relative" }}>
                            <WhyThisChart
                                chart={chart}
                                explanation={explanations[chartKey]}
                                isLoading={explaining[chartKey]}
                                onExplain={() => requestExplanation(chartKey, chart)}
                                onClose={() => closeExplanation(chartKey)}
                            />
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
