"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Calendar, Package, TrendingUp, Zap } from "lucide-react";
import clsx from "clsx";
import {
	getPricingAnalysis,
	getSKUById,
	simulatePriceChange,
} from "@/lib/services";
import {
	EngineListingView,
	EngineRecord,
	PricingAnalysisResponse,
	SimulatorOutput,
} from "@/lib/types";
import { MarketplaceBadge, SensitivityBadge } from "@/components/Badges";
import {
	CartesianGrid,
	Line,
	LineChart,
	ReferenceLine,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

function formatINR(n: number) {
	if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
	if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
	return `₹${n.toFixed(0)}`;
}

export default function SKUDetailPage({
	params,
}: {
	params: Promise<{ id: string }>;
}) {
	const [skuId, setSkuId] = useState("");
	const [record, setRecord] = useState<EngineRecord | null>(null);
	const [pricing, setPricing] = useState<PricingAnalysisResponse | null>(
		null,
	);
	const [loading, setLoading] = useState(true);

	const [activeListingId, setActiveListingId] = useState("");
	const [simPrice, setSimPrice] = useState(0);
	const [simFestivalBoost, setSimFestivalBoost] = useState(false);
	const [simLoading, setSimLoading] = useState(false);
	const [simResult, setSimResult] = useState<SimulatorOutput | null>(null);

	useEffect(() => {
		params.then(async ({ id }) => {
			setSkuId(id);
			setLoading(true);
			const [skuData, pricingData] = await Promise.all([
				getSKUById(id),
				getPricingAnalysis(id),
			]);

			setRecord(skuData);
			setPricing(pricingData);

			const primary = skuData?.listing;
			const allListings = skuData?.listings ?? [];
			const firstListing = allListings[0]?.listing || primary;

			if (firstListing) {
				setActiveListingId(firstListing.id);
				setSimPrice(firstListing.price);
			}

			setLoading(false);
		});
	}, [params]);

	const listingRows: EngineListingView[] = useMemo(() => {
		if (!record) return [];
		if (record.listings && record.listings.length > 0)
			return record.listings;
		if (record.listing) {
			return [
				{
					listing: record.listing,
					competitors: record.competitors,
					computed: record.computed,
				},
			];
		}
		return [];
	}, [record]);

	const activeListingRow = useMemo(
		() =>
			listingRows.find((row) => row.listing.id === activeListingId) ||
			listingRows[0],
		[listingRows, activeListingId],
	);

	const runSimulation = async () => {
		if (!skuId || simPrice <= 0) return;
		setSimLoading(true);
		const output = await simulatePriceChange(
			skuId,
			simPrice,
			simFestivalBoost,
		);
		setSimResult(output);
		setSimLoading(false);
	};

	useEffect(() => {
		if (skuId && simPrice > 0) {
			runSimulation();
		}
	}, [skuId]);

	if (loading) {
		return (
			<div className="flex items-center justify-center h-80">
				<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	if (!record) {
		return (
			<div className="text-center py-20 text-slate-500">
				<p className="text-lg font-semibold">SKU not found</p>
				<Link
					href="/skus"
					className="text-blue-600 text-sm mt-2 inline-block hover:underline"
				>
					Back to SKUs
				</Link>
			</div>
		);
	}

	const sku = record.sku;
	const skuFeatures = Object.entries(sku.features ?? {});
	const optimization = pricing?.optimization;
	const primaryPrice = record.listing?.price ?? 0;

	return (
		<div className="space-y-5">
			<div>
				<Link
					href="/skus"
					className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 mb-3"
				>
					<ArrowLeft size={14} /> Back to SKU Manager
				</Link>
				<div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-cyan-50 via-white to-blue-50 p-4 md:p-5">
					<div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-blue-100/60 blur-2xl" />
					<div className="relative flex flex-col lg:flex-row lg:items-start gap-4">
						<div className="w-full max-w-[220px]">
							<div className="aspect-square rounded-xl overflow-hidden border border-slate-200 bg-white shadow-sm">
								{sku.imageUrl ? (
									<img
										src={sku.imageUrl}
										alt={sku.name}
										className="w-full h-full object-cover"
									/>
								) : (
									<div className="w-full h-full bg-gradient-to-br from-blue-100 via-cyan-50 to-emerald-100 flex flex-col items-center justify-center text-blue-700">
										<span className="text-3xl font-bold">
											{sku.name.slice(0, 2).toUpperCase()}
										</span>
										<span className="text-xs text-blue-600 mt-2 px-3 text-center">
											Add image URL in SKU edit to brand this view
										</span>
									</div>
								)}
							</div>
						</div>

						<div className="flex-1 min-w-0">
							<h2 className="text-xl font-bold text-slate-800">
								{sku.name}
							</h2>
							<div className="flex flex-wrap items-center gap-2 mt-1.5">
								<span className="text-xs text-slate-500">
									{sku.category} · {sku.id}
								</span>
								<SensitivityBadge value={sku.demandScale} />
								<SensitivityBadge value={sku.priceSensitivity} />
								<SensitivityBadge value={sku.festivalSensitivity} />
							</div>
							<p className="text-sm text-slate-600 mt-3 leading-relaxed">
								{sku.description?.trim() ||
									"No product description yet. Add one in Edit SKU to improve catalog context."}
							</p>
							{skuFeatures.length > 0 && (
								<div className="mt-3 flex flex-wrap gap-2">
									{skuFeatures.map(([key, value]) => (
										<span
											key={`${key}-${value}`}
											className="text-xs px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-700"
										>
											<strong>{key}:</strong> {value}
										</span>
									))}
								</div>
							)}
						</div>

						{optimization && (
							<div className="grid grid-cols-2 gap-2 text-right shrink-0 lg:min-w-[260px]">
								<div className="bg-white rounded-lg border border-slate-200 px-4 py-2">
									<p className="text-xs text-slate-500">
										Current Price
									</p>
									<p className="font-bold text-slate-800 text-lg">
										₹{optimization.currentPrice}
									</p>
								</div>
								<div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2">
									<p className="text-xs text-emerald-600">
										Optimal Price
									</p>
									<p className="font-bold text-emerald-700 text-lg">
										₹{optimization.optimalPrice}
									</p>
								</div>
							</div>
						)}
					</div>
				</div>
			</div>

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<h3 className="font-semibold text-slate-800 mb-1">
					Optimization Reasoning
				</h3>
				<p className="text-xs text-slate-500 mb-4">
					Profit curve is fully computed from demand semantics and
					competitor context.
				</p>
				{optimization ? (
					<>
						<ResponsiveContainer width="100%" height={280}>
							<LineChart
								data={optimization.profitCurve}
								margin={{
									top: 10,
									right: 20,
									left: 0,
									bottom: 0,
								}}
							>
								<CartesianGrid
									strokeDasharray="3 3"
									stroke="#f1f5f9"
								/>
								<XAxis
									dataKey="price"
									tickFormatter={(v) => `₹${v}`}
									tick={{ fontSize: 11, fill: "#94a3b8" }}
									axisLine={false}
									tickLine={false}
								/>
								<YAxis
									tickFormatter={(v) => `₹${v}`}
									tick={{ fontSize: 11, fill: "#94a3b8" }}
									axisLine={false}
									tickLine={false}
									width={55}
								/>
								<Tooltip
									formatter={(val) => [
										`₹${Number(val ?? 0).toFixed(0)}`,
										"Profit / day",
									]}
									labelFormatter={(l) => `Price: ₹${l}`}
									contentStyle={{
										fontSize: 12,
										borderRadius: 8,
										border: "1px solid #e2e8f0",
									}}
								/>
								<Line
									type="monotone"
									dataKey="profit"
									stroke="#3b82f6"
									strokeWidth={2.5}
									dot={false}
								/>
								<ReferenceLine
									x={optimization.currentPrice}
									stroke="#f59e0b"
									strokeDasharray="4 4"
								/>
								<ReferenceLine
									x={optimization.optimalPrice}
									stroke="#10b981"
									strokeDasharray="4 4"
								/>
							</LineChart>
						</ResponsiveContainer>
						<div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
							<div className="bg-slate-50 rounded-lg border border-slate-100 p-3">
								<p className="text-xs text-slate-500">
									Estimated Demand
								</p>
								<p className="font-semibold text-slate-800">
									{optimization.estimatedDemand.toFixed(2)}
									/day
								</p>
							</div>
							<div className="bg-slate-50 rounded-lg border border-slate-100 p-3">
								<p className="text-xs text-slate-500">
									Comp. Min / Avg
								</p>
								<p className="font-semibold text-slate-800">
									₹{optimization.minCompPrice} / ₹
									{optimization.avgCompPrice}
								</p>
							</div>
							<div className="bg-slate-50 rounded-lg border border-slate-100 p-3">
								<p className="text-xs text-slate-500">
									Recommended Band
								</p>
								<p className="font-semibold text-slate-800">
									₹{optimization.recommendedMin} - ₹
									{optimization.recommendedMax}
								</p>
							</div>
							<div className="bg-emerald-50 rounded-lg border border-emerald-100 p-3">
								<p className="text-xs text-emerald-700">
									Profit Delta / day
								</p>
								<p className="font-semibold text-emerald-700">
									{formatINR(
										optimization.estimatedProfitChange,
									)}
								</p>
							</div>
						</div>
					</>
				) : (
					<p className="text-sm text-slate-500">
						Pricing analysis is unavailable for this SKU.
					</p>
				)}
			</div>

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<div className="flex items-center justify-between gap-2 mb-3">
					<h3 className="font-semibold text-slate-800">
						Listings, Competitors, and Computed Metrics
					</h3>
					<select
						value={activeListingRow?.listing.id || ""}
						onChange={(e) => {
							setActiveListingId(e.target.value);
							const row = listingRows.find(
								(it) => it.listing.id === e.target.value,
							);
							if (row) setSimPrice(row.listing.price);
						}}
						className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white"
					>
						{listingRows.map((row) => (
							<option key={row.listing.id} value={row.listing.id}>
								{row.listing.marketplace} ({row.listing.id})
							</option>
						))}
					</select>
				</div>

				{listingRows.length === 0 ? (
					<p className="text-sm text-slate-500">
						No listings available. Create one from
						inventory/listings page.
					</p>
				) : (
					<>
						<div className="overflow-x-auto">
							<table className="w-full text-sm">
								<thead>
									<tr className="border-b border-slate-100 bg-slate-50">
										<th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">
											Marketplace
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Price
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Cost
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Inventory
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Demand
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Profit/day
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Reorder Qty
										</th>
									</tr>
								</thead>
								<tbody>
									{listingRows.map((row) => (
										<tr
											key={row.listing.id}
											className="border-b border-slate-100 last:border-0"
										>
											<td className="px-4 py-3.5">
												<MarketplaceBadge
													value={
														row.listing.marketplace
													}
												/>
											</td>
											<td className="px-3 py-3.5 text-right font-mono">
												₹{row.listing.price}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-600">
												₹{row.listing.cost}
											</td>
											<td className="px-3 py-3.5 text-right font-mono">
												{row.listing.inventory}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-blue-700">
												{row.computed.demand.toFixed(2)}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-emerald-700">
												{formatINR(row.computed.profit)}
											</td>
											<td className="px-3 py-3.5 text-right font-mono">
												{row.computed.reorderQty}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>

						<div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
							<div className="border border-slate-100 rounded-xl p-4">
								<h4 className="font-medium text-slate-800 mb-2">
									Active Listing Computed Block
								</h4>
								<div className="text-sm text-slate-600 space-y-1">
									<p>
										Revenue/day:{" "}
										<strong>
											{formatINR(
												activeListingRow?.computed
													.revenue ?? 0,
											)}
										</strong>
									</p>
									<p>
										Profit/day:{" "}
										<strong>
											{formatINR(
												activeListingRow?.computed
													.profit ?? 0,
											)}
										</strong>
									</p>
									<p>
										Avg competitor price:{" "}
										<strong>
											₹
											{activeListingRow?.computed
												.avgCompPrice ?? 0}
										</strong>
									</p>
									<p>
										Min competitor price:{" "}
										<strong>
											₹
											{activeListingRow?.computed
												.minCompPrice ?? 0}
										</strong>
									</p>
									<p>
										Days to stockout:{" "}
										<strong>
											{activeListingRow?.computed
												.daysToStockout ?? 999}
										</strong>
									</p>
								</div>
							</div>
							<div className="border border-slate-100 rounded-xl p-4">
								<h4 className="font-medium text-slate-800 mb-2">
									Competitors (Active Listing)
								</h4>
								{!activeListingRow ||
								activeListingRow.competitors.length === 0 ? (
									<p className="text-sm text-slate-500">
										No competitors recorded.
									</p>
								) : (
									<div className="space-y-2">
										{activeListingRow.competitors.map(
											(comp) => (
												<div
													key={comp.id}
													className="flex items-center justify-between text-sm border-b border-slate-100 pb-1 last:border-0"
												>
													<span className="text-slate-700">
														{comp.name}
													</span>
													<span className="font-mono text-slate-600">
														₹{comp.price}
													</span>
												</div>
											),
										)}
									</div>
								)}
							</div>
						</div>
					</>
				)}
			</div>

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<h3 className="font-semibold text-slate-800 mb-1">
					Scenario Simulator
				</h3>
				<p className="text-xs text-slate-500 mb-4">
					Simulate price and festival effect. Competitor influence
					remains system-derived.
				</p>
				<div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
					<div className="lg:col-span-2 space-y-3">
						<div>
							<div className="flex justify-between text-xs mb-1.5">
								<label className="text-slate-600 font-medium">
									Your Price
								</label>
								<span className="font-bold text-blue-600">
									₹{simPrice}
								</span>
							</div>
							<input
								type="range"
								min={Math.round(
									(activeListingRow?.listing.cost ??
										primaryPrice) * 1.01,
								)}
								max={Math.round(
									(activeListingRow?.listing.price ??
										primaryPrice) * 1.5,
								)}
								value={simPrice}
								onChange={(e) =>
									setSimPrice(Number(e.target.value))
								}
								className="w-full h-2 rounded-lg appearance-none bg-slate-200 accent-blue-500"
							/>
						</div>
						<div className="flex items-center justify-between py-2 border-t border-slate-100">
							<label className="text-sm text-slate-600 font-medium">
								Festival Demand Boost
							</label>
							<button
								onClick={() => setSimFestivalBoost((v) => !v)}
								className={clsx(
									"relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
									simFestivalBoost
										? "bg-blue-600"
										: "bg-slate-200",
								)}
							>
								<span
									className={clsx(
										"inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
										simFestivalBoost
											? "translate-x-6"
											: "translate-x-1",
									)}
								/>
							</button>
						</div>
						<button
							onClick={runSimulation}
							disabled={simLoading}
							className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2 px-3 rounded-lg text-sm"
						>
							{simLoading ? "Calculating..." : "Run Simulation"}
						</button>
					</div>

					<div className="space-y-2">
						<div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2.5">
							<p className="text-xs text-blue-600">
								Expected Units (30d)
							</p>
							<p className="font-bold text-blue-800">
								{simResult?.expectedUnits ?? 0}
							</p>
						</div>
						<div className="bg-slate-50 border border-slate-100 rounded-lg px-3 py-2.5">
							<p className="text-xs text-slate-500">
								Demand (daily)
							</p>
							<p className="font-bold text-slate-700">
								{simResult?.demand?.toFixed(2) ?? "0.00"}
							</p>
						</div>
						<div className="bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2.5">
							<p className="text-xs text-emerald-600">
								Profit (30d)
							</p>
							<p className="font-bold text-emerald-700">
								{formatINR(simResult?.profit ?? 0)}
							</p>
						</div>
						<div className="bg-slate-50 border border-slate-100 rounded-lg px-3 py-2.5">
							<p className="text-xs text-slate-500">
								Projected Stockout
							</p>
							<p className="font-bold text-slate-700">
								{simResult?.stockoutDate ?? "-"}
							</p>
						</div>
					</div>
				</div>
			</div>

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<h3 className="font-semibold text-slate-800 mb-2">
					Inventory Planning Snapshot
				</h3>
				<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
					<div className="border border-slate-200 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<Package size={14} className="text-slate-400" />
							<span className="text-xs text-slate-500">
								Stock
							</span>
						</div>
						<p className="text-2xl font-bold text-slate-800">
							{activeListingRow?.listing.inventory ?? 0}
						</p>
					</div>
					<div className="border border-slate-200 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<TrendingUp size={14} className="text-slate-400" />
							<span className="text-xs text-slate-500">
								Demand/day
							</span>
						</div>
						<p className="text-2xl font-bold text-slate-800">
							{activeListingRow?.computed.demand?.toFixed(2) ??
								"0.00"}
						</p>
					</div>
					<div className="border border-slate-200 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<Calendar size={14} className="text-slate-400" />
							<span className="text-xs text-slate-500">
								Days to Stockout
							</span>
						</div>
						<p className="text-2xl font-bold text-slate-800">
							{activeListingRow?.computed.daysToStockout ?? 999}
						</p>
					</div>
					<div className="border border-blue-200 bg-blue-50 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<Zap size={14} className="text-blue-500" />
							<span className="text-xs text-slate-500">
								Reorder Qty
							</span>
						</div>
						<p className="text-2xl font-bold text-blue-700">
							{activeListingRow?.computed.reorderQty ?? 0}
						</p>
					</div>
				</div>
			</div>
		</div>
	);
}
