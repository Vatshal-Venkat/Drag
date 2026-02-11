import { useState } from "react";
import SourceCitations from "../components/SourceCitations";

function getSimilarityColor(score) {
  if (score > 0.8) return "#16a34a";
  if (score >= 0.6) return "#facc15";
  return "#dc2626";
}

function parseSections(content) {
  const regex = /Section\s+\d+\s+\(Similarity:\s+([\d.]+)\)/g;
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
    const body = content.slice(start + title.length, end).trim();

    sections.push({ title, similarity, body });
  }

  return sections;
}

export default function MessageRow({
  role,
  content,
  citations = [],
  timestamp,
}) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [openSections, setOpenSections] = useState({});

  const sections = !isUser ? parseSections(content || "") : null;

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
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: isUser ? "16px" : "26px",
      }}
    >
      <div
        style={{
          maxWidth: isUser ? "70%" : "70%",
          padding: isUser ? "12px 14px" : "0px",
          background: isUser ? "#1f2933" : "transparent",
          color: "#e5e7eb",
          borderRadius: isUser ? "12px" : "0px",
          whiteSpace: "pre-wrap",
          lineHeight: 1.65,
        }}
      >
        {isUser && <div>{content}</div>}

        {!isUser && sections && (
          <div>
            {sections.map((sec, i) => (
              <div
                key={i}
                style={{
                  border: "1px solid #1e293b",
                  borderRadius: 10,
                  padding: 12,
                  marginBottom: 14,
                  background: "#0f172a",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    cursor: "pointer",
                  }}
                  onClick={() => toggleSection(i)}
                >
                  <strong>{sec.title}</strong>
                  <span
                    style={{
                      background: getSimilarityColor(
                        sec.similarity
                      ),
                      padding: "4px 8px",
                      borderRadius: 8,
                      fontSize: 12,
                      color: "#000",
                    }}
                  >
                    {sec.similarity}
                  </span>
                </div>

                {openSections[i] && (
                  <div style={{ marginTop: 10 }}>
                    {sec.body}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {!isUser && !sections && (
          <div>{content}</div>
        )}

        {!isUser && citations.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "#9ca3af",
                marginBottom: 4,
                textTransform: "uppercase",
              }}
            >
              Sources used
            </div>
            <SourceCitations sources={citations} />
          </div>
        )}

        {timestamp && isUser && (
          <div
            style={{
              fontSize: "11px",
              opacity: 0.45,
              marginTop: 6,
              textAlign: "right",
            }}
          >
            {timestamp}
          </div>
        )}

        {!isUser && (
          <div
            style={{
              fontSize: 12,
              opacity: 0.6,
              marginTop: 8,
              cursor: "pointer",
            }}
            onClick={handleCopy}
          >
            {copied ? "Copied" : "Copy"}
          </div>
        )}
      </div>
    </div>
  );
}
