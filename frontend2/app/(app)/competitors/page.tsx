"use client";

import { useEffect, useState } from "react";
import { getCompetitorData } from "@/lib/services";
import { SKUS } from "@/lib/mockData";
import { CompetitorHistory } from "@/lib/types";
import { MarketplaceBadge, RiskIndicator } from "@/components/Badges";
import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
} from "recharts";
import clsx from "clsx";
import Link from "next/link";

export default function CompetitorsPage() {
	const [selectedSkuId, setSelectedSkuId] = useState(SKUS[0].id);
	const [data, setData] = useState<{
		sku: (typeof SKUS)[0];
		history: CompetitorHistory[];
		undercutFrequency: number;
		risk: string;
	} | null>(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		setLoading(true);
		getCompetitorData(selectedSkuId).then((d) => {
			setData(d);
			setLoading(false);
		});
	}, [selectedSkuId]);

	const skuOptions = SKUS;

	return (
		<div className="space-y-5">
			{/* SKU Selector */}
			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-4">
				<label className="text-sm font-medium text-slate-600 whitespace-nowrap">
					Select SKU:
				</label>
				<select
					value={selectedSkuId}
					onChange={(e) => setSelectedSkuId(e.target.value)}
					className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
				>
					{skuOptions.map((sku) => (
						<option key={sku.id} value={sku.id}>
							{sku.name} ({sku.marketplace})
						</option>
					))}
				</select>
				{data && (
					<Link
						href={`/skus/${selectedSkuId}`}
						className="text-xs text-blue-600 hover:underline whitespace-nowrap"
					>
						View SKU Deep Dive →
					</Link>
				)}
			</div>

			{loading ? (
				<div className="flex items-center justify-center h-80">
					<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
				</div>
			) : data ? (
				<>
					{/* Metrics Row */}
					<div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
						<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
							<p className="text-xs text-slate-500 mb-1">
								Our Current Price
							</p>
							<p className="text-2xl font-bold text-slate-800">
								₹{data.sku.currentPrice}
							</p>
						</div>
						<div
							className={clsx(
								"rounded-xl border shadow-sm p-4",
								data.sku.competitorPrice < data.sku.currentPrice
									? "bg-red-50 border-red-200"
									: "bg-emerald-50 border-emerald-200",
							)}
						>
							<p
								className={clsx(
									"text-xs mb-1",
									data.sku.competitorPrice <
										data.sku.currentPrice
										? "text-red-500"
										: "text-emerald-600",
								)}
							>
								Competitor Price
							</p>
							<p
								className={clsx(
									"text-2xl font-bold",
									data.sku.competitorPrice <
										data.sku.currentPrice
										? "text-red-700"
										: "text-emerald-700",
								)}
							>
								₹{data.sku.competitorPrice}
							</p>
							<p className="text-xs mt-0.5">
								{data.sku.competitorPrice <
								data.sku.currentPrice ? (
									<span className="text-red-500 font-medium">
										₹
										{data.sku.currentPrice -
											data.sku.competitorPrice}{" "}
										cheaper than you
									</span>
								) : (
									<span className="text-emerald-600 font-medium">
										₹
										{data.sku.competitorPrice -
											data.sku.currentPrice}{" "}
										more expensive
									</span>
								)}
							</p>
						</div>
						<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
							<p className="text-xs text-slate-500 mb-1">
								Undercut Frequency (30d)
							</p>
							<p className="text-2xl font-bold text-orange-600">
								{data.undercutFrequency}%
							</p>
							<p className="text-xs text-slate-400 mt-0.5">
								of days competitor was cheaper
							</p>
						</div>
						<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
							<p className="text-xs text-slate-500 mb-2">
								Competitor Risk
							</p>
							<RiskIndicator
								value={data.risk as "High" | "Medium" | "Low"}
							/>
						</div>
					</div>

					{/* Price History Chart */}
					<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
						<div className="flex items-center justify-between mb-1">
							<h3 className="font-semibold text-slate-800">
								30-Day Price History
							</h3>
							<MarketplaceBadge value={data.sku.marketplace} />
						</div>
						<p className="text-xs text-slate-500 mb-4">
							Track price movements vs. your top competitor over
							the past 30 days
						</p>
						<ResponsiveContainer width="100%" height={300}>
							<LineChart
								data={data.history}
								margin={{
									top: 5,
									right: 20,
									bottom: 5,
									left: 0,
								}}
							>
								<CartesianGrid
									strokeDasharray="3 3"
									stroke="#f1f5f9"
								/>
								<XAxis
									dataKey="date"
									tick={{ fontSize: 10, fill: "#94a3b8" }}
									axisLine={false}
									tickLine={false}
									interval={4}
								/>
								<YAxis
									tickFormatter={(v) => `₹${v}`}
									tick={{ fontSize: 11, fill: "#94a3b8" }}
									axisLine={false}
									tickLine={false}
									width={55}
									domain={["auto", "auto"]}
								/>
								<Tooltip
									formatter={(val, name) => [
										`₹${val}`,
										name === "ourPrice"
											? "Our Price"
											: "Competitor Price",
									]}
									contentStyle={{
										fontSize: 12,
										borderRadius: 8,
										border: "1px solid #e2e8f0",
									}}
								/>
								<Legend
									formatter={(v) =>
										v === "ourPrice"
											? "Our Price"
											: "Competitor Price"
									}
								/>
								<Line
									type="monotone"
									dataKey="ourPrice"
									stroke="#3b82f6"
									strokeWidth={2.5}
									dot={false}
									name="ourPrice"
								/>
								<Line
									type="monotone"
									dataKey="competitorPrice"
									stroke="#ef4444"
									strokeWidth={2}
									strokeDasharray="5 5"
									dot={false}
									name="competitorPrice"
								/>
							</LineChart>
						</ResponsiveContainer>
					</div>

					{/* Risk Breakdown */}
					<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
						<h3 className="font-semibold text-slate-800 mb-4">
							Risk Assessment
						</h3>
						<div className="space-y-3">
							{[
								{
									label: "Buy Box Loss Risk",
									value:
										data.sku.competitorRisk === "High"
											? 78
											: data.sku.competitorRisk ===
												  "Medium"
												? 42
												: 15,
									color: "bg-red-500",
								},
								{
									label: "Demand Diversion Risk",
									value:
										data.sku.priceSensitivity === "High"
											? 72
											: data.sku.priceSensitivity ===
												  "Medium"
												? 44
												: 18,
									color: "bg-orange-400",
								},
								{
									label: "Price War Escalation Risk",
									value: data.undercutFrequency,
									color: "bg-yellow-400",
								},
							].map(({ label, value, color }) => (
								<div key={label}>
									<div className="flex justify-between text-sm mb-1.5">
										<span className="text-slate-600">
											{label}
										</span>
										<span className="font-semibold text-slate-700">
											{value}%
										</span>
									</div>
									<div className="h-2 bg-slate-100 rounded-full overflow-hidden">
										<div
											className={clsx(
												"h-full rounded-full transition-all",
												color,
											)}
											style={{ width: `${value}%` }}
										/>
									</div>
								</div>
							))}
						</div>
						<div className="mt-4 p-3 bg-blue-50 rounded-lg text-xs text-blue-700 border border-blue-100">
							<strong>Recommendation:</strong>{" "}
							{data.sku.competitorRisk === "High"
								? `Match competitor at ₹${data.sku.competitorPrice} to recover Buy Box. Estimated profit gain: ₹${((data.sku.currentPrice - data.sku.cost) * data.sku.dailyDemand * 0.3 * 30).toFixed(0)}/month.`
								: data.sku.competitorRisk === "Medium"
									? "Hold current price. Monitor competitor activity for the next 5 days before adjusting."
									: "Your pricing is competitive. No action required."}
						</div>
					</div>
				</>
			) : null}
		</div>
	);
}
