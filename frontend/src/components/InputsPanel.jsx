import { useState } from "react";

function numberOrEmpty(v) {
	return v === "" ? "" : v;
}

export default function InputsPanel({
	values,
	onChange,
	onSubmit,
	loading,
	valid,
	showAdvanced,
	onToggleAdvanced,
}) {
	const [focused, setFocused] = useState(null);

	const field = (key, label, placeholder, hint, type = "number") => (
		<div style={styles.field}>
			<label style={styles.label} htmlFor={key}>
				{label}
			</label>
			<input
				id={key}
				type={type}
				inputMode="decimal"
				style={{
					...styles.input,
					borderColor:
						focused === key ? "#4f7cff" : styles.input.border,
					boxShadow:
						focused === key
							? "0 0 0 3px rgba(79,124,255,0.2)"
							: "none",
				}}
				value={numberOrEmpty(values[key])}
				placeholder={placeholder}
				onFocus={() => setFocused(key)}
				onBlur={() => setFocused(null)}
				onChange={(e) => onChange(key, e.target.value)}
			/>
			{hint && <div style={styles.hint}>{hint}</div>}
		</div>
	);

	return (
		<div style={styles.card}>
			<div style={styles.header}>
				<div>
					<h1 style={styles.title}>AI-Driven Price Optimization</h1>
					<p style={styles.subtitle}>
						Find profit-maximizing prices per month and outlet using
						your demand model.
					</p>
				</div>
				<div style={{ display: "flex", gap: 8 }}>
					<button
						style={{
							...styles.secondaryButton,
							opacity: showAdvanced ? 1 : 0.9,
						}}
						onClick={onToggleAdvanced}
						type="button"
					>
						{showAdvanced ? "Hide Advanced" : "Show Advanced"}
					</button>
					<button
						style={{
							...styles.primaryButton,
							opacity: valid ? 1 : 0.6,
						}}
						onClick={onSubmit}
						disabled={loading || !valid}
						type="button"
					>
						{loading ? "Optimizing…" : "Optimize"}
					</button>
				</div>
			</div>

			<div style={styles.grid}>
				{field("priceMin", "Min Price (₹)", "e.g. 200")}
				{field("priceMax", "Max Price (₹)", "e.g. 320")}
				{field(
					"variableCost",
					"Variable Cost per Unit (₹)",
					"e.g. 120"
				)}
				{field("fixedCost", "Fixed Cost (₹)", "e.g. 1000")}
				{field("minMarginPercent", "Min Margin (%)", "e.g. 10")}
			</div>

			{showAdvanced && (
				<div style={{ marginTop: 12 }}>
					<h3 style={styles.sectionTitle}>Advanced search</h3>
					<div style={styles.gridSmall}>
						{field("rounds", "Refinement Rounds", "3")}
						{field("pointsPerRound", "Grid Points / Round", "21")}
					</div>
					<p style={styles.footnote}>
						Higher values increase accuracy but take longer to run.
					</p>
				</div>
			)}
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
	header: {
		display: "flex",
		alignItems: "center",
		justifyContent: "space-between",
		gap: 16,
		marginBottom: 12,
		flexWrap: "wrap",
	},
	title: { fontSize: 22, margin: 0 },
	subtitle: { color: "#9fb2d9", margin: "6px 0 0 0" },
	grid: {
		display: "grid",
		gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
		gap: 12,
		marginTop: 12,
	},
	gridSmall: {
		display: "grid",
		gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
		gap: 12,
	},
	field: { display: "flex", flexDirection: "column" },
	label: { display: "block", marginBottom: 6, color: "#c6d3f5" },
	input: {
		padding: 10,
		borderRadius: 8,
		border: "1px solid #263557",
		background: "#0e1524",
		color: "#e9eefc",
		fontFamily: "inherit",
		outline: "none",
	},
	hint: { marginTop: 4, fontSize: 12, color: "#9fb2d9" },
	sectionTitle: { margin: "6px 0 8px 0", color: "#c6d3f5" },
	footnote: { marginTop: 8, color: "#9fb2d9", fontSize: 12 },
	primaryButton: {
		background: "#4f7cff",
		border: 0,
		color: "white",
		padding: "10px 14px",
		borderRadius: 8,
		cursor: "pointer",
	},
	secondaryButton: {
		background: "transparent",
		border: "1px solid #263557",
		color: "#9fb2d9",
		padding: "10px 14px",
		borderRadius: 8,
		cursor: "pointer",
	},
};
