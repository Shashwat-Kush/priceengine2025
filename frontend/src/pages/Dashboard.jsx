import { useMemo, useState } from "react";
import InputsPanel from "../components/InputsPanel";
import StrategyTable from "../components/StrategyTable";
import ChartModal from "../components/ChartModal";
import LoadingOverlay from "../components/LoadingOverlay";
import ErrorBanner from "../components/ErrorBanner";
import NoticeBanner from "../components/NoticeBanner";
import KPICards from "../components/KPICards";
import styles from "./Dashboard.module.css";

const DEFAULTS = {
	priceMin: 250,
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

	const edgeCases = useMemo(() => {
		// Build a map: { [month]: { [outletId]: 'high'|'low' } }
		const cases = {};
		if (!meta?.edge_summary_by_month) return cases;
		for (const [m, summary] of Object.entries(meta.edge_summary_by_month)) {
			cases[m] = cases[m] || {};
			const highs = Array.isArray(summary?.outlets_high)
				? summary.outlets_high
				: [];
			const lows = Array.isArray(summary?.outlets_low)
				? summary.outlets_low
				: [];
			for (const oid of highs) cases[m][oid] = "high";
			for (const oid of lows) cases[m][oid] = cases[m][oid] || "low";
		}
		return cases;
	}, [meta]);

	const handleFetch = async () => {
		if (!parsed.valid) return;
		setLoading(true);
		setError("");
		setStrategy(null);
		setDetailedAnalysis(null);
		setMeta(null);
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
				edge: edgeCases[month]?.[outletId],
			});
		}
	};

	const closeModal = () => setModalData(null);

	return (
		<div className={`${styles.page} fade-in`}>
			<h1 className={styles.pageTitle}>Dashboard</h1>
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
				onToggleAdvanced={() => setShowAdvanced((s) => !s)}
			/>

			{error && (
				<ErrorBanner message={error} onClose={() => setError("")} />
			)}

			{(meta || strategy) && <KPICards meta={meta} strategy={strategy} />}

			{meta && (
				<NoticeBanner
					title="Model Suggestions"
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
							(meta.last_range_by_month ||
								meta.feasible_bounds_by_month)
						) {
							for (const [m, s] of Object.entries(
								meta.edge_summary_by_month
							)) {
								const rng = meta.last_range_by_month?.[m];
								const feas = meta.feasible_bounds_by_month?.[m];
								const parts = [];
								if (s.increasing_high > 0) {
									parts.push(
										`Profit rising at upper bound for ${
											s.increasing_high
										} outlet(s). Consider increasing Max Price above ₹${Number(
											feas?.max_feasible_price ??
												rng?.hi ??
												0
										).toFixed(2)}.`
									);
								}
								if (s.increasing_low > 0) {
									parts.push(
										`Profit rising towards lower bound for ${
											s.increasing_low
										} outlet(s). Consider decreasing Min Price below ₹${Number(
											feas?.min_feasible_price ??
												rng?.lo ??
												0
										).toFixed(2)} (may violate min margin).`
									);
								}
								if (parts.length > 0) {
									msgs.push(`${m}: ${parts.join(" ")}`);
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
					edgeCases={edgeCases}
					onCellClick={handleCellClick}
				/>
			)}

			{modalData && (
				<ChartModal
					month={modalData.month}
					outletId={modalData.outletId}
					data={modalData.data}
					strategy={modalData.strategy}
					edge={modalData.edge}
					onClose={closeModal}
					minMarginPercent={parsed.margin}
				/>
			)}

			<LoadingOverlay show={loading} text="Analyzing scenarios..." />
		</div>
	);
}
export default Dashboard;
