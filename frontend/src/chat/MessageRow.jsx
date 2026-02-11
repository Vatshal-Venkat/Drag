import { useState, useRef, useEffect } from "react";
import SourceCitations from "../components/SourceCitations";

/* ================================
   Similarity Color Mapping
================================ */
function getSimilarityColor(score) {
  if (score > 0.8) return "#16a34a";
  if (score >= 0.6) return "#facc15";
  return "#dc2626";
}

/* ================================
   Section Parser
================================ */
function parseSections(content) {
  const regex =
    /Section\s+\d+\s+\(Similarity:\s+([\d.]+)\)/g;
  const matches = [...content.matchAll(regex)];

  if (!matches.length) return null;

  const sections = [];

  for (let i = 0; i < matches.length; i++) {
    const start = matches[i].index;
    const end =
      i + 1 < matches.length
        ? matches[i + 1].index
        : content.length;

    const title = matches[i][0];
    const similarity = parseFloat(matches[i][1]);
    const body = content
      .slice(start + title.length, end)
      .trim();

    sections.push({ title, similarity, body });
  }

  return sections;
}

/* ================================
   Animated Expandable Section
================================ */
function AnimatedSection({ open, children }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;

    if (open) {
      const scrollHeight = ref.current.scrollHeight;
      ref.current.style.maxHeight = scrollHeight + "px";
      ref.current.style.opacity = 1;
    } else {
      ref.current.style.maxHeight = "0px";
      ref.current.style.opacity = 0;
    }
  }, [open]);

  return (
    <div
      ref={ref}
      style={{
        overflow: "hidden",
        maxHeight: 0,
        opacity: 0,
        transition:
          "max-height 0.35s ease, opacity 0.3s ease",
      }}
    >
      <div style={{ paddingTop: 10 }}>{children}</div>
    </div>
  );
}

/* ================================
   Main Component
================================ */
export default function MessageRow({
  role,
  content,
  citations = [],
  timestamp,
}) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [openSections, setOpenSections] = useState({});
  const [viewMode, setViewMode] = useState("structured");

  const fallback =
    content?.includes(
      "No comparable sections were found"
    );

  const sections =
    !isUser && !fallback
      ? parseSections(content || "")
      : null;

  /* Auto-expand high similarity sections */
  useEffect(() => {
    if (!sections) return;

    const autoOpen = {};
    sections.forEach((sec, i) => {
      if (sec.similarity > 0.85) {
        autoOpen[i] = true;
      }
    });

    setOpenSections(autoOpen);
  }, [content]);

  function toggleSection(i) {
    setOpenSections((prev) => ({
      ...prev,
      [i]: !prev[i],
    }));
  }

  function handleCopy() {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser
          ? "flex-end"
          : "flex-start",
        marginBottom: isUser ? 16 : 26,
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: isUser ? "12px 14px" : 0,
          background: isUser ? "#1f2933" : "transparent",
          color: "#e5e7eb",
          borderRadius: isUser ? 12 : 0,
          whiteSpace: "pre-wrap",
          lineHeight: 1.65,
        }}
      >
        {/* ================= USER ================= */}
        {isUser && <div>{content}</div>}

        {/* ================= ASSISTANT ================= */}
        {!isUser && (
          <>
            {/* View Toggle */}
            {sections && (
              <div style={styles.toggleRow}>
                <button
                  style={
                    viewMode === "structured"
                      ? styles.activeBtn
                      : styles.btn
                  }
                  onClick={() =>
                    setViewMode("structured")
                  }
                >
                  Structured
                </button>
                <button
                  style={
                    viewMode === "raw"
                      ? styles.activeBtn
                      : styles.btn
                  }
                  onClick={() => setViewMode("raw")}
                >
                  Raw
                </button>
              </div>
            )}

            {/* Fallback UI */}
            {fallback && (
              <div style={styles.fallback}>
                ⚠️ Documents do not have strongly
                matching sections.
                <br />
                Showing general comparison instead.
              </div>
            )}

            {/* Structured View */}
            {sections &&
              viewMode === "structured" &&
              sections.map((sec, i) => (
                <div key={i} style={styles.sectionBox}>
                  <div
                    style={styles.sectionHeader}
                    onClick={() => toggleSection(i)}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      <span
                        style={{
                          transform: openSections[i]
                            ? "rotate(90deg)"
                            : "rotate(0deg)",
                          transition:
                            "transform 0.25s ease",
                        }}
                      >
                        ▶
                      </span>

                      <strong>
                        {sec.title}
                      </strong>
                    </div>

                    <span
                      style={{
                        ...styles.badge,
                        background:
                          getSimilarityColor(
                            sec.similarity
                          ),
                      }}
                    >
                      {sec.similarity}
                    </span>
                  </div>

                  <AnimatedSection
                    open={openSections[i]}
                  >
                    {sec.body}
                  </AnimatedSection>
                </div>
              ))}

            {/* Raw View */}
            {(!sections ||
              viewMode === "raw") && (
              <div>{content}</div>
            )}

            {/* Copy */}
            <div
              style={styles.copy}
              onClick={handleCopy}
            >
              {copied ? "Copied" : "Copy"}
            </div>

            {/* Sources */}
            {citations.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={styles.sourceTitle}>
                  Sources used
                </div>
                <SourceCitations
                  sources={citations}
                />
              </div>
            )}
          </>
        )}

        {/* Timestamp */}
        {timestamp && isUser && (
          <div style={styles.timestamp}>
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
}

/* ================================
   Styles
================================ */
const styles = {
  toggleRow: {
    display: "flex",
    gap: 8,
    marginBottom: 10,
  },

  btn: {
    background: "#1e293b",
    border: "none",
    padding: "6px 10px",
    borderRadius: 8,
    color: "#94a3b8",
    cursor: "pointer",
  },

  activeBtn: {
    background:
      "linear-gradient(135deg,#00e5ff,#2979ff)",
    border: "none",
    padding: "6px 10px",
    borderRadius: 8,
    color: "#000",
    cursor: "pointer",
  },

  fallback: {
    background: "#1e293b",
    padding: 12,
    borderRadius: 10,
    marginBottom: 14,
    fontSize: 13,
    color: "#facc15",
  },

  sectionBox: {
    border: "1px solid #1e293b",
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    background: "#0f172a",
  },

  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    cursor: "pointer",
  },

  badge: {
    padding: "4px 8px",
    borderRadius: 8,
    fontSize: 12,
    color: "#000",
  },

  copy: {
    fontSize: 12,
    opacity: 0.6,
    marginTop: 8,
    cursor: "pointer",
  },

  sourceTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: "#9ca3af",
    marginBottom: 4,
    textTransform: "uppercase",
  },

  timestamp: {
    fontSize: 11,
    opacity: 0.45,
    marginTop: 6,
    textAlign: "right",
  },
};
