/**
 * Visualizations — renders Plotly charts from backend JSON specs.
 */
import Plot from "react-plotly.js";
import LoadingSpinner from "./LoadingSpinner";

export default function Visualizations({ charts, isLoading }) {
    if (isLoading) return <LoadingSpinner text="Generating charts…" />;
    if (!charts) return null;

    // Flatten all chart arrays into a renderable list
    const allCharts = [
        ...(charts.histograms || []),
        ...(charts.bar_charts || []),
        ...(charts.scatter_plots || []),
    ];

    return (
        <div className="fade-in">
            <div className="section-header">
                <h2>📈 Visualizations</h2>
                <p>Interactive charts generated from your dataset</p>
            </div>

            {/* ── Correlation Heatmap (full width) ────────────── */}
            {charts.heatmap && (
                <div className="chart-card" style={{ marginBottom: 20 }}>
                    <Plot
                        data={charts.heatmap.figure.data}
                        layout={{
                            ...charts.heatmap.figure.layout,
                            autosize: true,
                            height: 500,
                        }}
                        config={{ responsive: true, displayModeBar: false }}
                        useResizeHandler
                        style={{ width: "100%" }}
                    />
                </div>
            )}

            {/* ── Other charts in a grid ─────────────────────── */}
            <div className="charts-grid">
                {allCharts.map((chart, i) => (
                    <div key={i} className="chart-card">
                        <Plot
                            data={chart.figure.data}
                            layout={{
                                ...chart.figure.layout,
                                autosize: true,
                                height: 360,
                            }}
                            config={{ responsive: true, displayModeBar: false }}
                            useResizeHandler
                            style={{ width: "100%" }}
                        />
                    </div>
                ))}
            </div>

            {allCharts.length === 0 && !charts.heatmap && (
                <div className="glass-card" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                    No charts could be generated for this dataset.
                </div>
            )}
        </div>
    );
}
