import { useChatStore } from "../store/chatStore";

export default function ChatHistoryItem({ title, active, onClick, id }) {
  const summary = useChatStore(
    (s) => s.sessionSummaries[id]
  );
  const setHovered = useChatStore(
    (s) => s.setHoveredSession
  );

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(id)}
      onMouseLeave={() => setHovered(null)}
      style={{
        ...styles.item,
        background: active ? "#020617" : "transparent",
      }}
    >
      {active && <div style={styles.activeBar} />}
      <span style={styles.title}>{title}</span>

      {summary && (
        <div style={styles.preview}>
          {summary}
        </div>
      )}
    </div>
  );
}

const styles = {
  item: {
    position: "relative",
    padding: "10px 10px 10px 14px",
    borderRadius: "6px",
    cursor: "pointer",
    marginBottom: "6px",
  },
  title: {
    fontSize: 13,
    color: "#e5e7eb",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  preview: {
    marginTop: 6,
    fontSize: 11,
    color: "#9aa7b2",
    lineHeight: 1.4,
  },
  activeBar: {
    position: "absolute",
    left: 0,
    top: 6,
    bottom: 6,
    width: 3,
    borderRadius: 2,
    background: "linear-gradient(180deg, #00e5ff, #2979ff)",
  },
};
