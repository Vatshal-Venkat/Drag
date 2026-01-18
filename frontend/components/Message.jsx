export default function Message({ role, content }) {
  return (
    <div
      style={{
        marginBottom: 12,
        textAlign: role === "user" ? "right" : "left",
      }}
    >
      <strong>{role === "user" ? "You" : "AI"}:</strong>
      <p>{content}</p>
    </div>
  );
}
