/**
 * AskQuestions — chat-style natural language Q&A about the dataset.
 */
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion } from "../api/client";

export default function AskQuestions({ hasDataset }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        const q = input.trim();
        if (!q || loading) return;

        setMessages((prev) => [...prev, { role: "user", text: q }]);
        setInput("");
        setLoading(true);

        try {
            const data = await askQuestion(q);
            setMessages((prev) => [...prev, { role: "ai", text: data.answer }]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "ai", text: `⚠️ Error: ${err.message}` },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="fade-in">
            <div className="section-header">
                <h2>💬 Ask Questions</h2>
                <p>Chat with your data using natural language</p>
            </div>

            <div className="glass-card chat-container">
                <div className="chat-messages">
                    {messages.length === 0 && (
                        <div style={{ margin: "auto", textAlign: "center", color: "var(--text-muted)" }}>
                            <p style={{ fontSize: 40, marginBottom: 12 }}>💡</p>
                            <p>Try asking:</p>
                            <p style={{ color: "var(--accent-purple)", marginTop: 8 }}>
                                "Which column has the most missing values?"
                            </p>
                            <p style={{ color: "var(--accent-cyan)", marginTop: 4 }}>
                                "Show the relationship between revenue and profit"
                            </p>
                            <p style={{ color: "var(--accent-pink)", marginTop: 4 }}>
                                "Are there any anomalies in the data?"
                            </p>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} className={`chat-bubble ${msg.role}`}>
                            {msg.role === "ai" ? (
                                <ReactMarkdown>{msg.text}</ReactMarkdown>
                            ) : (
                                msg.text
                            )}
                        </div>
                    ))}

                    {loading && (
                        <div className="chat-bubble ai" style={{ opacity: 0.6 }}>
                            <em>Thinking…</em>
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>

                <div className="chat-input-bar">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={hasDataset ? "Ask anything about your data…" : "Upload a dataset first"}
                        disabled={!hasDataset || loading}
                    />
                    <button
                        className="btn btn-primary"
                        onClick={handleSend}
                        disabled={!hasDataset || loading || !input.trim()}
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}
