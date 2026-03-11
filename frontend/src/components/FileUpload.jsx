/**
 * FileUpload — drag-and-drop / click file upload with visual feedback.
 */
import { useState, useRef } from "react";

export default function FileUpload({ onUpload, isLoading }) {
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef(null);

    const handleFile = (file) => {
        if (!file) return;
        const ext = file.name.split(".").pop().toLowerCase();
        if (!["csv", "xlsx", "xls"].includes(ext)) {
            alert("Please upload a CSV or Excel file.");
            return;
        }
        if (file.size > 50 * 1024 * 1024) {
            alert("File too large. Maximum 50 MB.");
            return;
        }
        onUpload(file);
    };

    const onDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files[0]);
    };

    return (
        <div>
            <div className="section-header">
                <h2>📂 Upload Dataset</h2>
                <p>Upload a CSV or Excel file to begin analysis</p>
            </div>

            <div
                className={`upload-zone glass-card ${dragOver ? "drag-over" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
            >
                <span className="upload-icon">⬆️</span>
                {isLoading ? (
                    <p className="upload-text">Processing file…</p>
                ) : (
                    <>
                        <p className="upload-text">
                            Drag &amp; drop your file here, or <strong style={{ color: "var(--accent-blue)" }}>browse</strong>
                        </p>
                        <p className="upload-hint">Supports CSV, XLSX, XLS — Max 50 MB</p>
                    </>
                )}
                <input
                    ref={inputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    style={{ display: "none" }}
                    onChange={(e) => handleFile(e.target.files[0])}
                />
            </div>
        </div>
    );
}
