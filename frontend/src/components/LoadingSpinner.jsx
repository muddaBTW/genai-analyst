/**
 * LoadingSpinner — reusable loading indicator.
 */
export default function LoadingSpinner({ text = "Loading..." }) {
    return (
        <div className="spinner-overlay fade-in">
            <div className="spinner" />
            <p className="spinner-text">{text}</p>
        </div>
    );
}
