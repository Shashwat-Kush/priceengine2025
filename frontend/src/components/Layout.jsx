import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import styles from "./Layout.module.css";

function Layout({ children }) {
	return (
		<div className={styles.layout}>
			<Sidebar />
			<div className={styles.main}>
				<Topbar />
				<main className={styles.content}>{children}</main>
			</div>
		</div>
	);
}

export default Layout;
