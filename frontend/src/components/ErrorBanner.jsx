import styles from "./ErrorBanner.module.css";

export default function ErrorBanner({ message, onClose }) {
	if (!message) return null;
	return (
		<div className={`${styles.wrap} fade-in`}>
			<div className={styles.icon}>⚠️</div>
			<div style={{ flex: 1 }}>{message}</div>
			{onClose && (
				<button className={styles.btn} onClick={onClose}>
					Dismiss
				</button>
			)}
		</div>
	);
}
