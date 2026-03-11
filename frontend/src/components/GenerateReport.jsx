/**
 * GenerateReport — download analysis report as PDF or Markdown.
 */
import { useState } from "react";
import { downloadReport } from "../api/client";

export default function GenerateReport({ hasDataset }) {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("");

    const handleDownload = async (format) => {
        setLoading(true);
        setStatus(`Generating ${format.toUpperCase()} report…`);
        try {
            await downloadReport(format);
            setStatus(`✅ ${format.toUpperCase()} report downloaded!`);
        } catch (err) {
            setStatus(`⚠️ Error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fade-in">
            <div className="section-header">
                <h2>📝 Generate Report</h2>
                <p>Download a comprehensive AI-generated analysis report</p>
            </div>

            <div className="glass-card" style={{ textAlign: "center", padding: 48 }}>
                <p style={{ fontSize: 48, marginBottom: 16 }}>📄</p>
                <p style={{ color: "var(--text-secondary)", marginBottom: 8 }}>
                    Generate a full analysis report with dataset summary, key statistics,
                    AI insights, and recommendations.
                </p>

                <div className="report-options" style={{ justifyContent: "center" }}>
                    <button
                        className="btn btn-primary"
                        disabled={!hasDataset || loading}
                        onClick={() => handleDownload("markdown")}
                    >
                        📝 Download Markdown
                    </button>
                    <button
                        className="btn btn-primary"
                        disabled={!hasDataset || loading}
                        onClick={() => handleDownload("pdf")}
                    >
                        📕 Download PDF
                    </button>
                </div>

                {status && (
                    <p style={{ marginTop: 20, fontSize: 14, color: "var(--text-muted)" }}>
                        {status}
                    </p>
                )}
            </div>
        </div>
    );
}
