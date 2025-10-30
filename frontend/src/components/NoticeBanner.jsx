import styles from "./NoticeBanner.module.css";
import Icon from "./Icon";

export default function NoticeBanner({ title = "Notice", messages = [] }) {
	if (!messages || messages.length === 0) return null;
	return (
		<div className={`${styles.wrap} fade-in`}>
			<div className={styles.header}>
				<Icon name="info" size={16} />
				<h3 className={styles.title}>{title}</h3>
			</div>
			<ul className={styles.list}>
				{messages.map((m, i) => (
					<li key={i} className={styles.item}>
						{m}
					</li>
				))}
			</ul>
		</div>
	);
}
