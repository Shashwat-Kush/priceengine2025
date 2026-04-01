"use client";

import { useEffect, useState } from "react";
import {
	getSKUById,
	simulatePriceChange,
	getProfitCurve,
} from "@/lib/services";
import { SKU, SimulatorOutput } from "@/lib/types";
import {
	MarketplaceBadge,
	SensitivityBadge,
	InventoryBadge,
	RiskIndicator,
} from "@/components/Badges";
import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ReferenceLine,
	ResponsiveContainer,
} from "recharts";
import Link from "next/link";
import {
	ArrowLeft,
	Zap,
	Calendar,
	ShoppingCart,
	TrendingUp,
	Package,
} from "lucide-react";
import clsx from "clsx";

function formatINR(n: number) {
	if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
	if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
	return `₹${n}`;
}

function DemandDriverCard({
	label,
	value,
	icon,
}: {
	label: string;
	value: string;
	icon: React.ReactNode;
}) {
	const colorMap: Record<string, string> = {
		High: "text-red-600 bg-red-50 border-red-200",
		Medium: "text-orange-600 bg-orange-50 border-orange-200",
		Low: "text-emerald-600 bg-emerald-50 border-emerald-200",
	};
	return (
		<div
			className={clsx(
				"rounded-xl border p-4",
				colorMap[value] ?? "bg-slate-50 border-slate-200",
			)}
		>
			<div className="flex items-center gap-2 mb-2 text-slate-500">
				{icon}
				<span className="text-xs font-medium text-slate-500">
					{label}
				</span>
			</div>
			<p className="font-bold text-lg">{value}</p>
		</div>
	);
}

export default function SKUDetailPage({
	params,
}: {
	params: Promise<{ id: string }>;
}) {
	const [sku, setSku] = useState<SKU | null>(null);
	const [profitCurve, setProfitCurve] = useState<
		{ price: number; profit: number }[]
	>([]);
	const [loading, setLoading] = useState(true);
	const [skuId, setSkuId] = useState<string>("");

	// Simulator state
	const [simPrice, setSimPrice] = useState(0);
	const [simCompPrice, setSimCompPrice] = useState(0);
	const [simFestival, setSimFestival] = useState(false);
	const [simOutput, setSimOutput] = useState<SimulatorOutput | null>(null);
	const [simLoading, setSimLoading] = useState(false);

	useEffect(() => {
		params.then(({ id }) => {
			setSkuId(id);
			Promise.all([getSKUById(id), getProfitCurve(id)]).then(
				([skuData, curveData]) => {
					if (skuData) {
						setSku(skuData);
						setSimPrice(skuData.currentPrice);
						setSimCompPrice(skuData.competitorPrice);
					}
					if (curveData) setProfitCurve(curveData.data);
					setLoading(false);
				},
			);
		});
	}, [params]);

	const handleSimulate = async () => {
		if (!sku) return;
		setSimLoading(true);
		const result = await simulatePriceChange(
			sku,
			simPrice,
			simCompPrice,
			simFestival,
		);
		setSimOutput(result);
		setSimLoading(false);
	};

	useEffect(() => {
		if (sku && simPrice > 0) {
			handleSimulate();
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [sku]);

	if (loading) {
		return (
			<div className="flex items-center justify-center h-80">
				<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	if (!sku) {
		return (
			<div className="text-center py-20 text-slate-500">
				<p className="text-lg font-semibold">SKU not found</p>
				<Link
					href="/skus"
					className="text-blue-600 text-sm mt-2 inline-block hover:underline"
				>
					← Back to SKUs
				</Link>
			</div>
		);
	}

	const optimalPoint = profitCurve.reduce(
		(best, pt) => (pt.profit > best.profit ? pt : best),
		profitCurve[0],
	);
	const daysUntilStockout =
		sku.dailyDemand > 0 ? Math.floor(sku.inventory / sku.dailyDemand) : 999;

	return (
		<div className="space-y-5">
			{/* Breadcrumb + Header */}
			<div>
				<Link
					href="/skus"
					className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 mb-3"
				>
					<ArrowLeft size={14} /> Back to SKU Manager
				</Link>
				<div className="flex items-start justify-between gap-4">
					<div>
						<h2 className="text-xl font-bold text-slate-800">
							{sku.name}
						</h2>
						<div className="flex items-center gap-2 mt-1.5">
							<MarketplaceBadge value={sku.marketplace} />
							<InventoryBadge value={sku.inventoryStatus} />
							<span className="text-xs text-slate-400">
								{sku.category} · {sku.id}
							</span>
						</div>
					</div>
					<div className="flex gap-3 text-right shrink-0">
						<div className="bg-white rounded-lg border border-slate-200 px-4 py-2">
							<p className="text-xs text-slate-500">
								Selling Price
							</p>
							<p className="font-bold text-slate-800 text-lg">
								₹{sku.currentPrice}
							</p>
						</div>
						<div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2">
							<p className="text-xs text-emerald-600">Margin</p>
							<p className="font-bold text-emerald-700 text-lg">
								{sku.margin.toFixed(1)}%
							</p>
						</div>
						<div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-2">
							<p className="text-xs text-orange-600">
								Comp. Price
							</p>
							<p className="font-bold text-orange-700 text-lg">
								₹{sku.competitorPrice}
							</p>
						</div>
					</div>
				</div>
			</div>

			{/* Section A: Profit Curve */}
			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<h3 className="font-semibold text-slate-800 mb-1">
					Price vs Profit Curve
				</h3>
				<p className="text-xs text-slate-500 mb-4">
					Find the sweet spot between price and profit — based on
					demand sensitivity
				</p>
				<ResponsiveContainer width="100%" height={280}>
					<LineChart
						data={profitCurve}
						margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
					>
						<CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
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
								"Daily Profit",
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
							name="Profit"
						/>
						<ReferenceLine
							x={sku.currentPrice}
							stroke="#f59e0b"
							strokeDasharray="4 4"
							strokeWidth={2}
							label={{
								value: "Current",
								position: "top",
								fontSize: 11,
								fill: "#f59e0b",
							}}
						/>
						<ReferenceLine
							x={sku.competitorPrice}
							stroke="#ef4444"
							strokeDasharray="4 4"
							strokeWidth={2}
							label={{
								value: "Competitor",
								position: "top",
								fontSize: 11,
								fill: "#ef4444",
							}}
						/>
						{optimalPoint && (
							<ReferenceLine
								x={optimalPoint.price}
								stroke="#10b981"
								strokeDasharray="4 4"
								strokeWidth={2}
								label={{
									value: "Optimal",
									position: "top",
									fontSize: 11,
									fill: "#10b981",
								}}
							/>
						)}
					</LineChart>
				</ResponsiveContainer>
				{optimalPoint && (
					<div className="flex items-center gap-2 mt-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
						<Zap size={14} className="text-emerald-600" />
						<p className="text-xs text-emerald-700">
							<strong>
								Optimal price: ₹{optimalPoint.price}
							</strong>{" "}
							— maximizes daily profit at ₹
							{optimalPoint.profit.toFixed(0)}. Your current price
							of ₹{sku.currentPrice} earns{" "}
							{(
								((optimalPoint.profit -
									(profitCurve.find(
										(p) => p.price >= sku.currentPrice,
									)?.profit ?? 0)) /
									optimalPoint.profit) *
								100
							).toFixed(1)}
							% less.
						</p>
					</div>
				)}
			</div>

			{/* Section B + Section C side by side */}
			<div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
				{/* Section B: Demand Drivers */}
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
					<h3 className="font-semibold text-slate-800 mb-1">
						Demand Drivers
					</h3>
					<p className="text-xs text-slate-500 mb-4">
						Key factors influencing this SKU&apos;s performance
					</p>
					<div className="grid grid-cols-2 gap-3">
						<DemandDriverCard
							label="Price Sensitivity"
							value={sku.priceSensitivity}
							icon={<TrendingUp size={13} />}
						/>
						<DemandDriverCard
							label="Competitor Sensitivity"
							value={sku.competitorRisk}
							icon={<ShoppingCart size={13} />}
						/>
						<DemandDriverCard
							label="Festival Boost Potential"
							value={sku.festivalBoostPotential}
							icon={<Calendar size={13} />}
						/>
						<DemandDriverCard
							label="Marketplace Strength"
							value={sku.marketplaceStrength}
							icon={<Zap size={13} />}
						/>
					</div>
				</div>

				{/* Section C: Scenario Simulator */}
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
					<h3 className="font-semibold text-slate-800 mb-1">
						Scenario Simulator
					</h3>
					<p className="text-xs text-slate-500 mb-4">
						Change inputs to see projected 30-day outcomes
					</p>
					<div className="space-y-3">
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
								min={Math.round(sku.cost * 1.05)}
								max={Math.round(sku.currentPrice * 1.5)}
								value={simPrice}
								onChange={(e) =>
									setSimPrice(Number(e.target.value))
								}
								className="w-full h-2 rounded-lg appearance-none bg-slate-200 accent-blue-500"
							/>
							<div className="flex justify-between text-xs text-slate-400 mt-0.5">
								<span>₹{Math.round(sku.cost * 1.05)}</span>
								<span>
									₹{Math.round(sku.currentPrice * 1.5)}
								</span>
							</div>
						</div>
						<div>
							<div className="flex justify-between text-xs mb-1.5">
								<label className="text-slate-600 font-medium">
									Competitor Price
								</label>
								<span className="font-bold text-orange-600">
									₹{simCompPrice}
								</span>
							</div>
							<input
								type="range"
								min={Math.round(sku.cost * 1.0)}
								max={Math.round(sku.currentPrice * 1.6)}
								value={simCompPrice}
								onChange={(e) =>
									setSimCompPrice(Number(e.target.value))
								}
								className="w-full h-2 rounded-lg appearance-none bg-slate-200 accent-orange-400"
							/>
						</div>
						<div className="flex items-center justify-between py-2 border-t border-slate-100">
							<label className="text-sm text-slate-600 font-medium">
								Festival Demand Boost
							</label>
							<button
								onClick={() => setSimFestival((v) => !v)}
								className={clsx(
									"relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
									simFestival
										? "bg-blue-600"
										: "bg-slate-200",
								)}
							>
								<span
									className={clsx(
										"inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
										simFestival
											? "translate-x-6"
											: "translate-x-1",
									)}
								/>
							</button>
						</div>
						<button
							onClick={handleSimulate}
							disabled={simLoading}
							className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
						>
							{simLoading ? "Calculating…" : "Run Simulation"}
						</button>

						{simOutput && (
							<div className="mt-2 grid grid-cols-2 gap-2">
								<div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2.5">
									<p className="text-xs text-blue-600">
										Expected Units (30d)
									</p>
									<p className="font-bold text-blue-800">
										{simOutput.expectedUnits}
									</p>
								</div>
								<div className="bg-slate-50 border border-slate-100 rounded-lg px-3 py-2.5">
									<p className="text-xs text-slate-500">
										Revenue (30d)
									</p>
									<p className="font-bold text-slate-700">
										{formatINR(simOutput.revenue)}
									</p>
								</div>
								<div className="bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2.5">
									<p className="text-xs text-emerald-600">
										Profit (30d)
									</p>
									<p className="font-bold text-emerald-700">
										{formatINR(simOutput.profit)}
									</p>
								</div>
								<div
									className={clsx(
										"border rounded-lg px-3 py-2.5",
										daysUntilStockout <= 7
											? "bg-red-50 border-red-100"
											: "bg-slate-50 border-slate-100",
									)}
								>
									<p
										className={clsx(
											"text-xs",
											daysUntilStockout <= 7
												? "text-red-500"
												: "text-slate-500",
										)}
									>
										Stockout Date
									</p>
									<p
										className={clsx(
											"font-bold text-sm",
											daysUntilStockout <= 7
												? "text-red-700"
												: "text-slate-700",
										)}
									>
										{simOutput.stockoutDate}
									</p>
								</div>
							</div>
						)}
					</div>
				</div>
			</div>

			{/* Section D: Inventory Planning */}
			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<h3 className="font-semibold text-slate-800 mb-1">
					Inventory Planning
				</h3>
				<p className="text-xs text-slate-500 mb-4">
					Stock levels, demand, and reorder recommendations
				</p>
				<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
					<div className="border border-slate-200 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<Package size={14} className="text-slate-400" />
							<span className="text-xs text-slate-500">
								Current Stock
							</span>
						</div>
						<p className="text-2xl font-bold text-slate-800">
							{sku.inventory}
						</p>
						<p className="text-xs text-slate-400 mt-0.5">units</p>
					</div>
					<div className="border border-slate-200 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<TrendingUp size={14} className="text-slate-400" />
							<span className="text-xs text-slate-500">
								Daily Demand
							</span>
						</div>
						<p className="text-2xl font-bold text-slate-800">
							{sku.dailyDemand}
						</p>
						<p className="text-xs text-slate-400 mt-0.5">
							units / day
						</p>
					</div>
					<div
						className={clsx(
							"border rounded-xl p-4",
							daysUntilStockout <= 7
								? "border-red-200 bg-red-50"
								: daysUntilStockout <= 14
									? "border-orange-200 bg-orange-50"
									: "border-slate-200",
						)}
					>
						<div className="flex items-center gap-2 mb-2">
							<Calendar
								size={14}
								className={
									daysUntilStockout <= 7
										? "text-red-400"
										: "text-slate-400"
								}
							/>
							<span className="text-xs text-slate-500">
								Days Until Stockout
							</span>
						</div>
						<p
							className={clsx(
								"text-2xl font-bold",
								daysUntilStockout <= 7
									? "text-red-700"
									: daysUntilStockout <= 14
										? "text-orange-700"
										: "text-slate-800",
							)}
						>
							{daysUntilStockout >= 999 ? "∞" : daysUntilStockout}
						</p>
						<p className="text-xs text-slate-400 mt-0.5">
							days remaining
						</p>
					</div>
					<div className="border border-blue-200 bg-blue-50 rounded-xl p-4">
						<div className="flex items-center gap-2 mb-2">
							<Zap size={14} className="text-blue-500" />
							<span className="text-xs text-slate-500">
								Reorder Suggestion
							</span>
						</div>
						<p className="text-2xl font-bold text-blue-700">
							{Math.max(
								0,
								Math.ceil(
									sku.dailyDemand * sku.leadTimeDays * 2.4 -
										sku.inventory,
								),
							)}
						</p>
						<p className="text-xs text-slate-400 mt-0.5">
							units recommended
						</p>
					</div>
				</div>
				<div className="mt-3 bg-slate-50 rounded-lg px-4 py-3 text-xs text-slate-600">
					Lead time: <strong>{sku.leadTimeDays} days</strong> ·
					Storage cost:{" "}
					<strong>₹{sku.storageCostPerUnit}/unit/month</strong> ·
					Reorder point:{" "}
					<strong>
						{Math.round(sku.dailyDemand * sku.leadTimeDays * 1.2)}{" "}
						units
					</strong>
				</div>
			</div>
		</div>
	);
}
