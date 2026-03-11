/**
 * AiInsights — displays AI-generated insights from Groq.
 */
import ReactMarkdown from "react-markdown";
import LoadingSpinner from "./LoadingSpinner";

export default function AiInsights({ insights, isLoading }) {
    if (isLoading) return <LoadingSpinner text="Generating AI insights…" />;
    if (!insights) return null;

    return (
        <div className="fade-in">
            <div className="section-header">
                <h2>🧠 AI Insights</h2>
                <p>Powered by Groq LLM — intelligent analysis of your dataset</p>
            </div>

            <div className="glass-card insights-content">
                <ReactMarkdown>{insights}</ReactMarkdown>
            </div>
        </div>
    );
}
