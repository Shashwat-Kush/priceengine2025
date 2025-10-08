function Analytics() {
	return (
		<div style={styles.page}>
			<div style={styles.card}>
				<h1 style={styles.title}>Analytics</h1>
				<p style={styles.subtitle}>
					View detailed performance metrics and insights.
				</p>
				<div style={styles.placeholder}>
					<span style={styles.icon}>📈</span>
					<p style={styles.placeholderText}>
						Analytics features coming soon...
					</p>
					<p style={styles.placeholderSubtext}>
						Track historical pricing strategies, demand forecasts,
						and revenue trends.
					</p>
				</div>
			</div>
		</div>
	);
}

const styles = {
	page: {
		minHeight: "100vh",
		background: "#0b1220",
		color: "#e9eefc",
		padding: "32px",
		display: "flex",
		flexDirection: "column",
		gap: "24px",
		alignItems: "center",
	},
	card: {
		width: "min(1100px, 96vw)",
		background: "#121a2a",
		border: "1px solid #1f2a44",
		borderRadius: 12,
		padding: 24,
		boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
	},
	title: { fontSize: 22, marginBottom: 8 },
	subtitle: { color: "#9fb2d9", marginBottom: 16 },
	placeholder: {
		textAlign: "center",
		padding: "60px 20px",
		color: "#9fb2d9",
	},
	icon: {
		fontSize: 64,
		display: "block",
		marginBottom: 16,
	},
	placeholderText: {
		fontSize: 18,
		fontWeight: 500,
		color: "#c6d3f5",
		marginBottom: 8,
	},
	placeholderSubtext: {
		fontSize: 14,
		color: "#9fb2d9",
	},
};

export default Analytics;
