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
		const maxProfit = Number(sortedData[sortedData.length - 1].Total_Profit);
		const prevMaxProfit = Number(sortedData[sortedData.length - 2].Total_Profit);
	const minPrice = Number(sortedData[0].Price);
		const minProfit = Number(sortedData[0].Total_Profit);
		const nextMinProfit = Number(sortedData[1].Total_Profit);
		const rec = Number(strategy?.recommended_price);
		if (Math.abs(rec - maxPrice) < 1e-6 && maxProfit > prevMaxProfit + 1e-9) {
			edgeBadge = { text: "Edge optimum (rising ↑): consider higher Max Price", color: "#22d1aa" };
		} else if (Math.abs(rec - minPrice) < 1e-6 && minProfit > nextMinProfit + 1e-9) {
			edgeBadge = { text: "Edge optimum (rising ↓): consider lower Min Price", color: "#ffc107" };
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
				<div style={styles.chartTooltip}>
					<p style={{ margin: 0, marginBottom: 4, fontWeight: 600 }}>
						Price: ₹{payload[0].payload.price}
					</p>
					<p style={{ margin: 0, color: "#4f7cff", fontSize: 13 }}>
						Demand: {payload[0].payload.demand} units
					</p>
					<p style={{ margin: 0, color: "#ff6b9d", fontSize: 13 }}>
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
		<div style={styles.modalOverlay} onClick={onClose}>
			<div
				style={styles.modalContent}
				onClick={(e) => e.stopPropagation()}
			>
				<div style={styles.modalHeader}>
					<div>
						<h2 style={styles.modalTitle}>
							Price Analysis: {outletId}
						</h2>
						<p style={styles.modalSubtitle}>
							{month} - Recommended Price:{" "}
							{formatMoney(strategy.recommended_price)}
						</p>
					</div>
					<button style={styles.closeButton} onClick={onClose}>
						✕
					</button>
				</div>
				{edgeBadge && (
					<div style={{ padding: "0 24px 8px 24px" }}>
						<span style={{
							display: "inline-block",
							padding: "6px 10px",
							borderRadius: 8,
							border: `1px solid ${edgeBadge.color}`,
							color: edgeBadge.color,
							background: "rgba(34,209,170,0.08)",
							fontSize: 12,
						}}>{edgeBadge.text}</span>
					</div>
				)}
				<div style={styles.chartContainer}>
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
								stroke="#263557"
							/>
							{/* Shaded risk regions */}
							{negProfitRanges.map((r, idx) => (
								<ReferenceArea
									key={`neg-${idx}`}
									x1={r.x1}
									x2={r.x2}
									fill="#ff6b9d"
									fillOpacity={0.12}
									stroke="#ff6b9d"
									strokeOpacity={0.3}
								/>
							))}
							{lowMarginRanges.map((r, idx) => (
								<ReferenceArea
									key={`lm-${idx}`}
									x1={r.x1}
									x2={r.x2}
									fill="#ffc107"
									fillOpacity={0.12}
									stroke="#ffc107"
									strokeOpacity={0.3}
								/>
							))}
							<XAxis
								dataKey="price"
								stroke="#9fb2d9"
								tick={{ fill: "#9fb2d9" }}
								label={{
									value: "Price (₹)",
									position: "insideBottom",
									offset: -10,
									fill: "#c6d3f5",
								}}
								tickFormatter={(value) => `₹${value}`}
							/>
							<YAxis
								yAxisId="left"
								stroke="#4f7cff"
								tick={{ fill: "#4f7cff" }}
								label={{
									value: "Demand (units)",
									angle: -90,
									position: "insideLeft",
									fill: "#4f7cff",
								}}
							/>
							<YAxis
								yAxisId="right"
								orientation="right"
								stroke="#ff6b9d"
								tick={{ fill: "#ff6b9d" }}
								label={{
									value: "Total Profit (₹)",
									angle: 90,
									position: "insideRight",
									fill: "#ff6b9d",
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
								stroke="#4f7cff"
								strokeWidth={3}
								dot={{ fill: "#4f7cff", r: 5 }}
								activeDot={{ r: 7 }}
								name="Demand"
							/>
							<Line
								yAxisId="right"
								type="monotone"
								dataKey="profit"
								stroke="#ff6b9d"
								strokeWidth={3}
								dot={{ fill: "#ff6b9d", r: 5 }}
								activeDot={{ r: 7 }}
								name="Total Profit"
							/>
							<ReferenceLine
								x={round2(strategy.recommended_price)}
								stroke="#22d1aa"
								strokeDasharray="4 4"
								label={{
									value: "Recommended",
									fill: "#22d1aa",
									position: "top",
								}}
							/>
						</LineChart>
					</ResponsiveContainer>
				</div>
				<div style={styles.badgeRow}>
					<span
						style={{
							...styles.badge,
							background: "rgba(255,107,157,0.2)",
							borderColor: "#ff6b9d",
							color: "#ffb3c9",
						}}
					>
						Negative profit
					</span>
					<span
						style={{
							...styles.badge,
							background: "rgba(255,193,7,0.2)",
							borderColor: "#ffc107",
							color: "#ffe08a",
						}}
					>
						Below min margin ({Number(minMarginPercent)}%)
					</span>
				</div>
				<div style={styles.dataTable}>
					<table style={styles.table}>
						<thead>
							<tr>
								<th style={styles.th}>Price</th>
								<th style={styles.th}>Demand</th>
								<th style={styles.th}>Revenue</th>
								<th style={styles.th}>Profit</th>
								<th style={styles.th}>Margin</th>
							</tr>
						</thead>
						<tbody>
							{sortedData.map((row) => {
								const neg = Number(row.Total_Profit) < 0;
								const lowM =
									!neg &&
									Number(row["Profit_Margin_%"]) <
										Number(minMarginPercent);
								const cellStyle = neg
									? styles.rowNeg
									: lowM
									? styles.rowLowMargin
									: styles.td;
								return (
									<tr key={row.Price}>
										<td style={cellStyle}>
											{formatMoney(row.Price)}
										</td>
										<td style={cellStyle}>
											{round2(row.Predicted_Demand)}
										</td>
										<td style={cellStyle}>
											{formatMoney(row.Revenue)}
										</td>
										<td style={cellStyle}>
											{formatMoney(row.Total_Profit)}
										</td>
										<td style={cellStyle}>
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

const styles = {
	modalOverlay: {
		position: "fixed",
		top: 0,
		left: 0,
		right: 0,
		bottom: 0,
		background: "rgba(0, 0, 0, 0.7)",
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		zIndex: 1000,
		padding: "20px",
	},
	modalContent: {
		background: "#121a2a",
		border: "1px solid #1f2a44",
		borderRadius: 16,
		maxWidth: "900px",
		width: "100%",
		maxHeight: "90vh",
		overflow: "auto",
		boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
	},
	modalHeader: {
		display: "flex",
		alignItems: "center",
		justifyContent: "space-between",
		padding: "24px",
		borderBottom: "1px solid #1f2a44",
	},
	modalTitle: { fontSize: 22, margin: 0, color: "#e9eefc" },
	modalSubtitle: { fontSize: 14, margin: "4px 0 0 0", color: "#9fb2d9" },
	closeButton: {
		background: "transparent",
		border: "1px solid #263557",
		color: "#9fb2d9",
		fontSize: 24,
		width: 40,
		height: 40,
		borderRadius: 8,
		cursor: "pointer",
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		transition: "all 0.2s",
	},
	chartContainer: {
		padding: "24px",
		background: "#0e1524",
		borderRadius: 8,
		margin: "0 24px 24px 24px",
	},
	badgeRow: {
		display: "flex",
		gap: 8,
		padding: "0 24px 12px 24px",
	},
	badge: {
		display: "inline-flex",
		alignItems: "center",
		gap: 6,
		padding: "4px 8px",
		borderRadius: 8,
		border: "1px solid transparent",
		fontSize: 12,
	},
	chartTooltip: {
		background: "#0e1524",
		border: "1px solid #263557",
		borderRadius: 8,
		padding: 12,
		color: "#e9eefc",
	},
	dataTable: {
		padding: "0 24px 24px 24px",
		maxHeight: "300px",
		overflow: "auto",
	},
	table: { width: "100%", borderCollapse: "collapse", marginTop: 16 },
	th: {
		textAlign: "left",
		borderBottom: "1px solid #263557",
		padding: "10px 8px",
		position: "sticky",
		top: 0,
		background: "#121a2a",
		zIndex: 1,
	},
	td: { padding: "10px 8px", borderBottom: "1px solid #1a2744" },
	rowNeg: {
		padding: "10px 8px",
		borderBottom: "1px solid #1a2744",
		background: "#2b1f24",
		color: "#ffd2d2",
	},
	rowLowMargin: {
		padding: "10px 8px",
		borderBottom: "1px solid #1a2744",
		background: "#2a2513",
		color: "#ffe9b3",
	},
};
