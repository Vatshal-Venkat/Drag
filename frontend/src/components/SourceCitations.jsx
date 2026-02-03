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
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        <span style={{ opacity: 0.85 }}>
          {open ? "Hide sources" : "View sources"}
        </span>
        <span style={{ opacity: 0.6 }}>
          ({sources.length})
        </span>
      </button>

      {open && (
        <div style={{ marginTop: 10 }}>
          {sources.map((s, i) => (
            <div
              key={s.id || i}
              style={{
                marginBottom: 14,
                paddingBottom: 12,
                borderBottom:
                  "1px dashed rgba(148,163,184,0.25)",
              }}
            >
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  marginBottom: 6,
                  color: "#e5e7eb",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span style={{ opacity: 0.6 }}>
                  [{i + 1}]
                </span>
                <span>{s.source}</span>
                {s.page && (
                  <span
                    style={{
                      opacity: 0.5,
                      fontSize: 12,
                    }}
                  >
                    · Page {s.page}
                  </span>
                )}
              </div>

              <div
                style={{
                  fontSize: 12,
                  lineHeight: 1.6,
                  opacity: 0.85,
                  color: "#cbd5f5",
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
