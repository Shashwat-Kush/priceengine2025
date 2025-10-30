import { useMemo, useState } from "react";
import InputsPanel from "../components/InputsPanel";
import StrategyTable from "../components/StrategyTable";
import ChartModal from "../components/ChartModal";
import LoadingOverlay from "../components/LoadingOverlay";
import ErrorBanner from "../components/ErrorBanner";
import NoticeBanner from "../components/NoticeBanner";

const DEFAULTS = {
	priceMin: 200,
	priceMax: 320,
	variableCost: 120,
	fixedCost: 1000,
	minMarginPercent: 10,
};

// no-op helper here; charts handle formatting inside components

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
	const [showAdvanced, setShowAdvanced] = useState(false);
	const [rounds, setRounds] = useState(2);
	const [pointsPerRound, setPointsPerRound] = useState(21);

	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [strategy, setStrategy] = useState(null);
	const [detailedAnalysis, setDetailedAnalysis] = useState(null);
	const [meta, setMeta] = useState(null);
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
						rounds: rounds,
						points_per_round: pointsPerRound,
					}),
				}
			);
			if (!res.ok) throw new Error(`Request failed (${res.status})`);
			const data = await res.json();
			setStrategy(data.optimization_results || null);
			setDetailedAnalysis(data.detailed_analysis || null);
			setMeta(data.meta || null);
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
			<InputsPanel
				values={{
					priceMin,
					priceMax,
					variableCost,
					fixedCost,
					minMarginPercent,
					rounds,
					pointsPerRound,
				}}
				onChange={(key, val) => {
					if (key === "priceMin") setPriceMin(val);
					else if (key === "priceMax") setPriceMax(val);
					else if (key === "variableCost") setVariableCost(val);
					else if (key === "fixedCost") setFixedCost(val);
					else if (key === "minMarginPercent")
						setMinMarginPercent(val);
					// advanced fields
					else if (key === "rounds") setRounds(val);
					else if (key === "pointsPerRound") {
						setPointsPerRound(val);
					}
				}}
				onSubmit={handleFetch}
				loading={loading}
				valid={parsed.valid}
				showAdvanced={showAdvanced}
				onToggleAdvanced={() => {
					setShowAdvanced((s) => !s);
				}}
			/>

			{error && (
				<ErrorBanner message={error} onClose={() => setError("")} />
			)}

			{meta && (
				<NoticeBanner
					title="Model suggestions"
					messages={(() => {
						const msgs = [];
						if (meta.status_by_month) {
							for (const [m, v] of Object.entries(
								meta.status_by_month
							)) {
								if (v && v.feasible === false) {
									msgs.push(
										`${m}: ${
											v.message ||
											"No feasible prices found for the given Min Margin"
										}`
									);
								}
							}
						}
						if (
							meta.edge_summary_by_month &&
							meta.last_range_by_month
						) {
							for (const [m, s] of Object.entries(
								meta.edge_summary_by_month
							)) {
								const rng = meta.last_range_by_month[m];
								if (s.increasing_high > 0) {
									msgs.push(
										`${m}: Profit rising at upper bound for ${
											s.increasing_high
										} outlet(s). Consider increasing Max Price above ₹${Number(
											rng?.hi ?? 0
										).toFixed(2)}.`
									);
								}
								if (s.increasing_low > 0) {
									msgs.push(
										`${m}: Profit rising towards lower bound for ${
											s.increasing_low
										} outlet(s). Consider decreasing Min Price below ₹${Number(
											rng?.lo ?? 0
										).toFixed(2)} (may violate min margin).`
									);
								}
							}
						}
						return msgs;
					})()}
				/>
			)}

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
					minMarginPercent={parsed.margin}
				/>
			)}

			<LoadingOverlay show={loading} text="Optimizing prices…" />
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
};

export default Dashboard;
