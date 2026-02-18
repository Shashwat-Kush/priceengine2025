import clsx from "clsx";
import {
	Sensitivity,
	Marketplace,
	InventoryStatus,
	CompetitorRisk,
} from "@/lib/types";

export function SensitivityBadge({ value }: { value: Sensitivity }) {
	return (
		<span
			className={clsx("text-xs font-semibold px-2.5 py-1 rounded-full", {
				"bg-red-100 text-red-700": value === "High",
				"bg-orange-100 text-orange-700": value === "Medium",
				"bg-emerald-100 text-emerald-700": value === "Low",
			})}
		>
			{value}
		</span>
	);
}

export function MarketplaceBadge({ value }: { value: Marketplace }) {
	return (
		<span
			className={clsx("text-xs font-semibold px-2.5 py-1 rounded-full", {
				"bg-orange-100 text-orange-700": value === "Amazon",
				"bg-blue-100 text-blue-700": value === "Flipkart",
				"bg-pink-100 text-pink-700": value === "Meesho",
			})}
		>
			{value}
		</span>
	);
}

export function InventoryBadge({ value }: { value: InventoryStatus }) {
	return (
		<span
			className={clsx("text-xs font-semibold px-2.5 py-1 rounded-full", {
				"bg-red-100 text-red-700": value === "Critical",
				"bg-orange-100 text-orange-700": value === "Low",
				"bg-emerald-100 text-emerald-700": value === "Healthy",
				"bg-purple-100 text-purple-700": value === "Overstock",
			})}
		>
			{value}
		</span>
	);
}

export function RiskIndicator({ value }: { value: CompetitorRisk }) {
	const bars = value === "High" ? 3 : value === "Medium" ? 2 : 1;
	const color =
		value === "High"
			? "bg-red-500"
			: value === "Medium"
				? "bg-orange-400"
				: "bg-emerald-500";
	return (
		<div className="flex items-center gap-1">
			{[1, 2, 3].map((i) => (
				<div
					key={i}
					className={clsx(
						"w-2 rounded-sm",
						i <= bars ? color : "bg-slate-200",
						{
							"h-2": i === 1,
							"h-3": i === 2,
							"h-4": i === 3,
						},
					)}
				/>
			))}
			<span className="text-xs text-slate-500 ml-1">{value}</span>
		</div>
	);
}
