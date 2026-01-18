export default function SourceCitations({ sources }) {
  return (
    <div style={{ marginTop: 20 }}>
      <h3>Sources</h3>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>
            <strong>{s.source}</strong>
            <p style={{ fontSize: 12 }}>{s.text.slice(0, 200)}…</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
