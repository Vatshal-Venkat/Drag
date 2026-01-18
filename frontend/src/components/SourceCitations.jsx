export default function SourceCitations({ sources }) {
  return (
    <div style={{ marginTop: 16 }}>
      <h4>Sources</h4>

      {sources.map((s, i) => (
        <div
          key={s.id}
          id={`source-${s.id}`}
          style={{
            fontSize: 12,
            padding: 10,
            border: "1px solid #ddd",
            marginBottom: 8,
            borderRadius: 4,
          }}
        >
          <div>
            <strong>[{i + 1}] {s.source}</strong>
            {s.page && <> — page {s.page}</>}
          </div>

          <div style={{ marginTop: 4 }}>
            Confidence: <strong>{Math.round(s.confidence * 100)}%</strong>
          </div>

          <div
            style={{
              marginTop: 6,
              color: "#555",
              fontStyle: "italic",
            }}
          >
            {s.text.slice(0, 200)}…
          </div>
        </div>
      ))}
    </div>
  );
}
