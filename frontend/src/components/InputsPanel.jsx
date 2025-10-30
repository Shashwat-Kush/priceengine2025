// Inputs form styled via CSS Modules
import styles from "./InputsPanel.module.css";

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
	const field = (key, label, placeholder, hint, type = "number") => (
		<div className={styles.field}>
			<label className={styles.label} htmlFor={key}>
				{label}
			</label>
			<input
				id={key}
				type={type}
				inputMode="decimal"
				className={styles.input}
				value={numberOrEmpty(values[key])}
				placeholder={placeholder}
				onChange={(e) => onChange(key, e.target.value)}
			/>
			{hint && <div className={styles.hint}>{hint}</div>}
		</div>
	);

	return (
		<div className={`${styles.card} fade-in`}>
			<div className={styles.header}>
				<div>
					<h1 className={styles.title}>
						AI-Driven Price Optimization
					</h1>
					<p className={styles.subtitle}>
						Find profit-maximizing prices per month and outlet using
						your demand model.
					</p>
				</div>
				<div className={styles.actions}>
					<button
						className={styles.secondaryButton}
						onClick={onToggleAdvanced}
						type="button"
						aria-pressed={showAdvanced}
					>
						{showAdvanced ? "Hide Advanced" : "Show Advanced"}
					</button>
					<button
						className={styles.primaryButton}
						style={{ opacity: valid ? 1 : 0.6 }}
						onClick={onSubmit}
						disabled={loading || !valid}
						type="button"
					>
						{loading ? "Optimizing…" : "Optimize"}
					</button>
				</div>
			</div>

			<div className={styles.grid}>
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
					<h3 className={styles.sectionTitle}>Advanced search</h3>
					<div className={styles.gridSmall}>
						{field("rounds", "Refinement Rounds", "3")}
						{field("pointsPerRound", "Grid Points / Round", "21")}
					</div>
					<p className={styles.footnote}>
						Higher values increase accuracy but take longer to run.
					</p>
				</div>
			)}
		</div>
	);
}
