"use client";

import { useEffect, useState } from "react";
import { getSKUs } from "@/lib/services";
import { SKU, Marketplace, Sensitivity, InventoryStatus } from "@/lib/types";
import {
	MarketplaceBadge,
	SensitivityBadge,
	InventoryBadge,
	RiskIndicator,
} from "@/components/Badges";
import Link from "next/link";
import { Search, ChevronRight, Filter } from "lucide-react";

export default function SKUsPage() {
	const [skus, setSkus] = useState<SKU[]>([]);
	const [loading, setLoading] = useState(true);
	const [search, setSearch] = useState("");
	const [filterMarketplace, setFilterMarketplace] = useState<string>("");
	const [filterMargin, setFilterMargin] = useState<string>("");
	const [filterStatus, setFilterStatus] = useState<string>("");
	const [filterRisk, setFilterRisk] = useState<string>("");

	useEffect(() => {
		getSKUs().then((data) => {
			setSkus(data);
			setLoading(false);
		});
	}, []);

	const filtered = skus.filter((sku) => {
		const matchSearch =
			!search ||
			sku.name.toLowerCase().includes(search.toLowerCase()) ||
			sku.id.toLowerCase().includes(search.toLowerCase()) ||
			sku.category.toLowerCase().includes(search.toLowerCase());
		const matchMarketplace =
			!filterMarketplace || sku.marketplace === filterMarketplace;
		const matchMargin =
			!filterMargin ||
			(filterMargin === "high" && sku.margin >= 55) ||
			(filterMargin === "medium" &&
				sku.margin >= 40 &&
				sku.margin < 55) ||
			(filterMargin === "low" && sku.margin < 40);
		const matchStatus =
			!filterStatus || sku.inventoryStatus === filterStatus;
		const matchRisk = !filterRisk || sku.competitorRisk === filterRisk;
		return (
			matchSearch &&
			matchMarketplace &&
			matchMargin &&
			matchStatus &&
			matchRisk
		);
	});

	return (
		<div className="space-y-4">
			{/* Search + Filters */}
			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
				<div className="flex flex-wrap gap-3 items-center">
					<div className="relative flex-1 min-w-[200px]">
						<Search
							size={15}
							className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
						/>
						<input
							type="text"
							placeholder="Search SKU, category…"
							value={search}
							onChange={(e) => setSearch(e.target.value)}
							className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
					<div className="flex items-center gap-2 text-slate-500 text-sm">
						<Filter size={14} />
						<span className="text-xs font-medium">Filters:</span>
					</div>
					<select
						value={filterMarketplace}
						onChange={(e) => setFilterMarketplace(e.target.value)}
						className="border border-slate-300 rounded-lg text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
					>
						<option value="">All Platforms</option>
						<option value="Amazon">Amazon</option>
						<option value="Flipkart">Flipkart</option>
						<option value="Meesho">Meesho</option>
					</select>
					<select
						value={filterMargin}
						onChange={(e) => setFilterMargin(e.target.value)}
						className="border border-slate-300 rounded-lg text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
					>
						<option value="">All Margins</option>
						<option value="high">High (≥55%)</option>
						<option value="medium">Medium (40–55%)</option>
						<option value="low">Low (&lt;40%)</option>
					</select>
					<select
						value={filterStatus}
						onChange={(e) => setFilterStatus(e.target.value)}
						className="border border-slate-300 rounded-lg text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
					>
						<option value="">All Inventory</option>
						<option value="Critical">Critical</option>
						<option value="Low">Low</option>
						<option value="Healthy">Healthy</option>
						<option value="Overstock">Overstock</option>
					</select>
					<select
						value={filterRisk}
						onChange={(e) => setFilterRisk(e.target.value)}
						className="border border-slate-300 rounded-lg text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
					>
						<option value="">All Risk Levels</option>
						<option value="High">High Risk</option>
						<option value="Medium">Medium Risk</option>
						<option value="Low">Low Risk</option>
					</select>
					{(filterMarketplace ||
						filterMargin ||
						filterStatus ||
						filterRisk ||
						search) && (
						<button
							onClick={() => {
								setSearch("");
								setFilterMarketplace("");
								setFilterMargin("");
								setFilterStatus("");
								setFilterRisk("");
							}}
							className="text-xs text-red-600 hover:underline"
						>
							Clear all
						</button>
					)}
				</div>
				<p className="text-xs text-slate-400 mt-2">
					{filtered.length} of {skus.length} SKUs
				</p>
			</div>

			{/* Table */}
			<div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
				{loading ? (
					<div className="flex items-center justify-center h-60">
						<div className="w-7 h-7 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
					</div>
				) : filtered.length === 0 ? (
					<div className="text-center py-16 text-slate-400">
						<p className="font-medium">
							No SKUs match your filters.
						</p>
						<p className="text-xs mt-1">
							Try adjusting your search or filter criteria.
						</p>
					</div>
				) : (
					<div className="overflow-x-auto">
						<table className="w-full text-sm">
							<thead>
								<tr className="border-b border-slate-100 bg-slate-50">
									<th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										SKU / Category
									</th>
									<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Platform
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Price
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Cost
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Margin
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Comp. Price
									</th>
									<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Stock
									</th>
									<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Inv. Status
									</th>
									<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Comp. Risk
									</th>
									<th className="px-3 py-3"></th>
								</tr>
							</thead>
							<tbody>
								{filtered.map((sku) => (
									<tr
										key={sku.id}
										className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors cursor-pointer"
									>
										<td className="px-5 py-3.5">
											<Link
												href={`/skus/${sku.id}`}
												className="block"
											>
												<p className="font-medium text-slate-800 hover:text-blue-600 transition-colors">
													{sku.name}
												</p>
												<p className="text-xs text-slate-400 mt-0.5">
													{sku.category} · {sku.id}
												</p>
											</Link>
										</td>
										<td className="px-3 py-3.5">
											<MarketplaceBadge
												value={sku.marketplace}
											/>
										</td>
										<td className="px-3 py-3.5 text-right font-mono text-slate-700 font-medium">
											₹{sku.currentPrice}
										</td>
										<td className="px-3 py-3.5 text-right font-mono text-slate-500">
											₹{sku.cost}
										</td>
										<td className="px-3 py-3.5 text-right">
											<span
												className={`font-semibold ${sku.margin >= 55 ? "text-emerald-600" : sku.margin >= 40 ? "text-blue-600" : "text-orange-600"}`}
											>
												{sku.margin.toFixed(1)}%
											</span>
										</td>
										<td className="px-3 py-3.5 text-right font-mono">
											<span
												className={
													sku.competitorPrice <
													sku.currentPrice
														? "text-red-600 font-semibold"
														: "text-slate-500"
												}
											>
												₹{sku.competitorPrice}
											</span>
										</td>
										<td className="px-3 py-3.5 text-right text-slate-600 font-mono">
											{sku.inventory}
										</td>
										<td className="px-3 py-3.5">
											<InventoryBadge
												value={sku.inventoryStatus}
											/>
										</td>
										<td className="px-3 py-3.5">
											<RiskIndicator
												value={sku.competitorRisk}
											/>
										</td>
										<td className="px-3 py-3.5">
											<Link
												href={`/skus/${sku.id}`}
												className="text-blue-500 hover:text-blue-700 transition-colors"
											>
												<ChevronRight size={16} />
											</Link>
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</div>
		</div>
	);
}
