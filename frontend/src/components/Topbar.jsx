import { ThemeToggle } from "../theme/ThemeContext";
import styles from "./Topbar.module.css";

export default function Topbar() {
	return (
		<header className={styles.topbar}>
			<div className={styles.left}>
				{/* Can add breadcrumbs or page title here later */}
			</div>
			<div className={styles.right}>
				<ThemeToggle />
				<div className={styles.user}>
					<span className={styles.avatar}>S</span>
					<span className={styles.userName}>Saharsh</span>
				</div>
			</div>
		</header>
	);
}
