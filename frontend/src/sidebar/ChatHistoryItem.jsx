export default function ChatHistoryItem({ title, active, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "10px",
        borderRadius: "6px",
        cursor: "pointer",
        background: active ? "#111827" : "transparent",
        opacity: active ? 1 : 0.8,
      }}
    >
      {title}
    </div>
  );
}