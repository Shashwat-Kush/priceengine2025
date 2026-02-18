"use client";

import { useEffect, useState } from "react";
import { getDashboardData } from "@/lib/services";
import { DashboardKPIs, RecommendedAction, Alert } from "@/lib/types";
import { KpiCard } from "@/components/KpiCard";
import { MarketplaceBadge } from "@/components/Badges";
import Link from "next/link";
import {
	IndianRupee,
	TrendingUp,
	TrendingDown,
	AlertTriangle,
	Users,
	Package,
	ChevronRight,
	CheckCircle2,
} from "lucide-react";
import clsx from "clsx";

function formatINR(n: number) {
	if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
	if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
	return `₹${n}`;
}

const alertIcons: Record<string, React.ReactNode> = {
	low_stock: <AlertTriangle size={14} />,
	undercut: <TrendingDown size={14} />,
	festival_opportunity: <TrendingUp size={14} />,
	overpriced: <IndianRupee size={14} />,
};

const alertColors: Record<string, string> = {
	high: "border-l-red-500 bg-red-50",
	medium: "border-l-orange-400 bg-orange-50",
	low: "border-l-blue-400 bg-blue-50",
};

const alertTextColors: Record<string, string> = {
	high: "text-red-700",
	medium: "text-orange-700",
	low: "text-blue-700",
};

export default function DashboardPage() {
	const [data, setData] = useState<{
		kpis: DashboardKPIs;
		recommendedActions: RecommendedAction[];
		alerts: Alert[];
	} | null>(null);
	const [loading, setLoading] = useState(true);
	const [appliedActions, setAppliedActions] = useState<Set<string>>(
		new Set(),
	);

	useEffect(() => {
		getDashboardData().then((d) => {
			setData(d);
			setLoading(false);
		});
	}, []);

	if (loading) {
		return (
			<div className="flex items-center justify-center h-80">
				<div className="flex flex-col items-center gap-3">
					<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
					<p className="text-slate-500 text-sm">Loading dashboard…</p>
				</div>
			</div>
		);
	}

	const { kpis, recommendedActions, alerts } = data!;

	const handleApply = (skuId: string) => {
		setAppliedActions((prev) => new Set([...prev, skuId]));
	};

	return (
		<div className="space-y-6">
			{/* KPI Cards */}
			<div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
				<KpiCard
					title="Revenue (30d)"
					value={formatINR(kpis.totalRevenue)}
					trend="up"
					trendValue="+12.4% vs last month"
					color="blue"
					icon={<IndianRupee size={16} />}
				/>
				<KpiCard
					title="Total Profit"
					value={formatINR(kpis.totalProfit)}
					trend="up"
					trendValue="+8.1%"
					color="green"
					icon={<TrendingUp size={16} />}
				/>
				<KpiCard
					title="Missed Profit"
					value={formatINR(kpis.missedProfit)}
					sub="Recoverable"
					trend="down"
					trendValue={formatINR(kpis.missedProfit)}
					color="orange"
					icon={<TrendingDown size={16} />}
				/>
				<KpiCard
					title="Inventory Alerts"
					value={kpis.inventoryAlerts}
					sub="SKUs need attention"
					color="red"
					icon={<Package size={16} />}
				/>
				<KpiCard
					title="Undercut Alerts"
					value={kpis.undercutAlerts}
					sub="Competitors cheaper"
					color="orange"
					icon={<Users size={16} />}
				/>
			</div>

			{/* Recommended Actions + Alerts */}
			<div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
				{/* Recommended Actions Table */}
				<div className="xl:col-span-2 bg-white rounded-xl shadow-sm border border-slate-100">
					<div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
						<div>
							<h2 className="font-semibold text-slate-800">
								Recommended Actions
							</h2>
							<p className="text-xs text-slate-500 mt-0.5">
								AI-suggested price changes for maximum profit
							</p>
						</div>
						<Link
							href="/skus"
							className="text-xs text-blue-600 hover:underline flex items-center gap-1"
						>
							View all SKUs <ChevronRight size={12} />
						</Link>
					</div>
					<div className="overflow-x-auto">
						<table className="w-full text-sm">
							<thead>
								<tr className="border-b border-slate-100 bg-slate-50">
									<th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										SKU
									</th>
									<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Platform
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Current
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Suggested Range
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Profit Impact
									</th>
									<th className="px-3 py-3"></th>
								</tr>
							</thead>
							<tbody>
								{recommendedActions.map((action) => {
									const applied = appliedActions.has(
										action.skuId,
									);
									return (
										<tr
											key={action.skuId}
											className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
										>
											<td className="px-5 py-3.5">
												<Link
													href={`/skus/${action.skuId}`}
													className="font-medium text-slate-800 hover:text-blue-600 transition-colors"
												>
													{action.skuName}
												</Link>
												<p className="text-xs text-slate-400 mt-0.5 max-w-[160px] truncate">
													{action.reason}
												</p>
											</td>
											<td className="px-3 py-3.5">
												<MarketplaceBadge
													value={action.marketplace}
												/>
											</td>
											<td className="px-3 py-3.5 text-right text-slate-600 font-mono">
												₹{action.currentPrice}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-blue-700 font-medium">
												₹{action.recommendedMin}–
												{action.recommendedMax}
											</td>
											<td className="px-3 py-3.5 text-right">
												<span className="text-emerald-600 font-semibold">
													+
													{formatINR(
														action.estimatedProfitChange,
													)}
												</span>
											</td>
											<td className="px-3 py-3.5">
												<div className="flex gap-1.5 justify-end">
													<Link
														href={`/skus/${action.skuId}`}
														className="px-2.5 py-1 text-xs rounded-md border border-slate-300 text-slate-600 hover:bg-slate-100 transition-colors"
													>
														Simulate
													</Link>
													<button
														onClick={() =>
															handleApply(
																action.skuId,
															)
														}
														disabled={applied}
														className={clsx(
															"px-2.5 py-1 text-xs rounded-md font-medium transition-colors",
															applied
																? "bg-emerald-100 text-emerald-700 border border-emerald-200 cursor-default"
																: "bg-blue-600 text-white hover:bg-blue-700",
														)}
													>
														{applied ? (
															<span className="flex items-center gap-1">
																<CheckCircle2
																	size={11}
																/>{" "}
																Applied
															</span>
														) : (
															"Apply"
														)}
													</button>
												</div>
											</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
				</div>

				{/* Alerts Panel */}
				<div className="bg-white rounded-xl shadow-sm border border-slate-100">
					<div className="px-5 py-4 border-b border-slate-100">
						<h2 className="font-semibold text-slate-800">Alerts</h2>
						<p className="text-xs text-slate-500 mt-0.5">
							{alerts.length} active alerts
						</p>
					</div>
					<div className="p-4 space-y-2.5 max-h-96 overflow-y-auto">
						{alerts.map((alert) => (
							<Link
								key={alert.id}
								href={`/skus/${alert.skuId}`}
								className={clsx(
									"block border-l-4 rounded-lg px-3.5 py-3 transition-opacity hover:opacity-80",
									alertColors[alert.severity],
								)}
							>
								<div
									className={clsx(
										"flex items-center gap-1.5 font-semibold text-xs mb-1",
										alertTextColors[alert.severity],
									)}
								>
									{alertIcons[alert.type]}
									<span className="capitalize">
										{alert.type.replace(/_/g, " ")}
									</span>
								</div>
								<p className="text-xs text-slate-700 font-medium">
									{alert.skuName}
								</p>
								<p className="text-xs text-slate-500 mt-0.5">
									{alert.message}
								</p>
							</Link>
						))}
					</div>
				</div>
			</div>
		</div>
	);
}
