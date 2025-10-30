export default function NoticeBanner({ title = "Notice", messages = [] }) {
  if (!messages || messages.length === 0) return null;
  return (
    <div style={styles.wrap}>
      <div style={styles.header}>{title}</div>
      <ul style={styles.list}>
        {messages.map((m, i) => (
          <li key={i} style={styles.item}>{m}</li>
        ))}
      </ul>
    </div>
  );
}

const styles = {
  wrap: {
    width: "min(1100px, 96vw)",
    background: "#101a2f",
    color: "#e9eefc",
    border: "1px solid #223459",
    borderRadius: 10,
    padding: 12,
  },
  header: { fontWeight: 600, marginBottom: 6, color: "#b9c9f3" },
  list: { margin: 0, paddingLeft: 18 },
  item: { margin: "4px 0" },
};
