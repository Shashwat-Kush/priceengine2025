"use client";

import { useEffect, useState } from "react";
import {
	createCompetitor,
	deleteCompetitor,
	getCompetitorData,
	getCompetitorItemsBySku,
	getListingsBySku,
	getSKUs,
	updateCompetitor,
} from "@/lib/services";
import {
	CompetitorCreateInput,
	CompetitorHistory,
	CompetitorRecord,
	EngineRecord,
	Listing,
} from "@/lib/types";
import { MarketplaceBadge, RiskIndicator } from "@/components/Badges";
import {
	CartesianGrid,
	Legend,
	Line,
	LineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import clsx from "clsx";
import Link from "next/link";

type CompetitorView = EngineRecord & {
	history: CompetitorHistory[];
	undercutFrequency: number;
	risk: "High" | "Medium" | "Low";
};

const defaultCompetitorForm: CompetitorCreateInput = {
	listingId: "",
	name: "",
	price: 100,
	rating: 4,
	shippingDays: 3,
};

export default function CompetitorsPage() {
	const [skuOptions, setSkuOptions] = useState<EngineRecord[]>([]);
	const [selectedSkuId, setSelectedSkuId] = useState("");
	const [data, setData] = useState<CompetitorView | null>(null);
	const [competitors, setCompetitors] = useState<CompetitorRecord[]>([]);
	const [listings, setListings] = useState<Listing[]>([]);
	const [form, setForm] = useState<CompetitorCreateInput>(
		defaultCompetitorForm,
	);
	const [editingCompetitorId, setEditingCompetitorId] = useState<
		string | null
	>(null);
	const [submitting, setSubmitting] = useState(false);
	const [loading, setLoading] = useState(true);
	const [toast, setToast] = useState<{
		type: "success" | "error";
		message: string;
	} | null>(null);

	const showToast = (type: "success" | "error", message: string) => {
		setToast({ type, message });
		window.setTimeout(() => setToast(null), 2800);
	};

	const loadSkuOptions = async () => {
		setLoading(true);
		const records = await getSKUs();
		setSkuOptions(records);
		setSelectedSkuId((prev) => prev || records[0]?.sku.id || "");
		setLoading(false);
	};

	const loadCompetitorContext = async (skuId: string) => {
		if (!skuId) {
			setData(null);
			setCompetitors([]);
			setListings([]);
			return;
		}

		setLoading(true);
		const [analysis, competitorRows, listingRows] = await Promise.all([
			getCompetitorData(skuId),
			getCompetitorItemsBySku(skuId),
			getListingsBySku(skuId),
		]);

		setData(analysis as CompetitorView | null);
		setCompetitors(competitorRows);
		setListings(listingRows);
		setForm((prev) => ({
			...prev,
			listingId: prev.listingId || listingRows[0]?.id || "",
		}));
		setLoading(false);
	};

	useEffect(() => {
		loadSkuOptions();
	}, []);

	useEffect(() => {
		loadCompetitorContext(selectedSkuId);
	}, [selectedSkuId]);

	const resetForm = () => {
		setEditingCompetitorId(null);
		setForm({
			...defaultCompetitorForm,
			listingId: listings[0]?.id || "",
		});
	};

	const onSubmit = async () => {
		if (!form.listingId || !form.name.trim()) {
			showToast("error", "Listing and competitor name are required.");
			return;
		}

		setSubmitting(true);
		try {
			if (!editingCompetitorId) {
				await createCompetitor({ ...form, name: form.name.trim() });
				showToast("success", "Competitor created.");
			} else {
				await updateCompetitor(editingCompetitorId, {
					listingId: form.listingId,
					name: form.name.trim(),
					price: form.price,
					rating: form.rating,
					shippingDays: form.shippingDays,
				});
				showToast("success", "Competitor updated.");
			}
			resetForm();
			await loadCompetitorContext(selectedSkuId);
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Save failed.",
			);
		} finally {
			setSubmitting(false);
		}
	};

	const onEdit = (competitor: CompetitorRecord) => {
		setEditingCompetitorId(competitor.id);
		setForm({
			listingId: competitor.listingId,
			name: competitor.name,
			price: competitor.price,
			rating: competitor.rating,
			shippingDays: competitor.shippingDays,
		});
	};

	const onDelete = async (competitorId: string) => {
		if (!window.confirm("Delete this competitor record?")) return;
		try {
			await deleteCompetitor(competitorId);
			showToast("success", "Competitor deleted.");
			await loadCompetitorContext(selectedSkuId);
			if (editingCompetitorId === competitorId) resetForm();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Delete failed.",
			);
		}
	};

	const ourPrice = data?.listing?.price ?? 0;
	const cost = data?.listing?.cost ?? 0;
	const minCompPrice = data?.computed.minCompPrice ?? 0;
	const demand = data?.computed.demand ?? 0;

	return (
		<div className="space-y-5">
			{toast && (
				<div
					className={`rounded-lg border px-4 py-2 text-sm ${toast.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"}`}
				>
					{toast.message}
				</div>
			)}

			{!loading && skuOptions.length === 0 && (
				<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 text-sm text-slate-500">
					No SKUs found. Create at least one SKU to start competitor
					tracking.
				</div>
			)}

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-4">
				<label className="text-sm font-medium text-slate-600 whitespace-nowrap">
					Select SKU:
				</label>
				<select
					value={selectedSkuId}
					onChange={(e) => setSelectedSkuId(e.target.value)}
					className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
				>
					{skuOptions.map((record) => (
						<option key={record.sku.id} value={record.sku.id}>
							{record.sku.name} (
							{record.listing?.marketplace || "No listing"})
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
					<div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
						<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
							<p className="text-xs text-slate-500 mb-1">
								Our Current Price
							</p>
							<p className="text-2xl font-bold text-slate-800">
								₹{ourPrice}
							</p>
						</div>
						<div
							className={clsx(
								"rounded-xl border shadow-sm p-4",
								minCompPrice < ourPrice
									? "bg-red-50 border-red-200"
									: "bg-emerald-50 border-emerald-200",
							)}
						>
							<p
								className={clsx(
									"text-xs mb-1",
									minCompPrice < ourPrice
										? "text-red-500"
										: "text-emerald-600",
								)}
							>
								Min Competitor Price
							</p>
							<p
								className={clsx(
									"text-2xl font-bold",
									minCompPrice < ourPrice
										? "text-red-700"
										: "text-emerald-700",
								)}
							>
								₹{minCompPrice}
							</p>
							<p className="text-xs mt-0.5">
								{minCompPrice < ourPrice ? (
									<span className="text-red-500 font-medium">
										₹{(ourPrice - minCompPrice).toFixed(2)}{" "}
										cheaper than you
									</span>
								) : (
									<span className="text-emerald-600 font-medium">
										₹{(minCompPrice - ourPrice).toFixed(2)}{" "}
										higher than your price
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
							<RiskIndicator value={data.risk} />
						</div>
					</div>

					<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
						<div className="flex items-center justify-between mb-1">
							<h3 className="font-semibold text-slate-800">
								30-Day Price History
							</h3>
							<MarketplaceBadge
								value={data.listing?.marketplace || "Amazon"}
							/>
						</div>
						<p className="text-xs text-slate-500 mb-4">
							Track your listing price vs. top competitor over the
							past 30 days.
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

					<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
						<h3 className="font-semibold text-slate-800 mb-4">
							Risk Assessment
						</h3>
						<div className="space-y-3">
							{[
								{
									label: "Buy Box Loss Risk",
									value:
										data.risk === "High"
											? 78
											: data.risk === "Medium"
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
							{data.risk === "High"
								? `Consider closing the gap to ₹${minCompPrice.toFixed(2)}. Estimated monthly upside from reducing undercut pressure: ₹${((ourPrice - cost) * demand * 30 * 0.2).toFixed(0)}.`
								: data.risk === "Medium"
									? "Monitor competitor movements for 5 days and react only if undercut frequency rises above 50%."
									: "Pricing position is stable. Keep current strategy and monitor weekly."}
						</div>
					</div>

					<div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
						<div className="px-5 py-4 border-b border-slate-100">
							<h3 className="font-semibold text-slate-800">
								Competitor Records
							</h3>
							<p className="text-xs text-slate-500 mt-0.5">
								Manage competitors per listing with immediate
								data refresh.
							</p>
						</div>
						<div className="px-5 py-4 border-b border-slate-100 bg-slate-50">
							<div className="grid grid-cols-1 md:grid-cols-5 gap-3">
								<label className="text-xs text-slate-600">
									Listing
									<select
										value={form.listingId}
										onChange={(e) =>
											setForm((prev) => ({
												...prev,
												listingId: e.target.value,
											}))
										}
										className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
									>
										{listings.map((listing) => (
											<option
												key={listing.id}
												value={listing.id}
											>
												{listing.marketplace} (
												{listing.id})
											</option>
										))}
									</select>
								</label>
								<label className="text-xs text-slate-600">
									Name
									<input
										value={form.name}
										onChange={(e) =>
											setForm((prev) => ({
												...prev,
												name: e.target.value,
											}))
										}
										className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
									/>
								</label>
								<label className="text-xs text-slate-600">
									Price
									<input
										type="number"
										value={form.price}
										onChange={(e) =>
											setForm((prev) => ({
												...prev,
												price: Number(e.target.value),
											}))
										}
										className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
									/>
								</label>
								<label className="text-xs text-slate-600">
									Rating
									<input
										type="number"
										step="0.1"
										min={0}
										max={5}
										value={form.rating}
										onChange={(e) =>
											setForm((prev) => ({
												...prev,
												rating: Number(e.target.value),
											}))
										}
										className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
									/>
								</label>
								<label className="text-xs text-slate-600">
									Shipping Days
									<input
										type="number"
										value={form.shippingDays}
										onChange={(e) =>
											setForm((prev) => ({
												...prev,
												shippingDays: Number(
													e.target.value,
												),
											}))
										}
										className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
									/>
								</label>
							</div>
							<div className="mt-3 flex items-center gap-2">
								<button
									disabled={submitting}
									onClick={onSubmit}
									className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-xs font-semibold px-3 py-2 rounded-lg"
								>
									{editingCompetitorId
										? "Save Changes"
										: "Add Competitor"}
								</button>
								{editingCompetitorId && (
									<button
										onClick={resetForm}
										className="text-xs text-slate-600 hover:underline"
									>
										Cancel edit
									</button>
								)}
							</div>
						</div>

						<div className="overflow-x-auto">
							<table className="w-full text-sm">
								<thead>
									<tr className="border-b border-slate-100 bg-slate-50">
										<th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">
											Name
										</th>
										<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Listing
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Price
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Rating
										</th>
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
											Shipping
										</th>
										<th className="px-3 py-3"></th>
									</tr>
								</thead>
								<tbody>
									{competitors.map((row) => (
										<tr
											key={row.id}
											className="border-b border-slate-100 last:border-0"
										>
											<td className="px-5 py-3.5 font-medium text-slate-800">
												{row.name}
											</td>
											<td className="px-3 py-3.5 text-xs text-slate-500">
												{row.marketplace || "Listing"} (
												{row.listingId})
											</td>
											<td className="px-3 py-3.5 text-right font-mono">
												₹{row.price}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-600">
												{row.rating}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-600">
												{row.shippingDays}d
											</td>
											<td className="px-3 py-3.5 text-right">
												<div className="flex items-center justify-end gap-2">
													<button
														onClick={() =>
															onEdit(row)
														}
														className="text-xs text-blue-600 hover:underline"
													>
														Edit
													</button>
													<button
														onClick={() =>
															onDelete(row.id)
														}
														className="text-xs text-red-600 hover:underline"
													>
														Delete
													</button>
												</div>
											</td>
										</tr>
									))}
									{competitors.length === 0 && (
										<tr>
											<td
												colSpan={6}
												className="px-5 py-6 text-sm text-slate-500"
											>
												No competitors recorded for this
												SKU yet.
											</td>
										</tr>
									)}
								</tbody>
							</table>
						</div>
					</div>
				</>
			) : null}
		</div>
	);
}
