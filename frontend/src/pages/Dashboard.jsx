import { useMemo, useState } from "react";
import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
} from "recharts";

const DEFAULTS = {
	priceMin: 200,
	priceMax: 320,
	variableCost: 120,
	fixedCost: 1000,
	minMarginPercent: 10,
};

const round2 = (v) => (v == null ? null : Math.round(Number(v) * 100) / 100);

function Dashboard() {
	const [priceMin, setPriceMin] = useState(String(DEFAULTS.priceMin));
	const [priceMax, setPriceMax] = useState(String(DEFAULTS.priceMax));
	const [variableCost, setVariableCost] = useState(
		String(DEFAULTS.variableCost)
	);
	const [fixedCost, setFixedCost] = useState(String(DEFAULTS.fixedCost));
	const [minMarginPercent, setMinMarginPercent] = useState(
		String(DEFAULTS.minMarginPercent)
	);

	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [strategy, setStrategy] = useState(null);
	const [detailedAnalysis, setDetailedAnalysis] = useState(null);
	const [modalData, setModalData] = useState(null);

	const parsed = useMemo(() => {
		const pMin = Number(priceMin);
		const pMax = Number(priceMax);
		const vCost = Number(variableCost);
		const fCost = Number(fixedCost);
		const margin = Number(minMarginPercent);
		const valid =
			[pMin, pMax, vCost, fCost, margin].every((x) => !Number.isNaN(x)) &&
			pMin > 0 &&
			pMax > 0 &&
			pMax > pMin &&
			vCost >= 0 &&
			fCost >= 0 &&
			margin >= 0 &&
			margin <= 100;
		return { pMin, pMax, vCost, fCost, margin, valid };
	}, [priceMin, priceMax, variableCost, fixedCost, minMarginPercent]);

	const handleFetch = async () => {
		if (!parsed.valid) return;
		setLoading(true);
		setError("");
		setStrategy(null);
		setDetailedAnalysis(null);
		try {
			const res = await fetch(
				"http://127.0.0.1:8080/v1/optimize-price/",
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						price_min: parsed.pMin,
						price_max: parsed.pMax,
						variable_cost: parsed.vCost,
						fixed_cost: parsed.fCost,
						min_margin_percent: parsed.margin,
					}),
				}
			);
			if (!res.ok) throw new Error(`Request failed (${res.status})`);
			const data = await res.json();
			setStrategy(data.optimization_results || null);
			setDetailedAnalysis(data.detailed_analysis || null);
		} catch (e) {
			setError(e.message || "Something went wrong");
		} finally {
			setLoading(false);
		}
	};

	const handleCellClick = (month, outletId) => {
		if (!detailedAnalysis || !detailedAnalysis[month]) return;

		// Filter data for this specific outlet
		const outletData = detailedAnalysis[month].filter(
			(item) => item.Outlet_ID === outletId
		);

		if (outletData.length > 0) {
			setModalData({
				month,
				outletId,
				data: outletData,
				strategy: strategy[month][outletId],
			});
		}
	};

	const closeModal = () => setModalData(null);

	return (
		<div style={styles.page}>
			<div style={styles.card}>
				<h1 style={styles.title}>AI-Driven Price Optimization</h1>
				<p style={styles.subtitle}>
					Find profit-maximizing prices per month and outlet using
					your demand model.
				</p>

				<div
					style={{
						display: "grid",
						gridTemplateColumns: "repeat(2, 1fr)",
						gap: 12,
					}}
				>
					<div>
						<label style={styles.label} htmlFor="priceMin">
							Min Price (₹)
						</label>
						<input
							id="priceMin"
							style={styles.input}
							value={priceMin}
							onChange={(e) => setPriceMin(e.target.value)}
						/>
					</div>
					<div>
						<label style={styles.label} htmlFor="priceMax">
							Max Price (₹)
						</label>
						<input
							id="priceMax"
							style={styles.input}
							value={priceMax}
							onChange={(e) => setPriceMax(e.target.value)}
						/>
					</div>
					<div>
						<label style={styles.label} htmlFor="variableCost">
							Variable Cost per Unit (₹)
						</label>
						<input
							id="variableCost"
							style={styles.input}
							value={variableCost}
							onChange={(e) => setVariableCost(e.target.value)}
						/>
					</div>
					<div>
						<label style={styles.label} htmlFor="fixedCost">
							Fixed Cost (₹)
						</label>
						<input
							id="fixedCost"
							style={styles.input}
							value={fixedCost}
							onChange={(e) => setFixedCost(e.target.value)}
						/>
					</div>
					<div>
						<label style={styles.label} htmlFor="minMargin">
							Min Margin (%)
						</label>
						<input
							id="minMargin"
							style={styles.input}
							value={minMarginPercent}
							onChange={(e) =>
								setMinMarginPercent(e.target.value)
							}
						/>
					</div>
				</div>

				<button
					style={styles.button}
					onClick={handleFetch}
					disabled={loading || !parsed.valid}
				>
					{loading ? "Optimizing…" : "Get Best Strategy"}
				</button>
				{!parsed.valid && (
					<p style={styles.help}>
						Please enter valid numbers: priceMin &lt; priceMax,
						non-negative costs, margin between 0 and 100.
					</p>
				)}
				{error && <p style={styles.error}>Error: {error}</p>}
			</div>

			{strategy && (
				<StrategyTable
					strategy={strategy}
					onCellClick={handleCellClick}
				/>
			)}

			{modalData && (
				<ChartModal
					month={modalData.month}
					outletId={modalData.outletId}
					data={modalData.data}
					strategy={modalData.strategy}
					onClose={closeModal}
				/>
			)}
		</div>
	);
}

function StrategyTable({ strategy, onCellClick }) {
	// strategy is a nested object: { [month]: { [outlet]: { recommended_price, expected_demand_units, expected_total_profit } } }
	const months = Object.keys(strategy);
	const outlets = Array.from(
		new Set(months.flatMap((m) => Object.keys(strategy[m] || {})))
	).sort();

	const formatMoney = (n) => `₹${Number(n).toFixed(2)}`;

	return (
		<div style={styles.card}>
			<h2 style={styles.title}>Best Pricing Strategy</h2>
			<p style={styles.subtitle}>
				Recommended price per Month × Outlet (based on profit
				maximization)
			</p>
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

function PriceCell({ info, formatMoney, onClick }) {
	// Normalize shape: number or object
	const isObj = typeof info === "object" && info !== null;
	const price = isObj
		? info?.recommended_price
		: typeof info === "number"
		? info
		: undefined;
	const demand = isObj ? info?.expected_demand_units : undefined;
	const revenue = isObj ? info?.expected_revenue : undefined;
	const profit = isObj ? info?.expected_total_profit : undefined;
	const margin = isObj ? info?.profit_margin_percentage : undefined;

	const [show, setShow] = useState(false);

	if (price == null && !isObj) {
		return <div>–</div>;
	}

	return (
		<div
			style={{ ...styles.tooltipContainer, ...styles.clickableCell }}
			onMouseEnter={() => setShow(true)}
			onMouseLeave={() => setShow(false)}
			onClick={onClick}
		>
			<div>{price != null ? formatMoney(price) : "–"}</div>
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
					{revenue != null && (
						<div style={styles.tooltipRow}>
							<span>Expected revenue</span>
							<strong>{formatMoney(revenue)}</strong>
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

function ChartModal({ month, outletId, data, strategy, onClose }) {
	const formatMoney = (n) => `₹${Number(n).toFixed(2)}`;

	// Sort data by price for proper chart rendering
	const sortedData = [...data].sort((a, b) => a.Price - b.Price);

	// Format data for Recharts
	const chartData = sortedData.map((d) => ({
		price: round2(d.Price),
		demand: round2(d.Predicted_Demand),
		profit: round2(d.Total_Profit),
		revenue: round2(d.Revenue),
	}));

	// Custom tooltip for the chart
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
						Profit: ₹{payload[0].payload.profit.toLocaleString()}
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
						</LineChart>
					</ResponsiveContainer>
				</div>{" "}
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
							{sortedData.map((row) => (
								<tr key={row.Price}>
									<td style={styles.td}>
										{formatMoney(row.Price)}
									</td>
									<td style={styles.td}>
										{round2(row.Predicted_Demand)}
									</td>
									<td style={styles.td}>
										{formatMoney(row.Revenue)}
									</td>
									<td style={styles.td}>
										{formatMoney(row.Total_Profit)}
									</td>
									<td style={styles.td}>
										{row["Profit_Margin_%"]?.toFixed(1)}%
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
}

const styles = {
	page: {
		minHeight: "100vh",
		background: "#0b1220",
		color: "#e9eefc",
		padding: "32px",
		display: "flex",
		flexDirection: "column",
		gap: "24px",
		alignItems: "center",
	},
	card: {
		width: "min(1100px, 96vw)",
		background: "#121a2a",
		border: "1px solid #1f2a44",
		borderRadius: 12,
		padding: 24,
		boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
	},
	title: { fontSize: 22, marginBottom: 8 },
	subtitle: { color: "#9fb2d9", marginBottom: 16 },
	label: { display: "block", marginBottom: 8, color: "#c6d3f5" },
	input: {
		width: "100%",
		padding: 10,
		borderRadius: 8,
		border: "1px solid #263557",
		background: "#0e1524",
		color: "#e9eefc",
		marginBottom: 8,
		fontFamily: "inherit",
	},
	button: {
		background: "#4f7cff",
		border: 0,
		color: "white",
		padding: "10px 14px",
		borderRadius: 8,
		cursor: "pointer",
	},
	help: { marginTop: 10, color: "#d7e0f8" },
	error: { marginTop: 10, color: "#ff8e8e" },
	table: {
		width: "100%",
		borderCollapse: "collapse",
		marginTop: 16,
	},
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
	td: {
		padding: "10px 8px",
		borderBottom: "1px solid #1a2744",
	},
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
	clickableCell: {
		cursor: "pointer",
		transition: "background-color 0.2s",
	},
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
	modalTitle: {
		fontSize: 22,
		margin: 0,
		color: "#e9eefc",
	},
	modalSubtitle: {
		fontSize: 14,
		margin: "4px 0 0 0",
		color: "#9fb2d9",
	},
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
};

export default Dashboard;
