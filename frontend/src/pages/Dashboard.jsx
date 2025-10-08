import { useMemo, useState } from "react";

const DEFAULT_PRICES = [
	200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320,
];

function Dashboard() {
	const [priceInput, setPriceInput] = useState(DEFAULT_PRICES.join(", "));
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [strategy, setStrategy] = useState(null);

	const parsedPrices = useMemo(() => {
		return priceInput
			.split(/[,\s]+/)
			.map((v) => v.trim())
			.filter((v) => v.length > 0)
			.map((v) => Number(v))
			.filter((v) => !Number.isNaN(v) && v > 0);
	}, [priceInput]);

	const handleFetch = async () => {
		setLoading(true);
		setError("");
		setStrategy(null);
		try {
			const res = await fetch(
				"http://127.0.0.1:8080/v1/optimize-price/",
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ prices: parsedPrices }),
				}
			);
			if (!res.ok) throw new Error(`Request failed (${res.status})`);
			const data = await res.json();
			// Expected shape: { status, input_product_details, optimization_results }
			setStrategy(data.optimization_results || null);
		} catch (e) {
			setError(e.message || "Something went wrong");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div style={styles.page}>
			<div style={styles.card}>
				<h1 style={styles.title}>AI-Driven Price Optimization</h1>
				<p style={styles.subtitle}>
					Find revenue-maximizing prices per month and outlet using
					your demand model.
				</p>

				<label style={styles.label} htmlFor="prices">
					Candidate Prices (₹, comma or space separated)
				</label>
				<textarea
					id="prices"
					style={styles.textarea}
					rows={3}
					value={priceInput}
					onChange={(e) => setPriceInput(e.target.value)}
				/>

				<button
					style={styles.button}
					onClick={handleFetch}
					disabled={loading || parsedPrices.length === 0}
				>
					{loading ? "Optimizing…" : "Get Best Strategy"}
				</button>
				{parsedPrices.length === 0 && (
					<p style={styles.help}>
						Please enter at least one positive numeric price.
					</p>
				)}
				{error && <p style={styles.error}>Error: {error}</p>}
			</div>

			{strategy && <StrategyTable strategy={strategy} />}
		</div>
	);
}

function StrategyTable({ strategy }) {
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
											/>
										</td>
									);
								})}
							</tr>
						))}
					</tbody>
				</table>
			</div>
			<p style={styles.note}>Tip: Hover a cell to view all details.</p>
		</div>
	);
}

function PriceCell({ info, formatMoney }) {
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
			style={styles.tooltipContainer}
			onMouseEnter={() => setShow(true)}
			onMouseLeave={() => setShow(false)}
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
	textarea: {
		width: "100%",
		padding: 12,
		borderRadius: 8,
		border: "1px solid #263557",
		background: "#0e1524",
		color: "#e9eefc",
		marginBottom: 12,
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
};

export default Dashboard;
