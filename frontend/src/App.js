import React, { useMemo, useState } from "react";

const DEFAULT_PRICES = [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400];

function App() {
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
	// strategy is a nested object: { [month]: { [outlet]: bestPrice } }
	const months = Object.keys(strategy);
	const outlets = Array.from(
		new Set(months.flatMap((m) => Object.keys(strategy[m] || {})))
	).sort();

	return (
		<div style={styles.card}>
			<h2 style={styles.title}>Best Pricing Strategy</h2>
			<p style={styles.subtitle}>
				Price (₹) that maximizes revenue per Month × Outlet
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
									const v = strategy?.[m]?.[o];
									return (
										<td style={styles.td} key={`${m}-${o}`}>
											{v == null
												? "–"
												: `₹${v.toFixed(2)}`}
										</td>
									);
								})}
							</tr>
						))}
					</tbody>
				</table>
			</div>
			<p style={styles.note}>
				Tip: Use this as a monthly price schedule per outlet.
			</p>
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
};

export default App;
