export default function SourceCitations({ sources }) {
  return (
    <div className="sources">
      <h4>Sources Referenced</h4>
      {sources.map((s, i) => (
        <div key={s.id} className="source-item">
          <div className="source-title">
            [{i + 1}] {s.source}
            {s.page && <span> · Page {s.page}</span>}
          </div>
          <div className="source-text">
            {s.text.slice(0, 180)}…
          </div>
        </div>
      ))}
    </div>
  );
}
