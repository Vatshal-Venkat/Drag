export default function Message({ role, content, citations = [] }) {
  /* ============================
     USER MESSAGE
     ============================ */
  if (role === "user") {
    return (
      <div className="user-card">
        <div className="user-content">{content}</div>
      </div>
    );
  }

  /* ============================
     ASSISTANT MESSAGE
     ============================ */

  let rendered = content;

  // Inject citation markers inline
  citations.forEach((c) => {
    const marker = ` [${c.source_ids.map((id) => id + 1).join(",")}]`;
    rendered = rendered.replace(c.sentence, c.sentence + marker);
  });

  const lines = rendered.split("\n").filter(Boolean);
  const title = lines[0];
  const body = lines.slice(1);

  return (
    <div style={styles.aiRoot}>
      {/* Title */}
      <div style={styles.title}>{title}</div>

      {/* Body */}
      <div style={styles.body}>
        {body.map((line, i) => {
          if (line.endsWith(":")) {
            return (
              <div key={i} style={styles.section}>
                {line.replace(":", "")}
              </div>
            );
          }

          return (
            <div key={i} style={styles.text}>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  aiRoot: {
    marginBottom: "28px",
  },
  title: {
    fontSize: "20px",
    fontWeight: 600,
    marginBottom: "14px",
    color: "#f8fafc",
  },
  section: {
    fontSize: "16px",
    fontWeight: 600,
    marginTop: "18px",
    marginBottom: "6px",
    color: "#67e8f9", // cyan-teal accent
  },
  body: {
    fontSize: "14.5px",
    lineHeight: 1.7,
    color: "#e5e7eb",
  },
  text: {
    marginBottom: "6px",
  },
};
