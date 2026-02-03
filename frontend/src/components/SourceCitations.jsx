import { useState } from "react";

export default function SourceCitations({ sources = [] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="sources">
      <button
        onClick={() => setOpen(!open)}
        style={{
          fontSize: 12,
          background: "none",
          border: "none",
          color: "#67e8f9",
          cursor: "pointer",
          padding: 0,
          marginBottom: open ? 10 : 0,
        }}
      >
        {open
          ? "Hide source details ▲"
          : `View source details (${sources.length}) ▼`}
      </button>

      {open && (
        <div style={{ marginTop: 8 }}>
          {sources.map((s, i) => (
            <div
              key={s.id || i}
              style={{
                marginBottom: 14,
                paddingBottom: 12,
                borderBottom: "1px dashed var(--border-subtle)",
              }}
            >
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  marginBottom: 6,
                  color: "#e5e7eb",
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
                  lineHeight: 1.6,
                  opacity: 0.85,
                }}
              >
                {s.text?.slice(0, 200)}…
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
