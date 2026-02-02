import { useState } from "react";

export default function SourceCitations({ sources = [] }) {
  const [open, setOpen] = useState(false);

  if (!sources.length) {
    return (
      <div className="sources">
        <p
          style={{
            opacity: 0.5,
            fontSize: 12,
            fontStyle: "italic",
            marginTop: 8,
          }}
        >
          No sources available.
        </p>
      </div>
    );
  }

  return (
    <div className="sources" style={{ marginTop: 12 }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          fontSize: 12,
          background: "none",
          border: "none",
          color: "#67e8f9",
          cursor: "pointer",
          padding: 0,
          marginBottom: open ? 12 : 0,
        }}
      >
        {open ? "Hide sources ▲" : `View sources (${sources.length}) ▼`}
      </button>

      {open && (
        <div>
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
                  opacity: 0.8,
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
