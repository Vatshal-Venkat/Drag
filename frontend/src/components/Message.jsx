export default function Message({ role, content, citations = [] }) {
  /* ============================
     User message
     ============================ */
  if (role === "user") {
    return (
      <div className="user-card">
        <div className="user-content">
          {content}
        </div>
      </div>
    );
  }

  /* ============================
     Assistant message
     ============================ */

  let rendered = content;

  /* Inject citation markers inline (unchanged logic) */
  citations.forEach((c) => {
    const marker = ` [${c.source_ids.map((id) => id + 1).join(",")}]`;
    rendered = rendered.replace(c.sentence, c.sentence + marker);
  });

  return (
    <div className="ai-card">
      {/* Label */}
      <div className="ai-label">
        AI INSIGHT
      </div>

      {/* Content */}
      <div className="ai-content">
        {rendered}
      </div>
    </div>
  );
}
