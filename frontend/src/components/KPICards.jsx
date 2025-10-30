import styles from "./KPICards.module.css";

function KPICard({ title, value, icon, color }) {
	return (
		<div className={styles.card}>
			<div
				className={styles.iconWrapper}
				style={{ backgroundColor: `var(--${color}-bg)` }}
			>
				<span
					className={styles.icon}
					style={{ color: `var(--${color})` }}
				>
					{icon}
				</span>
			</div>
			<div className={styles.content}>
				<p className={styles.title}>{title}</p>
				<p className={styles.value}>{value}</p>
			</div>
		</div>
	);
}

export default function KPICards({ meta, strategy }) {
	if (!meta && !strategy) return null;

	const kpis = [];

	if (strategy) {
		const prices = Object.values(strategy)
			.flatMap((outlets) => Object.values(outlets))
			.map((s) => s?.recommended_price)
			.filter(Boolean);

		if (prices.length > 0) {
			const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
			kpis.push({
				title: "Avg. Recommended Price",
				value: `₹${avgPrice.toFixed(2)}`,
				icon: "💰",
				color: "primary",
			});
		}
	}

	if (meta) {
		const totalProfit = meta.expected_total_profit;
		if (totalProfit != null) {
			kpis.push({
				title: "Est. Total Profit",
				value: `₹${totalProfit.toLocaleString()}`,
				icon: "📈",
				color: "accent",
			});
		}
	}

	if (strategy) {
		const outletCount = new Set(
			Object.values(strategy).flatMap((outlets) => Object.keys(outlets))
		).size;
		if (outletCount > 0) {
			kpis.push({
				title: "Outlets Optimized",
				value: outletCount,
				icon: "🏪",
				color: "warning",
			});
		}
	}

	if (kpis.length === 0) return null;

	return (
		<div className={styles.kpiContainer}>
			{kpis.map((kpi) => (
				<KPICard key={kpi.title} {...kpi} />
			))}
		</div>
	);
}
