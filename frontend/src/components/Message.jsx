export default function Message({ role, content, citations = [] }) {
  if (role !== "assistant") {
    return <div style={{ marginBottom: 8 }}>{content}</div>;
  }

  let rendered = content;

  citations.forEach((c, i) => {
    const marker = ` [${c.source_ids.map((id) => id + 1).join(",")}]`;
    rendered = rendered.replace(c.sentence, c.sentence + marker);
  });

  return (
    <div style={{ marginBottom: 8, whiteSpace: "pre-wrap" }}>
      {rendered}
    </div>
  );
}
