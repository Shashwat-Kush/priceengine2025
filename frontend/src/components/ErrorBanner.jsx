export default function ErrorBanner({ message, onClose }) {
	if (!message) return null;
	return (
		<div style={styles.wrap}>
			<div style={styles.icon}>⚠️</div>
			<div style={{ flex: 1 }}>{message}</div>
			{onClose && (
				<button style={styles.btn} onClick={onClose}>
					Dismiss
				</button>
			)}
		</div>
	);
}

const styles = {
	wrap: {
		width: "min(1100px, 96vw)",
		background: "#2b1f24",
		color: "#ffd2d2",
		border: "1px solid #532b33",
		borderRadius: 10,
		padding: 12,
		display: "flex",
		alignItems: "center",
		gap: 10,
	},
	icon: { fontSize: 18 },
	btn: {
		background: "transparent",
		border: "1px solid #7a3e48",
		color: "#ffd2d2",
		padding: "6px 10px",
		borderRadius: 8,
		cursor: "pointer",
	},
};
