import styles from "./InputsPanel.module.css";
import Icon from "./Icon";

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
	const field = (key, label, placeholder, hint) => (
		<div className={styles.field}>
			<label className={styles.label} htmlFor={key}>
				<span>{label}</span>
				{hint && (
					<span className={styles.tooltipWrapper}>
						<Icon name="help" size={14} />
						<span className={styles.tooltip}>{hint}</span>
					</span>
				)}
			</label>
			<input
				id={key}
				type="number"
				inputMode="decimal"
				className={styles.input}
				value={numberOrEmpty(values[key])}
				placeholder={placeholder}
				onChange={(e) => onChange(key, e.target.value)}
			/>
		</div>
	);

	return (
		<div className={`${styles.card} fade-in`}>
			<div className={styles.header}>
				<h1 className={styles.title}>Optimization Inputs</h1>
				<div className={styles.actions}>
					<button
						className={styles.secondaryButton}
						onClick={onToggleAdvanced}
						type="button"
						aria-pressed={showAdvanced}
					>
						<Icon name="settings" size={16} />
						<span>
							{showAdvanced ? "Hide Advanced" : "Advanced"}
						</span>
					</button>
					<button
						className={styles.primaryButton}
						onClick={onSubmit}
						disabled={loading || !valid}
						type="button"
					>
						{loading ? "Optimizing…" : "Run Optimization"}
					</button>
				</div>
			</div>

			<div className={styles.grid}>
				{field("priceMin", "Min Price (₹)", "e.g. 250")}
				{field("priceMax", "Max Price (₹)", "e.g. 320")}
				{field(
					"variableCost",
					"Variable Cost per Unit (₹)",
					"e.g. 120"
				)}
				{field("fixedCost", "Fixed Cost (₹)", "e.g. 1000")}
				{field(
					"minMarginPercent",
					"Min Margin (%)",
					"e.g. 10",
					"The minimum profit margin you want to achieve."
				)}
			</div>

			{showAdvanced && (
				<div className={styles.advancedSection}>
					<h3 className={styles.sectionTitle}>Advanced Settings</h3>
					<div className={styles.gridSmall}>
						{field(
							"rounds",
							"Refinement Rounds",
							"3",
							"Number of optimization rounds. More rounds can improve accuracy."
						)}
						{field(
							"pointsPerRound",
							"Grid Points / Round",
							"21",
							"Number of price points to test in each round."
						)}
					</div>
				</div>
			)}
		</div>
	);
}
