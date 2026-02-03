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
    rendered = rendered.replace(
      c.sentence,
      c.sentence + marker
    );
  });

  const lines = rendered.split("\n").filter(Boolean);

  const lead = lines[0] || "";
  const body = lines.slice(1);

  // 🔥 Detect simple greetings (ChatGPT-style response)
  const isGreeting =
    lead.length <= 20 &&
    /^(hi|hello|hey|hai|hii|yo|sup|good morning|good evening)/i.test(
      lead.trim()
    );

  return (
    <div style={styles.aiRoot}>
      {/* Lead / Greeting */}
      <div
        style={{
          ...styles.lead,
          fontSize: isGreeting ? "14.5px" : styles.lead.fontSize,
          fontWeight: isGreeting ? 400 : styles.lead.fontWeight,
          marginBottom: isGreeting ? "6px" : styles.lead.marginBottom,
        }}
      >
        {lead}
      </div>

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

          if (line.startsWith("- ") || line.startsWith("•")) {
            return (
              <div key={i} style={styles.bullet}>
                {line.replace(/^[-•]\s*/, "")}
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
    marginBottom: "30px",
  },

  // 🔥 Flattened to ChatGPT-like scale
  lead: {
    fontSize: "15px",
    fontWeight: 500,
    marginBottom: "10px",
    color: "#f1f5f9",
    lineHeight: 1.6,
  },

  // Headings use weight, NOT size
  section: {
    fontSize: "14px",
    fontWeight: 600,
    marginTop: "14px",
    marginBottom: "4px",
    color: "#67e8f9",
    letterSpacing: "0.2px",
  },

  body: {
    fontSize: "14.5px",
    lineHeight: 1.65,
    color: "#e5e7eb",
  },

  text: {
    marginBottom: "6px",
  },

  bullet: {
    marginBottom: "6px",
    paddingLeft: "12px",
  },
};
