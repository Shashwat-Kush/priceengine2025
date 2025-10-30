import { useEffect } from "react";

export default function LoadingOverlay({ show, text = "Loading…" }) {
	useEffect(() => {
		// Inject keyframes for spinner animation once
		const id = "__loading_overlay_spin_keyframes__";
		if (!document.getElementById(id)) {
			const style = document.createElement("style");
			style.id = id;
			style.textContent = `@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`;
			document.head.appendChild(style);
		}
	}, []);

	if (!show) return null;
	return (
		<div style={styles.backdrop}>
			<div style={styles.box}>
				<div style={styles.spinner} />
				<div>{text}</div>
			</div>
		</div>
	);
}

const styles = {
	backdrop: {
		position: "fixed",
		inset: 0,
		background: "rgba(0,0,0,0.45)",
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		zIndex: 1100,
	},
	box: {
		background: "#121a2a",
		border: "1px solid #1f2a44",
		color: "#e9eefc",
		borderRadius: 12,
		padding: 20,
		display: "flex",
		alignItems: "center",
		gap: 12,
		boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
	},
	spinner: {
		width: 20,
		height: 20,
		borderRadius: "50%",
		border: "3px solid #263557",
		borderTopColor: "#4f7cff",
		animation: "spin 1s linear infinite",
	},
};
