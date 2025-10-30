import { useMemo, useState } from "react";

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
			style={{ ...styles.tooltipContainer, ...styles.clickableCell }}
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
			<div style={styles.priceValue}>
				{price != null ? formatMoney(price) : "–"}
			</div>
			{demand != null && profit != null && (
				<div style={{ color: "#9fb2d9", fontSize: 12 }}>
					{`Demand: ${demand} • Profit: ${formatMoney(profit)}`}
				</div>
			)}
			{isObj && show && (
				<div style={styles.tooltipBubble}>
					<div style={styles.tooltipRow}>
						<span>Recommended price</span>
						<strong>
							{price != null ? formatMoney(price) : "N/A"}
						</strong>
					</div>
					{demand != null && (
						<div style={styles.tooltipRow}>
							<span>Expected demand</span>
							<strong>{demand}</strong>
						</div>
					)}
					{profit != null && (
						<div style={styles.tooltipRow}>
							<span>Expected profit</span>
							<strong>{formatMoney(profit)}</strong>
						</div>
					)}
					{margin != null && (
						<div style={styles.tooltipRow}>
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
		<div style={styles.card}>
			<div style={styles.headerRow}>
				<div>
					<h2 style={styles.title}>Best Pricing Strategy</h2>
					<p style={styles.subtitle}>
						Recommended price per Month × Outlet (profit-maximizing)
					</p>
				</div>
			</div>

			<div style={{ overflowX: "auto" }}>
				<table style={styles.table}>
					<thead>
						<tr>
							<th style={styles.th}>Month</th>
							{outlets.map((o) => (
								<th style={styles.th} key={o}>
									{o}
								</th>
							))}
						</tr>
					</thead>
					<tbody>
						{months.map((m) => (
							<tr key={m}>
								<td style={styles.tdHeader}>{m}</td>
								{outlets.map((o) => {
									const info = strategy?.[m]?.[o];
									return (
										<td style={styles.td} key={`${m}-${o}`}>
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

			<p style={styles.note}>
				Tip: Hover a cell to view details. Click to see price analysis
				chart.
			</p>
		</div>
	);
}

const styles = {
	card: {
		width: "min(1100px, 96vw)",
		background: "#121a2a",
		border: "1px solid #1f2a44",
		borderRadius: 12,
		padding: 24,
		boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
	},
	headerRow: {
		display: "flex",
		alignItems: "center",
		justifyContent: "space-between",
		gap: 12,
		marginBottom: 8,
	},
	title: { fontSize: 20, margin: 0 },
	subtitle: { color: "#9fb2d9", marginTop: 6 },
	table: { width: "100%", borderCollapse: "collapse", marginTop: 8 },
	th: {
		textAlign: "left",
		borderBottom: "1px solid #263557",
		padding: "10px 8px",
		position: "sticky",
		top: 0,
		background: "#121a2a",
		zIndex: 1,
	},
	tdHeader: {
		padding: "10px 8px",
		borderRight: "1px solid #263557",
		whiteSpace: "nowrap",
		fontWeight: 600,
	},
	td: { padding: "10px 8px", borderBottom: "1px solid #1a2744" },
	note: { marginTop: 10, color: "#9fb2d9" },
	tooltipContainer: { position: "relative", display: "inline-block" },
	tooltipBubble: {
		position: "absolute",
		top: "calc(100% + 6px)",
		left: 0,
		background: "#0e1524",
		border: "1px solid #263557",
		borderRadius: 8,
		padding: 10,
		minWidth: 220,
		boxShadow: "0 8px 20px rgba(0,0,0,0.35)",
		zIndex: 5,
	},
	tooltipRow: {
		display: "flex",
		alignItems: "center",
		justifyContent: "space-between",
		gap: 12,
		fontSize: 12,
		padding: "4px 0",
		borderBottom: "1px dashed #263557",
	},
	clickableCell: { cursor: "pointer", transition: "background-color 0.2s" },
	priceValue: { fontWeight: 600 },
};
