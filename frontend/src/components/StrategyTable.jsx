import { useMemo } from "react";
import styles from "./StrategyTable.module.css";
import Icon from "./Icon";

function PriceCell({ info, edge, formatMoney, onClick }) {
	const isObj = typeof info === "object" && info !== null;
	const price = isObj ? info?.recommended_price : undefined;
	const profit = isObj ? info?.expected_total_profit : undefined;

	if (price == null) {
		return <div className={styles.noData}>–</div>;
	}

	let cellClass = styles.clickableCell;
	if (edge === "high") cellClass += ` ${styles.edgeHigh}`;
	if (edge === "low") cellClass += ` ${styles.edgeLow}`;

	return (
		<div className={cellClass} onClick={onClick}>
			<div className={styles.priceValue}>{formatMoney(price)}</div>
			{profit != null && (
				<div className={styles.profitValue}>
					Profit: {formatMoney(profit)}
				</div>
			)}
			{edge && (
				<div
					className={styles.edgeIndicator}
					title={
						edge === "high"
							? "Model suggests increasing max price (profit rising at upper bound)"
							: "Model suggests lowering min price (profit rising near lower bound)"
					}
					aria-label={
						edge === "high"
							? "Edge case: increase max price"
							: "Edge case: lower min price"
					}
				>
					{edge === "high" ? "▲" : "▼"}
				</div>
			)}
		</div>
	);
}

export default function StrategyTable({ strategy, edgeCases, onCellClick }) {
	const months = useMemo(() => Object.keys(strategy || {}), [strategy]);
	const outlets = useMemo(
		() =>
			Array.from(
				new Set(months.flatMap((m) => Object.keys(strategy[m] || {})))
			).sort(),
		[months, strategy]
	);

	const formatMoney = (n) => `₹${Number(n).toFixed(2)}`;

	if (!strategy || months.length === 0) {
		// Render nothing or a placeholder if there's no data yet
		return null;
	}

	if (outlets.length === 0) {
		// This case is handled by the NoticeBanner in Dashboard.jsx
		return null;
	}

	return (
		<div className={`${styles.card} fade-in`}>
			<div className={styles.headerRow}>
				<div>
					<h2 className={styles.title}>Pricing Strategy</h2>
					<p className={styles.subtitle}>
						Recommended price per month and outlet
					</p>
				</div>
			</div>

			<div className={styles.tableWrap}>
				<table className={styles.table}>
					<thead>
						<tr>
							<th className={`${styles.th} ${styles.thMonth}`}>
								Month
							</th>
							{outlets.map((o) => (
								<th className={styles.th} key={o}>
									{o}
								</th>
							))}
						</tr>
					</thead>
					<tbody>
						{months.map((m) => (
							<tr key={m}>
								<td className={styles.tdMonth}>{m}</td>
								{outlets.map((o) => {
									const info = strategy?.[m]?.[o];
									const edge = edgeCases?.[m]?.[o];
									return (
										<td
											className={styles.td}
											key={`${m}-${o}`}
										>
											<PriceCell
												info={info}
												edge={edge}
												formatMoney={formatMoney}
												onClick={() =>
													onCellClick(m, o)
												}
											/>
										</td>
									);
								})}
							</tr>
						))}
					</tbody>
				</table>
			</div>

			<p className={styles.note}>
				<Icon name="help" size={14} />
				Click any cell to see the detailed price analysis chart.
			</p>
		</div>
	);
}
