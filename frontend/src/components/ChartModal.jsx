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
	edge,
	onClose,
	minMarginPercent,
}) {
	const formatMoney = (n) => `₹${Number(n).toFixed(2)}`;
	const sortedData = [...data].sort((a, b) => a.Price - b.Price);
	const chartData = sortedData.map((d) => ({
		price: round2(d.Price),
		demand: round2(d.Predicted_Demand),
		profit: round2(d.Total_Profit),
	}));

	// Build shaded ranges for negative-profit and below-min-margin regions
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
					<p className={styles.tooltipLabel}>
						Price: {formatMoney(payload[0].payload.price)}
					</p>
					<p className={`${styles.tooltipLine} ${styles.demand}`}>
						Demand: {payload[0].payload.demand} units
					</p>
					<p className={`${styles.tooltipLine} ${styles.profit}`}>
						Profit: {formatMoney(payload[0].payload.profit)}
					</p>
				</div>
			);
		}
		return null;
	};

	const edgeMessage =
		edge === "high"
			? "Profit is still increasing. Consider raising the max price."
			: edge === "low"
			? "Profit is increasing at the lower bound. Consider lowering the min price."
			: null;

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
							{month} — Recommended Price:{" "}
							<strong>
								{formatMoney(strategy.recommended_price)}
							</strong>
						</p>
					</div>
					<button
						className={styles.closeButton}
						onClick={onClose}
						aria-label="Close modal"
					>
						✕
					</button>
				</div>

				{edgeMessage && (
					<div
						className={`${styles.edgeBanner} ${
							edge === "high"
								? styles.edgeBannerHigh
								: styles.edgeBannerLow
						}`}
					>
						{edgeMessage}
					</div>
				)}

				<div className={styles.chartContainer}>
					<ResponsiveContainer width="100%" height={350}>
						<LineChart
							data={chartData}
							margin={{
								top: 20,
								right: 20,
								left: 20,
								bottom: 20,
							}}
						>
							<CartesianGrid
								strokeDasharray="3 3"
								stroke="var(--border)"
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
									value: "Demand",
									angle: -90,
									position: "insideLeft",
									fill: "var(--primary)",
								}}
							/>
							<YAxis
								yAxisId="right"
								orientation="right"
								stroke="var(--accent)"
								tick={{ fill: "var(--accent)" }}
								label={{
									value: "Profit",
									angle: 90,
									position: "insideRight",
									fill: "var(--accent)",
								}}
								tickFormatter={(value) =>
									`₹${(value / 1000).toFixed(1)}k`
								}
							/>
							<Tooltip content={<CustomTooltip />} />
							<Legend
								wrapperStyle={{ paddingTop: "20px" }}
								iconType="circle"
							/>
							<Line
								yAxisId="left"
								type="monotone"
								dataKey="demand"
								stroke="var(--primary)"
								strokeWidth={2}
								dot={false}
								activeDot={{ r: 6 }}
								name="Demand"
							/>
							<Line
								yAxisId="right"
								type="monotone"
								dataKey="profit"
								stroke="var(--accent)"
								strokeWidth={2}
								dot={false}
								activeDot={{ r: 6 }}
								name="Total Profit"
							/>
							<ReferenceLine
								x={round2(strategy.recommended_price)}
								stroke="var(--text)"
								strokeDasharray="4 4"
								label={{
									value: "Recommended",
									fill: "var(--text)",
									position: "insideTop",
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
								const isRec =
									Math.abs(
										Number(row.Price) -
											strategy.recommended_price
									) < 1e-9;

								let rowClass = styles.tr;
								if (neg) rowClass += ` ${styles.rowNeg}`;
								else if (lowM)
									rowClass += ` ${styles.rowLowMargin}`;
								if (isRec) rowClass += ` ${styles.rowRec}`;

								return (
									<tr key={row.Price} className={rowClass}>
										<td className={styles.td}>
											{formatMoney(row.Price)}
										</td>
										<td className={styles.td}>
											{round2(row.Predicted_Demand)}
										</td>
										<td className={styles.td}>
											{formatMoney(row.Revenue)}
										</td>
										<td className={styles.td}>
											{formatMoney(row.Total_Profit)}
										</td>
										<td className={styles.td}>
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
