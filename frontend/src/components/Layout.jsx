import { Link, useLocation } from "react-router-dom";

function Layout({ children }) {
	const location = useLocation();

	const isActive = (path) => location.pathname === path;

	return (
		<div style={styles.container}>
			<nav style={styles.sidebar}>
				<div style={styles.brand}>
					<h2 style={styles.brandTitle}>PriceEngine</h2>
					<p style={styles.brandSubtitle}>AI Pricing Platform</p>
				</div>
				<div style={styles.nav}>
					<Link
						to="/"
						style={{
							...styles.navLink,
							...(isActive("/") ? styles.navLinkActive : {}),
						}}
					>
						<span style={styles.navIcon}>📊</span>
						Dashboard
					</Link>
					<Link
						to="/analytics"
						style={{
							...styles.navLink,
							...(isActive("/analytics")
								? styles.navLinkActive
								: {}),
						}}
					>
						<span style={styles.navIcon}>📈</span>
						Analytics
					</Link>
					<Link
						to="/settings"
						style={{
							...styles.navLink,
							...(isActive("/settings")
								? styles.navLinkActive
								: {}),
						}}
					>
						<span style={styles.navIcon}>⚙️</span>
						Settings
					</Link>
				</div>
			</nav>
			<main style={styles.main}>{children}</main>
		</div>
	);
}

const styles = {
	container: {
		display: "flex",
		minHeight: "100vh",
		background: "#0b1220",
	},
	sidebar: {
		width: 260,
		background: "#0e1524",
		borderRight: "1px solid #1f2a44",
		display: "flex",
		flexDirection: "column",
		padding: "24px 0",
	},
	brand: {
		padding: "0 24px 24px 24px",
		borderBottom: "1px solid #1f2a44",
		marginBottom: 24,
	},
	brandTitle: {
		fontSize: 24,
		fontWeight: 700,
		color: "#e9eefc",
		margin: 0,
		marginBottom: 4,
	},
	brandSubtitle: {
		fontSize: 12,
		color: "#9fb2d9",
		margin: 0,
		textTransform: "uppercase",
		letterSpacing: 1,
	},
	nav: {
		display: "flex",
		flexDirection: "column",
		gap: 4,
		padding: "0 12px",
	},
	navLink: {
		display: "flex",
		alignItems: "center",
		gap: 12,
		padding: "12px 16px",
		borderRadius: 8,
		color: "#9fb2d9",
		textDecoration: "none",
		fontSize: 14,
		fontWeight: 500,
		transition: "all 0.2s",
	},
	navLinkActive: {
		background: "#1a2744",
		color: "#4f7cff",
	},
	navIcon: {
		fontSize: 18,
	},
	main: {
		flex: 1,
		overflow: "auto",
	},
};

export default Layout;
