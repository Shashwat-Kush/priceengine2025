"use client";

import { useEffect, useState } from "react";
import { getPortfolioAnalytics } from "@/lib/services";
import { PortfolioDataPoint } from "@/lib/types";
import {
	ScatterChart,
	Scatter,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	ResponsiveContainer,
	BarChart,
	Bar,
	Cell,
	PieChart,
	Pie,
	Legend,
} from "recharts";

const mpColors: Record<string, string> = {
	Amazon: "#f97316",
	Flipkart: "#3b82f6",
	Meesho: "#ec4899",
};

function formatINR(n: number) {
	if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
	if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
	return `₹${n}`;
}

export default function PortfolioPage() {
	const [data, setData] = useState<PortfolioDataPoint[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		getPortfolioAnalytics().then((d) => {
			setData(d);
			setLoading(false);
		});
	}, []);

	if (loading) {
		return (
			<div className="flex items-center justify-center h-80">
				<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	// Marketplace distribution
	const mpCount = data.reduce(
		(acc, d) => {
			acc[d.marketplace] = (acc[d.marketplace] || 0) + 1;
			return acc;
		},
		{} as Record<string, number>,
	);
	const pieData = Object.entries(mpCount).map(([name, value]) => ({
		name,
		value,
	}));

	// Bar chart data sorted by profit descending
	const barData = [...data].sort((a, b) => b.profit - a.profit);

	const sensitivityLabels = ["", "Low", "Medium", "High"];

	return (
		<div className="space-y-5">
			{/* Summary Cards */}
			<div className="grid grid-cols-3 gap-4">
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
					<p className="text-xs text-slate-500 mb-1">Total SKUs</p>
					<p className="text-2xl font-bold text-slate-800">
						{data.length}
					</p>
				</div>
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
					<p className="text-xs text-slate-500 mb-1">Avg Margin</p>
					<p className="text-2xl font-bold text-emerald-600">
						{(
							data.reduce((s, d) => s + d.margin, 0) / data.length
						).toFixed(1)}
						%
					</p>
				</div>
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
					<p className="text-xs text-slate-500 mb-1">
						Total Est. Monthly Profit
					</p>
					<p className="text-2xl font-bold text-slate-800">
						{formatINR(data.reduce((s, d) => s + d.profit, 0))}
					</p>
				</div>
			</div>

			<div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
				{/* Scatter Plot */}
				<div className="lg:col-span-2 bg-white rounded-xl border border-slate-100 shadow-sm p-5">
					<h3 className="font-semibold text-slate-800 mb-1">
						Margin vs Price Sensitivity
					</h3>
					<p className="text-xs text-slate-500 mb-4">
						Top-right = high-margin, high demand sensitivity
						(risky). Bottom-left = stable SKUs.
					</p>
					<ResponsiveContainer width="100%" height={300}>
						<ScatterChart
							margin={{ top: 10, right: 20, bottom: 20, left: 0 }}
						>
							<CartesianGrid
								strokeDasharray="3 3"
								stroke="#f1f5f9"
							/>
							<XAxis
								dataKey="priceSensitivity"
								name="Sensitivity"
								type="number"
								domain={[0.5, 3.5]}
								tickCount={3}
								tickFormatter={(v) =>
									sensitivityLabels[v] ?? ""
								}
								tick={{ fontSize: 11, fill: "#94a3b8" }}
								axisLine={false}
								tickLine={false}
								label={{
									value: "Price Sensitivity →",
									position: "insideBottom",
									offset: -12,
									fontSize: 11,
									fill: "#94a3b8",
								}}
							/>
							<YAxis
								dataKey="margin"
								name="Margin"
								tickFormatter={(v) => `${v}%`}
								tick={{ fontSize: 11, fill: "#94a3b8" }}
								axisLine={false}
								tickLine={false}
								width={45}
							/>
							<Tooltip
								cursor={{ strokeDasharray: "3 3" }}
								content={({ payload }) => {
									if (!payload?.length) return null;
									const d = payload[0]
										.payload as PortfolioDataPoint;
									return (
										<div className="bg-white border border-slate-200 rounded-lg px-3 py-2 shadow text-xs">
											<p className="font-semibold text-slate-800">
												{d.name}
											</p>
											<p className="text-slate-500">
												{d.marketplace}
											</p>
											<p className="text-emerald-600">
												Margin: {d.margin.toFixed(1)}%
											</p>
											<p className="text-blue-600">
												Profit: {formatINR(d.profit)}/mo
											</p>
										</div>
									);
								}}
							/>
							{["Amazon", "Flipkart", "Meesho"].map((mp) => (
								<Scatter
									key={mp}
									name={mp}
									data={data.filter(
										(d) => d.marketplace === mp,
									)}
									fill={mpColors[mp]}
									opacity={0.85}
								/>
							))}
						</ScatterChart>
					</ResponsiveContainer>
					<div className="flex gap-4 mt-2 justify-center">
						{Object.entries(mpColors).map(([mp, color]) => (
							<div key={mp} className="flex items-center gap-1.5">
								<div
									className="w-3 h-3 rounded-full"
									style={{ backgroundColor: color }}
								/>
								<span className="text-xs text-slate-500">
									{mp}
								</span>
							</div>
						))}
					</div>
				</div>

				{/* Pie Chart */}
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
					<h3 className="font-semibold text-slate-800 mb-1">
						Marketplace Mix
					</h3>
					<p className="text-xs text-slate-500 mb-4">
						Distribution of SKUs across platforms
					</p>
					<ResponsiveContainer width="100%" height={220}>
						<PieChart>
							<Pie
								data={pieData}
								cx="50%"
								cy="50%"
								innerRadius={55}
								outerRadius={85}
								paddingAngle={3}
								dataKey="value"
								label={({ name, percent }) =>
									`${name} ${((percent ?? 0) * 100).toFixed(0)}%`
								}
								labelLine={false}
							>
								{pieData.map((entry) => (
									<Cell
										key={entry.name}
										fill={mpColors[entry.name] ?? "#94a3b8"}
									/>
								))}
							</Pie>
							<Tooltip
								formatter={(val) => [
									`${val} SKUs`,
									"Count",
								]}
							/>
						</PieChart>
					</ResponsiveContainer>
					<div className="mt-3 space-y-1.5">
						{pieData.map(({ name, value }) => (
							<div
								key={name}
								className="flex items-center justify-between text-sm"
							>
								<div className="flex items-center gap-2">
									<div
										className="w-2.5 h-2.5 rounded-full"
										style={{
											backgroundColor: mpColors[name],
										}}
									/>
									<span className="text-slate-600">
										{name}
									</span>
								</div>
								<span className="font-semibold text-slate-700">
									{value} SKUs
								</span>
							</div>
						))}
					</div>
				</div>
			</div>

			{/* Bar Chart */}
			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
				<h3 className="font-semibold text-slate-800 mb-1">
					Monthly Profit by SKU
				</h3>
				<p className="text-xs text-slate-500 mb-4">
					Estimated 30-day profit contribution per SKU
				</p>
				<ResponsiveContainer width="100%" height={260}>
					<BarChart
						data={barData}
						margin={{ top: 5, right: 20, left: 0, bottom: 60 }}
					>
						<CartesianGrid
							strokeDasharray="3 3"
							stroke="#f1f5f9"
							vertical={false}
						/>
						<XAxis
							dataKey="name"
							tick={{ fontSize: 10, fill: "#94a3b8" }}
							axisLine={false}
							tickLine={false}
							angle={-35}
							textAnchor="end"
							interval={0}
						/>
						<YAxis
							tickFormatter={(v) => formatINR(v)}
							tick={{ fontSize: 11, fill: "#94a3b8" }}
							axisLine={false}
							tickLine={false}
							width={55}
						/>
						<Tooltip
							formatter={(val) => [
								formatINR(Number(val ?? 0)),
								"Monthly Profit",
							]}
							contentStyle={{
								fontSize: 12,
								borderRadius: 8,
								border: "1px solid #e2e8f0",
							}}
						/>
						<Bar dataKey="profit" radius={[4, 4, 0, 0]}>
							{barData.map((entry) => (
								<Cell
									key={entry.skuId}
									fill={mpColors[entry.marketplace]}
									opacity={0.85}
								/>
							))}
						</Bar>
					</BarChart>
				</ResponsiveContainer>
			</div>
		</div>
	);
}
