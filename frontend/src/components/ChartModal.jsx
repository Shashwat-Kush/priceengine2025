import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
	ReferenceLine,
	ReferenceArea,
} from "recharts";
import styles from "./ChartModal.module.css";

const round2 = (v) => (v == null ? null : Math.round(Number(v) * 100) / 100);

export default function ChartModal({
	month,
	outletId,
	data,
	strategy,
	onClose,
	minMarginPercent,
}) {
	const formatMoney = (n) => `₹${Number(n).toFixed(2)}`;
	const sortedData = [...data].sort((a, b) => a.Price - b.Price);
	const chartData = sortedData.map((d) => ({
		price: round2(d.Price),
		demand: round2(d.Predicted_Demand),
		profit: round2(d.Total_Profit),
		revenue: round2(d.Revenue),
	}));

	// Simple local edge signal for this outlet/month
	let edgeBadge = null;
	if (sortedData.length >= 2) {
		const maxPrice = Number(sortedData[sortedData.length - 1].Price);
		const maxProfit = Number(
			sortedData[sortedData.length - 1].Total_Profit
		);
		const prevMaxProfit = Number(
			sortedData[sortedData.length - 2].Total_Profit
		);
		const minPrice = Number(sortedData[0].Price);
		const minProfit = Number(sortedData[0].Total_Profit);
		const nextMinProfit = Number(sortedData[1].Total_Profit);
		const rec = Number(strategy?.recommended_price);
		if (
			Math.abs(rec - maxPrice) < 1e-6 &&
			maxProfit > prevMaxProfit + 1e-9
		) {
			edgeBadge = {
				text: "Edge optimum (rising ↑): consider higher Max Price",
				color: "var(--accent)",
			};
		} else if (
			Math.abs(rec - minPrice) < 1e-6 &&
			minProfit > nextMinProfit + 1e-9
		) {
			edgeBadge = {
				text: "Edge optimum (rising ↓): consider lower Min Price",
				color: "var(--warning)",
			};
		}
	}

	// Build shaded ranges for negative-profit and below-min-margin (but non-negative profit) regions
	const negProfitRanges = [];
	const lowMarginRanges = [];
	let currNegStart = null;
	let currLMStart = null;

	const isNeg = (row) => Number(row.Total_Profit) < 0;
	const isLowMargin = (row) =>
		Number(row["Profit_Margin_%"]) < Number(minMarginPercent);

	for (let i = 0; i < sortedData.length; i++) {
		const row = sortedData[i];
		const price = Number(row.Price);

		if (isNeg(row)) {
			if (currNegStart == null) currNegStart = price;
		} else if (currNegStart != null) {
			negProfitRanges.push({
				x1: currNegStart,
				x2: Number(sortedData[i - 1].Price),
			});
			currNegStart = null;
		}

		if (!isNeg(row) && isLowMargin(row)) {
			if (currLMStart == null) currLMStart = price;
		} else if (currLMStart != null) {
			lowMarginRanges.push({
				x1: currLMStart,
				x2: Number(sortedData[i - 1].Price),
			});
			currLMStart = null;
		}
	}
	if (currNegStart != null)
		negProfitRanges.push({
			x1: currNegStart,
			x2: Number(sortedData[sortedData.length - 1].Price),
		});
	if (currLMStart != null)
		lowMarginRanges.push({
			x1: currLMStart,
			x2: Number(sortedData[sortedData.length - 1].Price),
		});

	const CustomTooltip = ({ active, payload }) => {
		if (active && payload && payload.length) {
			return (
				<div className={styles.chartTooltip}>
					<p style={{ margin: 0, marginBottom: 4, fontWeight: 600 }}>
						Price: ₹{payload[0].payload.price}
					</p>
					<p
						style={{
							margin: 0,
							color: "var(--primary)",
							fontSize: 13,
						}}
					>
						Demand: {payload[0].payload.demand} units
					</p>
					<p
						style={{
							margin: 0,
							color: "var(--danger)",
							fontSize: 13,
						}}
					>
						Profit: ₹
						{payload[0].payload.profit?.toLocaleString?.() ??
							payload[0].payload.profit}
					</p>
				</div>
			);
		}
		return null;
	};

	return (
		<div className={styles.modalOverlay} onClick={onClose}>
			<div
				className={styles.modalContent}
				onClick={(e) => e.stopPropagation()}
			>
				<div className={styles.modalHeader}>
					<div>
						<h2 className={styles.modalTitle}>
							Price Analysis: {outletId}
						</h2>
						<p className={styles.modalSubtitle}>
							{month} - Recommended Price:{" "}
							{formatMoney(strategy.recommended_price)}
						</p>
					</div>
					<button className={styles.closeButton} onClick={onClose}>
						✕
					</button>
				</div>
				{edgeBadge && (
					<div style={{ padding: "0 24px 8px 24px" }}>
						<span
							style={{
								display: "inline-block",
								padding: "6px 10px",
								borderRadius: 8,
								border: `1px solid ${edgeBadge.color}`,
								color: edgeBadge.color,
								background: "transparent",
								fontSize: 12,
							}}
						>
							{edgeBadge.text}
						</span>
					</div>
				)}
				<div className={styles.chartContainer}>
					<ResponsiveContainer width="100%" height={400}>
						<LineChart
							data={chartData}
							margin={{
								top: 20,
								right: 30,
								left: 20,
								bottom: 20,
							}}
						>
							<CartesianGrid
								strokeDasharray="3 3"
								stroke="var(--border-strong)"
							/>
							{negProfitRanges.map((r, idx) => (
								<ReferenceArea
									key={`neg-${idx}`}
									x1={r.x1}
									x2={r.x2}
									fill="var(--danger-bg)"
									stroke="var(--danger)"
									strokeOpacity={0.3}
								/>
							))}
							{lowMarginRanges.map((r, idx) => (
								<ReferenceArea
									key={`lm-${idx}`}
									x1={r.x1}
									x2={r.x2}
									fill="var(--warning-bg)"
									stroke="var(--warning)"
									strokeOpacity={0.3}
								/>
							))}
							<XAxis
								dataKey="price"
								stroke="var(--text-muted)"
								tick={{ fill: "var(--text-muted)" }}
								label={{
									value: "Price (₹)",
									position: "insideBottom",
									offset: -10,
									fill: "var(--text-muted)",
								}}
								tickFormatter={(value) => `₹${value}`}
							/>
							<YAxis
								yAxisId="left"
								stroke="var(--primary)"
								tick={{ fill: "var(--primary)" }}
								label={{
									value: "Demand (units)",
									angle: -90,
									position: "insideLeft",
									fill: "var(--primary)",
								}}
							/>
							<YAxis
								yAxisId="right"
								orientation="right"
								stroke="var(--danger)"
								tick={{ fill: "var(--danger)" }}
								label={{
									value: "Total Profit (₹)",
									angle: 90,
									position: "insideRight",
									fill: "var(--danger)",
								}}
								tickFormatter={(value) =>
									`₹${(value / 1000).toFixed(1)}k`
								}
							/>
							<Tooltip content={<CustomTooltip />} />
							<Legend
								wrapperStyle={{ paddingTop: "20px" }}
								iconType="line"
							/>
							<Line
								yAxisId="left"
								type="monotone"
								dataKey="demand"
								stroke="var(--primary)"
								strokeWidth={3}
								dot={{ fill: "var(--primary)", r: 5 }}
								activeDot={{ r: 7 }}
								name="Demand"
							/>
							<Line
								yAxisId="right"
								type="monotone"
								dataKey="profit"
								stroke="var(--danger)"
								strokeWidth={3}
								dot={{ fill: "var(--danger)", r: 5 }}
								activeDot={{ r: 7 }}
								name="Total Profit"
							/>
							<ReferenceLine
								x={round2(strategy.recommended_price)}
								stroke="var(--accent)"
								strokeDasharray="4 4"
								label={{
									value: "Recommended",
									fill: "var(--accent)",
									position: "top",
								}}
							/>
						</LineChart>
					</ResponsiveContainer>
				</div>
				<div className={styles.badgeRow}>
					<span className={`${styles.badge} ${styles.badgeNeg}`}>
						Negative profit
					</span>
					<span
						className={`${styles.badge} ${styles.badgeLowMargin}`}
					>
						Below min margin ({Number(minMarginPercent)}%)
					</span>
				</div>
				<div className={styles.dataTable}>
					<table className={styles.table}>
						<thead>
							<tr>
								<th className={styles.th}>Price</th>
								<th className={styles.th}>Demand</th>
								<th className={styles.th}>Revenue</th>
								<th className={styles.th}>Profit</th>
								<th className={styles.th}>Margin</th>
							</tr>
						</thead>
						<tbody>
							{sortedData.map((row) => {
								const neg = Number(row.Total_Profit) < 0;
								const lowM =
									!neg &&
									Number(row["Profit_Margin_%"]) <
										Number(minMarginPercent);
								const cellClass = neg
									? styles.rowNeg
									: lowM
									? styles.rowLowMargin
									: styles.td;
								return (
									<tr key={row.Price}>
										<td className={cellClass}>
											{formatMoney(row.Price)}
										</td>
										<td className={cellClass}>
											{round2(row.Predicted_Demand)}
										</td>
										<td className={cellClass}>
											{formatMoney(row.Revenue)}
										</td>
										<td className={cellClass}>
											{formatMoney(row.Total_Profit)}
										</td>
										<td className={cellClass}>
											{row["Profit_Margin_%"]?.toFixed(1)}
											%
										</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
}
