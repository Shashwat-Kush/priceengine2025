"use client";

import { useState } from "react";
import clsx from "clsx";
import { CheckCircle2, RefreshCw } from "lucide-react";

function Toggle({
	value,
	onChange,
}: {
	value: boolean;
	onChange: (v: boolean) => void;
}) {
	return (
		<button
			onClick={() => onChange(!value)}
			className={clsx(
				"relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
				value ? "bg-blue-600" : "bg-slate-200",
			)}
		>
			<span
				className={clsx(
					"inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform",
					value ? "translate-x-6" : "translate-x-1",
				)}
			/>
		</button>
	);
}

function Section({
	title,
	subtitle,
	children,
}: {
	title: string;
	subtitle?: string;
	children: React.ReactNode;
}) {
	return (
		<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
			<h2 className="font-semibold text-slate-800 mb-0.5">{title}</h2>
			{subtitle && (
				<p className="text-xs text-slate-500 mb-4">{subtitle}</p>
			)}
			<div className="mt-3">{children}</div>
		</div>
	);
}

const platformConnections = [
	{
		name: "Amazon",
		status: "connected",
		lastSync: "2 hours ago",
		color: "bg-orange-500",
	},
	{
		name: "Flipkart",
		status: "connected",
		lastSync: "4 hours ago",
		color: "bg-blue-500",
	},
	{
		name: "Meesho",
		status: "pending",
		lastSync: "Never",
		color: "bg-pink-500",
	},
];

export default function SettingsPage() {
	const [minMargin, setMinMargin] = useState(30);
	const [maxDiscount, setMaxDiscount] = useState(25);
	const [autoApprove, setAutoApprove] = useState(false);
	const [priceAlerts, setPriceAlerts] = useState(true);
	const [stockAlerts, setStockAlerts] = useState(true);
	const [festivalReminders, setFestivalReminders] = useState(true);
	const [saved, setSaved] = useState(false);

	const handleSave = async () => {
		await new Promise((r) => setTimeout(r, 600));
		setSaved(true);
		setTimeout(() => setSaved(false), 3000);
	};

	return (
		<div className="max-w-2xl space-y-5">
			{/* Pricing Rules */}
			<Section
				title="Pricing Rules"
				subtitle="Define guardrails that limit automated price changes"
			>
				<div className="space-y-5">
					<div>
						<div className="flex justify-between text-sm mb-2">
							<label className="font-medium text-slate-700">
								Minimum Margin %
							</label>
							<span className="font-bold text-blue-600">
								{minMargin}%
							</span>
						</div>
						<input
							type="range"
							min={5}
							max={70}
							value={minMargin}
							onChange={(e) =>
								setMinMargin(Number(e.target.value))
							}
							className="w-full h-2 rounded-lg appearance-none bg-slate-200 accent-blue-500"
						/>
						<p className="text-xs text-slate-400 mt-1.5">
							Prices will never be set below this margin
							threshold. Currently protecting{" "}
							<span className="font-medium text-slate-600">
								all SKUs
							</span>
							.
						</p>
					</div>
					<div>
						<div className="flex justify-between text-sm mb-2">
							<label className="font-medium text-slate-700">
								Maximum Discount %
							</label>
							<span className="font-bold text-orange-600">
								{maxDiscount}%
							</span>
						</div>
						<input
							type="range"
							min={0}
							max={60}
							value={maxDiscount}
							onChange={(e) =>
								setMaxDiscount(Number(e.target.value))
							}
							className="w-full h-2 rounded-lg appearance-none bg-slate-200 accent-orange-400"
						/>
						<p className="text-xs text-slate-400 mt-1.5">
							Max discount allowed vs. your listed price. Prevents
							excessive markdowns.
						</p>
					</div>
				</div>
			</Section>

			{/* Automation */}
			<Section
				title="Automation"
				subtitle="Control how AI recommendations are applied"
			>
				<div className="space-y-4">
					<div className="flex items-center justify-between py-3 border-b border-slate-100">
						<div>
							<p className="text-sm font-medium text-slate-700">
								Auto-Approve Recommendations
							</p>
							<p className="text-xs text-slate-400 mt-0.5">
								{autoApprove
									? "⚠️ AI changes are applied automatically without review."
									: "Manual review required before any price change is applied."}
							</p>
						</div>
						<Toggle value={autoApprove} onChange={setAutoApprove} />
					</div>
					{autoApprove && (
						<div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 text-xs text-orange-700">
							<strong>Caution:</strong> Auto-approve will apply
							price changes within your defined guardrails
							automatically. You can revert any change from the
							audit log.
						</div>
					)}
				</div>
			</Section>

			{/* Notifications */}
			<Section
				title="Notifications"
				subtitle="Choose which alerts you want to receive"
			>
				<div className="space-y-4">
					{[
						{
							label: "Competitor Price Alerts",
							sub: "Notify when a competitor undercuts your pricing",
							value: priceAlerts,
							onChange: setPriceAlerts,
						},
						{
							label: "Stock Level Alerts",
							sub: "Notify when inventory drops below reorder point",
							value: stockAlerts,
							onChange: setStockAlerts,
						},
						{
							label: "Festival Opportunity Reminders",
							sub: "Remind you 30 days before key shopping events",
							value: festivalReminders,
							onChange: setFestivalReminders,
						},
					].map(({ label, sub, value, onChange }) => (
						<div
							key={label}
							className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
						>
							<div>
								<p className="text-sm font-medium text-slate-700">
									{label}
								</p>
								<p className="text-xs text-slate-400 mt-0.5">
									{sub}
								</p>
							</div>
							<Toggle value={value} onChange={onChange} />
						</div>
					))}
				</div>
			</Section>

			{/* Marketplace Connections */}
			<Section
				title="Marketplace Connections"
				subtitle="Manage platform integrations"
			>
				<div className="space-y-3">
					{platformConnections.map(
						({ name, status, lastSync, color }) => (
							<div
								key={name}
								className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0"
							>
								<div className="flex items-center gap-3">
									<div
										className={clsx(
											"w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold",
											color,
										)}
									>
										{name[0]}
									</div>
									<div>
										<p className="text-sm font-medium text-slate-700">
											{name}
										</p>
										<p className="text-xs text-slate-400">
											Last synced: {lastSync}
										</p>
									</div>
								</div>
								<div className="flex items-center gap-3">
									<span
										className={clsx(
											"text-xs font-semibold px-2.5 py-1 rounded-full",
											status === "connected"
												? "bg-emerald-100 text-emerald-700"
												: "bg-orange-100 text-orange-700",
										)}
									>
										{status === "connected"
											? "Connected"
											: "Pending Setup"}
									</span>
									<button className="text-slate-400 hover:text-blue-500 transition-colors">
										<RefreshCw size={14} />
									</button>
								</div>
							</div>
						),
					)}
					<p className="text-xs text-slate-400 mt-2">
						This is a demo environment. Marketplace connections are
						simulated.
					</p>
				</div>
			</Section>

			{/* Account */}
			<Section title="Account" subtitle="Your seller profile">
				<div className="space-y-3">
					<div className="grid grid-cols-2 gap-3">
						<div>
							<label className="text-xs font-medium text-slate-500 mb-1 block">
								Name
							</label>
							<input
								defaultValue="Ravi Sharma"
								className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>
						<div>
							<label className="text-xs font-medium text-slate-500 mb-1 block">
								Email
							</label>
							<input
								defaultValue="ravi@shop.in"
								className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>
					</div>
					<div>
						<label className="text-xs font-medium text-slate-500 mb-1 block">
							Business Name
						</label>
						<input
							defaultValue="Ravi Electronics & General Store"
							className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
				</div>
			</Section>

			{/* Save */}
			<div className="flex justify-end">
				<button
					onClick={handleSave}
					className={clsx(
						"flex items-center gap-2 px-6 py-2.5 rounded-lg font-semibold text-sm transition-all",
						saved
							? "bg-emerald-600 text-white"
							: "bg-blue-600 hover:bg-blue-700 text-white",
					)}
				>
					{saved ? (
						<>
							<CheckCircle2 size={16} /> Saved!
						</>
					) : (
						"Save Changes"
					)}
				</button>
			</div>
		</div>
	);
}
