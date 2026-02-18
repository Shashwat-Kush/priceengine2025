import clsx from "clsx";

type Props = {
	title: string;
	value: string | number;
	sub?: string;
	trend?: "up" | "down" | "neutral";
	trendValue?: string;
	color?: "default" | "green" | "red" | "orange" | "blue";
	icon?: React.ReactNode;
};

export function KpiCard({
	title,
	value,
	sub,
	trend,
	trendValue,
	color = "default",
	icon,
}: Props) {
	const borderColor = {
		default: "border-l-slate-300",
		green: "border-l-emerald-500",
		red: "border-l-red-500",
		orange: "border-l-orange-500",
		blue: "border-l-blue-500",
	}[color];

	const trendColor =
		trend === "up"
			? "text-emerald-600"
			: trend === "down"
				? "text-red-500"
				: "text-slate-500";

	return (
		<div
			className={clsx(
				"bg-white rounded-xl shadow-sm border border-slate-100 border-l-4 p-5",
				borderColor,
			)}
		>
			<div className="flex items-start justify-between">
				<p className="text-sm font-medium text-slate-500 mb-1">
					{title}
				</p>
				{icon && <span className="text-slate-400">{icon}</span>}
			</div>
			<p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
			{(trendValue || sub) && (
				<p className={clsx("text-xs mt-1.5 font-medium", trendColor)}>
					{trendValue &&
						(trend === "up" ? "▲ " : trend === "down" ? "▼ " : "")}
					{trendValue ?? sub}
					{sub && trendValue && (
						<span className="text-slate-400 ml-1">{sub}</span>
					)}
				</p>
			)}
		</div>
	);
}
