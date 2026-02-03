import { useState } from "react";

export default function SourceCitations({ sources = [] }) {
  const [open, setOpen] = useState(false);

  // ✅ NEW: graceful empty handling
  if (!sources || sources.length === 0) {
    return null;
  }

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
          display: "flex",               // ✅ NEW
          alignItems: "center",          // ✅ NEW
          gap: 6,                        // ✅ NEW
        }}
      >
        {/* ✅ NEW: professional toggle text */}
        {open
          ? "Hide sources"
          : `View sources (${sources.length})`}
        <span style={{ opacity: 0.6 }}>
          {open ? "▲" : "▼"}
        </span>
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
                  display: "flex",          // ✅ NEW
                  alignItems: "center",     // ✅ NEW
                  gap: 6,                   // ✅ NEW
                }}
              >
                <span>
                  [{i + 1}] {s.source}
                </span>

                {s.page && (
                  <span style={{ opacity: 0.6 }}>
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
