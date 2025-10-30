import styles from "./ErrorBanner.module.css";
import Icon from "./Icon";

export default function ErrorBanner({ message, onClose }) {
	if (!message) return null;
	return (
		<div className={`${styles.wrap} fade-in`}>
			<div className={styles.icon}>
				<Icon name="alert" size={20} />
			</div>
			<div className={styles.message}>{message}</div>
			{onClose && (
				<button
					className={styles.btn}
					onClick={onClose}
					aria-label="Dismiss error"
				>
					<Icon name="close" size={16} />
				</button>
			)}
		</div>
	);
}
