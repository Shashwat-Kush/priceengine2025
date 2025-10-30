import styles from "./LoadingOverlay.module.css";
import Icon from "./Icon";

export default function LoadingOverlay({ show, text = "Loading..." }) {
	if (!show) return null;
	return (
		<div className={styles.backdrop} aria-modal="true" role="dialog">
			<div className={styles.box}>
				<div className={styles.spinnerContainer}>
					<Icon name="logo" size={24} />
				</div>
				<div className={styles.text}>{text}</div>
			</div>
		</div>
	);
}
