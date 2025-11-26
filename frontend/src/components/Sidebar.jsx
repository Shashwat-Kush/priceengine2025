import { NavLink } from "react-router-dom";
import styles from "./Sidebar.module.css";

const links = [
	{ to: "/", label: "Dashboard", icon: "📊" },
	// { to: "/analytics", label: "Analytics", icon: "📈" },
	// { to: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar() {
	return (
		<nav className={styles.sidebar}>
			<div className={styles.logo}>
				<span role="img" aria-label="logo">
					📈
				</span>
				<span>AI Pricing</span>
			</div>
			<ul className={styles.navList}>
				{links.map((link) => (
					<li key={link.to}>
						<NavLink
							to={link.to}
							className={({ isActive }) =>
								`${styles.navLink} ${
									isActive ? styles.active : ""
								}`
							}
						>
							<span className={styles.icon}>{link.icon}</span>
							<span className={styles.label}>{link.label}</span>
						</NavLink>
					</li>
				))}
			</ul>
		</nav>
	);
}
