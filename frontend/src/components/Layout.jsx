import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ThemeToggle } from "../theme/ThemeContext";
import styles from "./Layout.module.css";

function Layout({ children }) {
	const location = useLocation();
	const [open, setOpen] = useState(false);
	const isActive = (path) => location.pathname === path;

	return (
		<div className={styles.container}>
			{/* Mobile topbar */}
			<div className={styles.topbar}>
				<div className={styles.topbarRow}>
					<div className={styles.brandInline}>
						<button
							className={styles.hamburger}
							onClick={() => setOpen((s) => !s)}
							aria-label="Toggle menu"
						>
							☰
						</button>
						<strong>PriceEngine</strong>
					</div>
					<ThemeToggle />
				</div>
			</div>

			<nav
				className={`${styles.sidebar} ${
					open ? styles.sidebarOpen : ""
				}`}
				onClick={() => setOpen(false)}
			>
				<div className={styles.brand}>
					<h2 className={styles.brandTitle}>PriceEngine</h2>
					<p className={styles.brandSubtitle}>AI Pricing Platform</p>
				</div>
				<div className={styles.nav}>
					<Link
						to="/"
						className={`${styles.navLink} ${
							isActive("/") ? styles.navLinkActive : ""
						}`}
					>
						<span className={styles.navIcon}>📊</span>
						Dashboard
					</Link>
					<Link
						to="/analytics"
						className={`${styles.navLink} ${
							isActive("/analytics") ? styles.navLinkActive : ""
						}`}
					>
						<span className={styles.navIcon}>📈</span>
						Analytics
					</Link>
					<Link
						to="/settings"
						className={`${styles.navLink} ${
							isActive("/settings") ? styles.navLinkActive : ""
						}`}
					>
						<span className={styles.navIcon}>⚙️</span>
						Settings
					</Link>
				</div>
				<div style={{ marginTop: "auto", padding: "0 16px" }}>
					<ThemeToggle />
				</div>
			</nav>
			<main className={styles.main}>{children}</main>
		</div>
	);
}

export default Layout;
