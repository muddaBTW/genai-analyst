/**
 * DatasetOverview — metadata cards + data preview table + column types + missing values.
 */
import { useState } from "react";
import { buildIndex } from "../api/client";

  export default function DatasetOverview({ metadata, preview, analysis, datasetId }) {
    const [building, setBuilding] = useState(false);
    if (!metadata) return null;

    return (
        <div className="fade-in">
            <div className="section-header">
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                        <div>
                            <h2>📊 Dataset Overview</h2>
                            <p>Preview and metadata for your uploaded dataset</p>
                        </div>
                        <div style={{ display: "flex", gap: 8 }}>
                            <button
                                className="btn"
                                onClick={async () => {
                                    if (!confirm("Build the semantic vector index from the currently uploaded dataset?")) return;
                                    try {
                                        setBuilding(true);
                                         await buildIndex(datasetId);
                                        alert("Index built successfully.");
                                    } catch (err) {
                                        alert("Index build failed: " + err.message);
                                    } finally {
                                        setBuilding(false);
                                    }
                                }}
                                disabled={building}
                            >
                                {building ? "Building…" : "Build Index"}
                            </button>
                        </div>
                    </div>
            </div>

            {/* ── Metadata Cards ─────────────────────────────────── */}
            <div className="meta-grid">
                <div className="meta-card glass-card">
                    <div className="meta-value">{metadata.rows.toLocaleString()}</div>
                    <div className="meta-label">Rows</div>
                </div>
                <div className="meta-card glass-card">
                    <div className="meta-value">{metadata.columns}</div>
                    <div className="meta-label">Columns</div>
                </div>
                <div className="meta-card glass-card">
                    <div className="meta-value">{metadata.total_missing}</div>
                    <div className="meta-label">Missing Values</div>
                </div>
                <div className="meta-card glass-card">
                    <div className="meta-value">
                        {Object.values(metadata.column_types).filter((t) => t.startsWith("int") || t.startsWith("float")).length}
                    </div>
                    <div className="meta-label">Numeric Cols</div>
                </div>
            </div>

            {/* ── Column Types ───────────────────────────────────── */}
            <div className="glass-card" style={{ marginBottom: 20 }}>
                <h3 style={{ marginBottom: 12, fontSize: 16 }}>Column Types</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {metadata.column_names.map((col) => {
                        const dtype = metadata.column_types[col];
                        const isNum = dtype.startsWith("int") || dtype.startsWith("float");
                        return (
                            <span key={col} className={`type-badge ${isNum ? "numeric" : "categorical"}`}>
                                {col} <span style={{ opacity: 0.6 }}>({dtype})</span>
                            </span>
                        );
                    })}
                </div>
            </div>

            {/* ── Missing Values ─────────────────────────────────── */}
            {metadata.total_missing > 0 && analysis?.missing_analysis && (
                <div className="glass-card" style={{ marginBottom: 20 }}>
                    <h3 style={{ marginBottom: 12, fontSize: 16 }}>Missing Values Breakdown</h3>
                    {analysis.missing_analysis
                        .filter((m) => m.missing_count > 0)
                        .map((m) => (
                            <div key={m.column} style={{ marginBottom: 10 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                                    <span>{m.column}</span>
                                    <span style={{ color: "var(--accent-orange)" }}>
                                        {m.missing_count} ({m.missing_percent}%)
                                    </span>
                                </div>
                                <div className="missing-bar-bg">
                                    <div className="missing-bar-fill" style={{ width: `${m.missing_percent}%` }} />
                                </div>
                            </div>
                        ))}
                </div>
            )}

            {/* ── Data Preview Table ─────────────────────────────── */}
            <div className="glass-card">
                <h3 style={{ marginBottom: 12, fontSize: 16 }}>Data Preview (first 10 rows)</h3>
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                {metadata.column_names.map((col) => (
                                    <th key={col}>{col}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {preview.map((row, i) => (
                                <tr key={i}>
                                    {metadata.column_names.map((col) => (
                                        <td key={col}>{String(row[col] ?? "")}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
