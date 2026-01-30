export default function SourceCitations({ sources = [] }) {
  if (!sources.length) {
    return (
      <div className="sources">
        <p
          style={{
            opacity: 0.6,
            fontSize: 13,
            fontStyle: "italic",
          }}
        >
          No sources available for this response.
        </p>
      </div>
    );
  }

  return (
    <div className="sources">
      <h4
        style={{
          margin: "0 0 14px",
          fontSize: 12,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--accent-main)",
        }}
      >
        Sources Referenced
      </h4>

      {sources.map((s, i) => (
        <div
          key={s.id || i}
          style={{
            marginBottom: 16,
            paddingBottom: 14,
            borderBottom: "1px dashed var(--border-subtle)",
          }}
        >
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              marginBottom: 6,
              color: "var(--text-primary)",
            }}
          >
            [{i + 1}] {s.source}
            {s.page && (
              <span style={{ opacity: 0.6 }}>
                {" "}
                · Page {s.page}
              </span>
            )}
          </div>

          <div
            style={{
              fontSize: 12,
              lineHeight: 1.65,
              color: "var(--text-secondary)",
            }}
          >
            {s.text?.slice(0, 180)}…
          </div>
        </div>
      ))}
    </div>
  );
}
