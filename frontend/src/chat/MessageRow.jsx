export default function MessageRow({ role, content, timestamp }) {
  const isUser = role === "user";

  return (
    <div style={{ ...styles.row, justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div style={isUser ? styles.user : styles.agent}>
        <div>{content}</div>
        <div style={styles.time}>{timestamp}</div>
      </div>
    </div>
  );
}

const styles = {
  row: {
    display: "flex",
    marginBottom: "16px",
  },
  user: {
    background: "#111827",
    padding: "10px 14px",
    borderRadius: "10px",
    maxWidth: "70%",
  },
  agent: {
    maxWidth: "70%",
  },
  time: {
    fontSize: "11px",
    opacity: 0.5,
    marginTop: "4px",
  },
};