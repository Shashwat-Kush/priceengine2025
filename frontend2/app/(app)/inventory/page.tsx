"use client";

import { useEffect, useState } from "react";
import { getInventoryData } from "@/lib/services";
import { MarketplaceBadge, InventoryBadge } from "@/components/Badges";
import { KpiCard } from "@/components/KpiCard";
import Link from "next/link";
import clsx from "clsx";
import { Package, IndianRupee, AlertTriangle } from "lucide-react";

function formatINR(n: number) {
	if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
	if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
	return `₹${n}`;
}

type InventoryRow = {
	id: string;
	name: string;
	marketplace: "Amazon" | "Flipkart" | "Meesho";
	inventory: number;
	dailyDemand: number;
	leadTimeDays: number;
	inventoryStatus: "Healthy" | "Low" | "Critical" | "Overstock";
	daysUntilStockout: number;
	reorderPoint: number;
	suggestedOrderQty: number;
	storageCostImpact: number;
	orderCost: number;
	cost: number;
};

export default function InventoryPage() {
	const [data, setData] = useState<InventoryRow[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		getInventoryData().then((d) => {
			setData(d as InventoryRow[]);
			setLoading(false);
		});
	}, []);

	const totalInventoryValue = data.reduce(
		(s, r) => s + r.inventory * r.cost,
		0,
	);
	const totalOrderCost = data.reduce((s, r) => s + r.orderCost, 0);
	const criticalCount = data.filter(
		(r) => r.inventoryStatus === "Critical",
	).length;
	const overstockCount = data.filter(
		(r) => r.inventoryStatus === "Overstock",
	).length;

	return (
		<div className="space-y-5">
			{loading ? (
				<div className="flex items-center justify-center h-80">
					<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
				</div>
			) : (
				<>
					{/* Summary KPIs */}
					<div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
						<KpiCard
							title="Total Inventory Value"
							value={formatINR(totalInventoryValue)}
							sub="Current stock at cost"
							color="blue"
							icon={<Package size={16} />}
						/>
						<KpiCard
							title="Cash for Reorders"
							value={formatINR(totalOrderCost)}
							sub="Suggested purchase value"
							color="orange"
							icon={<IndianRupee size={16} />}
						/>
						<KpiCard
							title="Critical SKUs"
							value={criticalCount}
							sub="Stockout risk < 7 days"
							color="red"
							icon={<AlertTriangle size={16} />}
						/>
						<KpiCard
							title="Overstock SKUs"
							value={overstockCount}
							sub="Capital locked in stock"
							color="orange"
							icon={<Package size={16} />}
						/>
					</div>

					{/* Table */}
					<div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
						<div className="px-5 py-4 border-b border-slate-100">
							<h2 className="font-semibold text-slate-800">
								Inventory & Purchase Planner
							</h2>
							<p className="text-xs text-slate-500 mt-0.5">
								Real-time stock levels with AI-powered reorder
								suggestions
							</p>
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
											Stock
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Daily Demand
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Days Left
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Lead Time
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Suggested Order
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Order Cost
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Storage Impact
										</th>
										<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Status
										</th>
									</tr>
								</thead>
								<tbody>
									{data.map((row) => (
										<tr
											key={row.id}
											className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
										>
											<td className="px-5 py-3.5">
												<Link
													href={`/skus/${row.id}`}
													className="font-medium text-slate-800 hover:text-blue-600 transition-colors"
												>
													{row.name}
												</Link>
											</td>
											<td className="px-3 py-3.5">
												<MarketplaceBadge
													value={row.marketplace}
												/>
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-700">
												{row.inventory}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-600">
												{row.dailyDemand}
											</td>
											<td className="px-3 py-3.5 text-right">
												<span
													className={clsx(
														"font-semibold font-mono",
														{
															"text-red-600":
																row.daysUntilStockout <=
																7,
															"text-orange-500":
																row.daysUntilStockout >
																	7 &&
																row.daysUntilStockout <=
																	14,
															"text-emerald-600":
																row.daysUntilStockout >
																14,
														},
													)}
												>
													{row.daysUntilStockout >=
													999
														? "∞"
														: row.daysUntilStockout}
													d
												</span>
											</td>
											<td className="px-3 py-3.5 text-right text-slate-500 font-mono">
												{row.leadTimeDays}d
											</td>
											<td className="px-3 py-3.5 text-right">
												{row.suggestedOrderQty > 0 ? (
													<span className="font-bold text-blue-700 font-mono">
														{row.suggestedOrderQty}{" "}
														units
													</span>
												) : (
													<span className="text-slate-400 text-xs">
														None needed
													</span>
												)}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-600">
												{row.orderCost > 0
													? formatINR(row.orderCost)
													: "—"}
											</td>
											<td className="px-3 py-3.5 text-right text-slate-500 font-mono text-xs">
												{row.storageCostImpact > 0
													? `+₹${row.storageCostImpact}/mo`
													: "—"}
											</td>
											<td className="px-3 py-3.5">
												<InventoryBadge
													value={row.inventoryStatus}
												/>
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				</>
			)}
		</div>
	);
}
