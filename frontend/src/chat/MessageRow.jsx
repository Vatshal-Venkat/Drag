import { useState, useRef, useEffect } from "react";
import SourceCitations from "../components/SourceCitations";

/* ================================
   Utilities
================================ */

function getSimilarityPercent(score) {
  return Math.min(Math.max(score * 100, 0), 100);
}

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
   Split Document A / B
================================ */

function splitDocuments(body) {
  const parts = body.split(/Document\s+[A-Z]:/g);

  if (parts.length < 3) {
    return { left: body, right: null };
  }

  return {
    left: parts[1]?.trim(),
    right: parts[2]?.trim(),
  };
}

/* ================================
   Animated Section
================================ */

function AnimatedSection({ open, glow, children }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;

    if (open) {
      const height = ref.current.scrollHeight;
      ref.current.style.maxHeight = height + "px";
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
          "max-height 0.4s ease, opacity 0.3s ease",
      }}
    >
      <div
        style={{
          paddingTop: 12,
          boxShadow: glow
            ? "0 0 18px rgba(0,229,255,0.25)"
            : "none",
          transition: "box-shadow 0.4s ease",
        }}
      >
        {children}
      </div>
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

  const [openSections, setOpenSections] =
    useState({});
  const [viewMode, setViewMode] =
    useState("structured");
  const [copied, setCopied] =
    useState(false);

  const sectionRefs = useRef({});

  const fallback =
    content?.includes(
      "No comparable sections were found"
    );

  const sections =
    !isUser && !fallback
      ? parseSections(content || "")
      : null;

  /* ================================
     Auto Open + Auto Scroll
  ================================= */

  useEffect(() => {
    if (!sections) return;

    const autoOpen = {};
    let firstHighIndex = null;

    sections.forEach((sec, i) => {
      if (sec.similarity > 0.85) {
        autoOpen[i] = true;
        if (firstHighIndex === null) {
          firstHighIndex = i;
        }
      }
    });

    setOpenSections(autoOpen);

    if (
      firstHighIndex !== null &&
      sectionRefs.current[firstHighIndex]
    ) {
      setTimeout(() => {
        sectionRefs.current[
          firstHighIndex
        ].scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 400);
    }
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

  /* ================================
     Render
  ================================= */

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser
          ? "flex-end"
          : "flex-start",
        marginBottom: isUser ? 16 : 28,
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: isUser ? "12px 14px" : 0,
          background: isUser
            ? "#1f2933"
            : "transparent",
          borderRadius: isUser ? 12 : 0,
          color: "#e5e7eb",
          whiteSpace: "pre-wrap",
        }}
      >
        {/* USER */}
        {isUser && <div>{content}</div>}

        {/* ASSISTANT */}
        {!isUser && (
          <>
            {/* Toggle */}
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
                  onClick={() =>
                    setViewMode("raw")
                  }
                >
                  Raw
                </button>
              </div>
            )}

            {/* Fallback */}
            {fallback && (
              <div style={styles.fallback}>
                ⚠️ No strong section
                alignment detected.
              </div>
            )}

            {/* Structured View */}
            {sections &&
              viewMode === "structured" &&
              sections.map((sec, i) => {
                const percent =
                  getSimilarityPercent(
                    sec.similarity
                  );

                const { left, right } =
                  splitDocuments(sec.body);

                return (
                  <div
                    key={i}
                    ref={(el) =>
                      (sectionRefs.current[
                        i
                      ] = el)
                    }
                    style={styles.sectionBox}
                  >
                    {/* Header */}
                    <div
                      style={
                        styles.sectionHeader
                      }
                      onClick={() =>
                        toggleSection(i)
                      }
                    >
                      <strong>
                        {sec.title}
                      </strong>

                      {/* Progress Bar */}
                      <div
                        style={
                          styles.progressWrap
                        }
                      >
                        <div
                          style={{
                            ...styles.progressFill,
                            width:
                              percent + "%",
                          }}
                        />
                      </div>
                    </div>

                    {/* Content */}
                    <AnimatedSection
                      open={
                        openSections[i]
                      }
                      glow={
                        openSections[i]
                      }
                    >
                      {/* Side-by-side layout */}
                      <div
                        style={
                          styles.diffLayout
                        }
                      >
                        <div
                          style={
                            styles.docColumn
                          }
                        >
                          {left}
                        </div>

                        {right && (
                          <div
                            style={
                              styles.docColumn
                            }
                          >
                            {right}
                          </div>
                        )}
                      </div>
                    </AnimatedSection>
                  </div>
                );
              })}

            {/* Raw */}
            {(!sections ||
              viewMode === "raw") && (
              <div>{content}</div>
            )}

            {/* Copy */}
            <div
              style={styles.copy}
              onClick={handleCopy}
            >
              {copied
                ? "Copied"
                : "Copy"}
            </div>

            {/* Sources */}
            {citations.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <div
                  style={
                    styles.sourceTitle
                  }
                >
                  Sources used
                </div>
                <SourceCitations
                  sources={citations}
                />
              </div>
            )}
          </>
        )}

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
    marginBottom: 12,
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
    color: "#facc15",
  },

  sectionBox: {
    border: "1px solid #1e293b",
    borderRadius: 12,
    padding: 14,
    marginBottom: 18,
    background: "#0f172a",
  },

  sectionHeader: {
    cursor: "pointer",
    marginBottom: 10,
  },

  progressWrap: {
    height: 6,
    background: "#1e293b",
    borderRadius: 999,
    marginTop: 6,
    overflow: "hidden",
  },

  progressFill: {
    height: "100%",
    background:
      "linear-gradient(90deg,#00e5ff,#2979ff)",
    transition: "width 0.4s ease",
  },

  diffLayout: {
    display: "grid",
    gridTemplateColumns:
      "1fr 1fr",
    gap: 20,
  },

  docColumn: {
    background: "#111827",
    padding: 12,
    borderRadius: 10,
    fontSize: 14,
    lineHeight: 1.6,
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
