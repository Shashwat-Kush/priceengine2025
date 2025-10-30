import { useMemo, useState } from "react";
import styles from "./StrategyTable.module.css";

function PriceCell({ info, formatMoney, onClick }) {
	const isObj = typeof info === "object" && info !== null;
	const price = isObj
		? info?.recommended_price
		: typeof info === "number"
		? info
		: undefined;
	const demand = isObj ? info?.expected_demand_units : undefined;
	const profit = isObj ? info?.expected_total_profit : undefined;
	const margin = isObj ? info?.profit_margin_percentage : undefined;

	const [show, setShow] = useState(false);

	if (price == null && !isObj) return <div>–</div>;

	return (
		<div
			className={`${styles.tooltipContainer} ${styles.clickableCell}`}
			onMouseEnter={() => setShow(true)}
			onMouseLeave={() => setShow(false)}
			onClick={onClick}
			title={
				isObj
					? `Price ${formatMoney(
							price
					  )} | Demand ${demand} | Profit ${formatMoney(profit)}`
					: undefined
			}
		>
			<div className={styles.priceValue}>
				{price != null ? formatMoney(price) : "–"}
			</div>
			{demand != null && profit != null && (
				<div style={{ color: "var(--text-muted)", fontSize: 12 }}>
					{`Demand: ${demand} • Profit: ${formatMoney(profit)}`}
				</div>
			)}
			{isObj && show && (
				<div className={styles.tooltipBubble}>
					<div className={styles.tooltipRow}>
						<span>Recommended price</span>
						<strong>
							{price != null ? formatMoney(price) : "N/A"}
						</strong>
					</div>
					{demand != null && (
						<div className={styles.tooltipRow}>
							<span>Expected demand</span>
							<strong>{demand}</strong>
						</div>
					)}
					{profit != null && (
						<div className={styles.tooltipRow}>
							<span>Expected profit</span>
							<strong>{formatMoney(profit)}</strong>
						</div>
					)}
					{margin != null && (
						<div className={styles.tooltipRow}>
							<span>Profit margin</span>
							<strong>{Number(margin).toFixed(2)}%</strong>
						</div>
					)}
				</div>
			)}
		</div>
	);
}

export default function StrategyTable({ strategy, onCellClick }) {
	const months = useMemo(() => Object.keys(strategy), [strategy]);
	const outlets = useMemo(
		() =>
			Array.from(
				new Set(months.flatMap((m) => Object.keys(strategy[m] || {})))
			).sort(),
		[months, strategy]
	);

	const formatMoney = (n) => `₹${Number(n).toFixed(2)}`;

	if (!months.length) return null;

	if (outlets.length === 0) {
		return (
			<div style={styles.card}>
				<div style={styles.headerRow}>
					<div>
						<h2 style={styles.title}>Best Pricing Strategy</h2>
						<p style={styles.subtitle}>
							No feasible prices found for any outlet given the
							current Min Margin and costs. Try lowering Min
							Margin, widening the price range, or adjusting
							costs.
						</p>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className={`${styles.card} fade-in`}>
			<div className={styles.headerRow}>
				<div>
					<h2 className={styles.title}>Best Pricing Strategy</h2>
					<p className={styles.subtitle}>
						Recommended price per Month × Outlet (profit-maximizing)
					</p>
				</div>
			</div>

			<div className={styles.tableWrap}>
				<table className={styles.table}>
					<thead>
						<tr>
							<th className={styles.th}>Month</th>
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
								<td className={styles.tdHeader}>{m}</td>
								{outlets.map((o) => {
									const info = strategy?.[m]?.[o];
									return (
										<td
											className={styles.td}
											key={`${m}-${o}`}
										>
											<PriceCell
												info={info}
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
				Tip: Hover a cell to view details. Click to see price analysis
				chart.
			</p>
		</div>
	);
}
