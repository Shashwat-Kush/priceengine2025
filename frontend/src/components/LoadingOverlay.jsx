import { useEffect } from "react";
import styles from "./LoadingOverlay.module.css";

export default function LoadingOverlay({ show, text = "Loading…" }) {
	useEffect(() => {
		// No-op: keyframes defined in CSS module
	}, []);

	if (!show) return null;
	return (
		<div className={styles.backdrop}>
			<div className={styles.box}>
				<div className={styles.spinner} />
				<div>{text}</div>
			</div>
		</div>
	);
}
