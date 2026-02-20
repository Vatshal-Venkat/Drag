import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

const SIDEBAR_WIDTH = 260;
const DEFAULT_PANEL_WIDTH = 360;
const MIN_WIDTH = 260;
const MAX_WIDTH = 600;

export default function ChatContainer() {
  const messages = useChatStore((s) => s.messages);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const compareMode = useChatStore((s) => s.compareMode);
  const selectedDocuments = useChatStore((s) => s.selectedDocuments);
  const toggleDocumentSelection = useChatStore(
    (s) => s.toggleDocumentSelection
  );

  const hasMessages = messages.length > 0;
  const showPanel = compareMode && selectedDocuments.length >= 2;

  /* ===========================
     Panel State
  ============================ */

  const [collapsed, setCollapsed] = useState(false);
  const [panelWidth, setPanelWidth] = useState(DEFAULT_PANEL_WIDTH);
  const isResizing = useRef(false);

  function startResize() {
    isResizing.current = true;
  }

  function stopResize() {
    isResizing.current = false;
  }

  function resize(e) {
    if (!isResizing.current) return;

    const newWidth = window.innerWidth - e.clientX;

    if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
      setPanelWidth(newWidth);
    }
  }

  useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResize);

    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResize);
    };
  }, []);

  /* ===========================
     Extract Sections + Similarity
  ============================ */

  const similarityScores = messages
    .filter((m) => m.role === "assistant")
    .flatMap((m) => {
      const matches =
        m.content?.match(/Similarity:\s+([\d.]+)/g) || [];

      return matches.map((match) =>
        parseFloat(match.replace("Similarity:", ""))
      );
    });

  const high = similarityScores.filter((s) => s > 0.85).length;
  const medium = similarityScores.filter(
    (s) => s >= 0.6 && s <= 0.85
  ).length;
  const low = similarityScores.filter((s) => s < 0.6).length;

  const total = similarityScores.length || 1;

  /* ===========================
     Render
  ============================ */

  return (
    <div style={styles.container}>
      {/* MAIN CHAT */}
      <div
        style={{
          ...styles.inner,
          marginLeft: sidebarOpen
            ? `calc(50% - ${SIDEBAR_WIDTH / 2}px)`
            : "50%",
          transform: "translateX(-50%)",
        }}
      >
        {!hasMessages && (
          <div style={styles.emptyState}>
            <h1 style={styles.title}>
              What can I help you figure out?
            </h1>

            <div style={styles.inputWrapper}>
              <MessageInput hasMessages={false} />
            </div>
          </div>
        )}

        {hasMessages && (
          <>
            <div style={styles.messageArea}>
              <MessageList />
            </div>
            <MessageInput hasMessages />
          </>
        )}
      </div>

      {/* PANEL */}
      {showPanel && (
        <>
          {!collapsed && (
            <div
              style={{
                ...styles.resizeHandle,
                right: panelWidth,
              }}
              onMouseDown={startResize}
            />
          )}

          <div
            style={{
              ...styles.panel,
              width: panelWidth,
              transform: collapsed
                ? `translateX(${panelWidth}px)`
                : "translateX(0)",
            }}
          >
            {/* Collapse Toggle */}
            <div
              style={styles.collapseBtn}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? "⟨" : "⟩"}
            </div>

            {!collapsed && (
              <>
                <div style={styles.header}>
                  🔍 Comparison Mode
                </div>

                {/* Similarity Graph */}
                <div style={styles.section}>
                  <div style={styles.label}>
                    Similarity Distribution
                  </div>

                  <Bar
                    label="High"
                    value={high}
                    total={total}
                    color="#00e5ff"
                  />
                  <Bar
                    label="Medium"
                    value={medium}
                    total={total}
                    color="#facc15"
                  />
                  <Bar
                    label="Low"
                    value={low}
                    total={total}
                    color="#dc2626"
                  />
                </div>

                {/* Switch Docs */}
                <div style={styles.section}>
                  <div style={styles.label}>
                    Switch Documents
                  </div>

                  {selectedDocuments.map((doc) => (
                    <div key={doc} style={styles.docRow}>
                      <span>{doc}</span>

                      <button
                        style={styles.removeBtn}
                        onClick={() =>
                          toggleDocumentSelection(doc)
                        }
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ===========================
   Bar Component
=========================== */

function Bar({ label, value, total, color }) {
  const percent =
    Math.round((value / total) * 100) || 0;

  return (
    <div style={{ marginBottom: 8 }}>
      <div
        style={{
          fontSize: 12,
          marginBottom: 4,
        }}
      >
        {label} ({value})
      </div>

      <div
        style={{
          height: 6,
          background: "#1e293b",
          borderRadius: 999,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: percent + "%",
            background: color,
            transition: "width 0.4s ease",
          }}
        />
      </div>
    </div>
  );
}

/* ===========================
   Styles
=========================== */

const styles = {
  container: {
    height: "100vh",
    background: "#141418",
    position: "relative",
  },

  inner: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
  },

  messageArea: {
    flex: 1,
    overflowY: "auto",
  },

  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",   // ✅ FIX
    alignItems: "center",
    justifyContent: "center",
    gap: 24,
    textAlign: "center",
  },

  inputWrapper: {
    width: 600,
    maxWidth: "90%",
  },

  title: {
    fontSize: 26,
    color: "#e7ebef",
  },

  panel: {
    position: "fixed",
    right: 0,
    top: 0,
    height: "100vh",
    background:
      "linear-gradient(180deg,#0f172a,#0b1220)",
    borderLeft: "1px solid #1e293b",
    padding: 16,
    zIndex: 20,
    display: "flex",
    flexDirection: "column",
    gap: 18,
    transition: "transform 0.3s ease",
  },

  resizeHandle: {
    position: "fixed",
    top: 0,
    width: 6,
    height: "100vh",
    cursor: "col-resize",
    zIndex: 25,
  },

  collapseBtn: {
    cursor: "pointer",
    alignSelf: "flex-end",
    fontSize: 18,
    color: "#94a3b8",
  },

  header: {
    fontSize: 16,
    fontWeight: 600,
    color: "#67e8f9",
  },

  section: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },

  label: {
    fontSize: 12,
    textTransform: "uppercase",
    color: "#64748b",
  },

  docRow: {
    display: "flex",
    justifyContent: "space-between",
    background: "#1e293b",
    padding: "6px 10px",
    borderRadius: 6,
    fontSize: 13,
  },

  removeBtn: {
    background: "none",
    border: "none",
    color: "#f87171",
    cursor: "pointer",
  },
};