"use client";

import { useEffect, useState } from "react";
import {
	createFestival,
	deleteFestival,
	getFestivalCatalog,
	getFestivalData,
	updateFestival,
} from "@/lib/services";
import { FestivalCatalogItem, FestivalEvent } from "@/lib/types";
import { MarketplaceBadge } from "@/components/Badges";
import Link from "next/link";
import {
	Calendar,
	TrendingUp,
	Package,
	IndianRupee,
	ChevronDown,
	ChevronUp,
} from "lucide-react";
import clsx from "clsx";

function formatINR(n: number) {
	if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
	if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
	return `₹${n}`;
}

function urgencyColor(days: number) {
	if (days <= 30) return "border-red-200 bg-red-50";
	if (days <= 60) return "border-orange-200 bg-orange-50";
	return "border-slate-200 bg-white";
}

function urgencyBadge(days: number) {
	if (days <= 30)
		return (
			<span className="bg-red-100 text-red-700 text-xs font-semibold px-2.5 py-1 rounded-full">
				Urgent — {days}d away
			</span>
		);
	if (days <= 60)
		return (
			<span className="bg-orange-100 text-orange-700 text-xs font-semibold px-2.5 py-1 rounded-full">
				Coming up — {days}d away
			</span>
		);
	return (
		<span className="bg-slate-100 text-slate-600 text-xs font-semibold px-2.5 py-1 rounded-full">
			{days}d away
		</span>
	);
}

export default function FestivalsPage() {
	const [events, setEvents] = useState<FestivalEvent[]>([]);
	const [catalog, setCatalog] = useState<FestivalCatalogItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [expanded, setExpanded] = useState<Set<string>>(new Set());
	const [submitting, setSubmitting] = useState(false);
	const [editingFestivalId, setEditingFestivalId] = useState<string | null>(
		null,
	);
	const [form, setForm] = useState({
		name: "",
		date: "",
		boost: 1.3,
		platformText: "Amazon, Flipkart",
	});
	const [toast, setToast] = useState<{
		type: "success" | "error";
		message: string;
	} | null>(null);

	const showToast = (type: "success" | "error", message: string) => {
		setToast({ type, message });
		window.setTimeout(() => setToast(null), 2800);
	};

	const loadFestivals = async () => {
		setLoading(true);
		const [planner, catalogRows] = await Promise.all([
			getFestivalData(),
			getFestivalCatalog(),
		]);
		setEvents(planner);
		setCatalog(catalogRows);
		if (planner.length > 0) {
			setExpanded(new Set([planner[0].id]));
		}
		setLoading(false);
	};

	useEffect(() => {
		loadFestivals();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const resetForm = () => {
		setEditingFestivalId(null);
		setForm({
			name: "",
			date: "",
			boost: 1.3,
			platformText: "Amazon, Flipkart",
		});
	};

	const submitFestival = async () => {
		if (!form.name.trim() || !form.date) {
			showToast("error", "Festival name and date are required.");
			return;
		}

		const platforms = form.platformText
			.split(",")
			.map((row) => row.trim())
			.filter(Boolean);
		if (platforms.length === 0) {
			showToast("error", "At least one platform is required.");
			return;
		}

		setSubmitting(true);
		try {
			if (!editingFestivalId) {
				await createFestival({
					name: form.name.trim(),
					date: form.date,
					boost: form.boost,
					platform: platforms,
				});
				showToast("success", "Festival created.");
			} else {
				await updateFestival(editingFestivalId, {
					name: form.name.trim(),
					date: form.date,
					boost: form.boost,
					platform: platforms,
				});
				showToast("success", "Festival updated.");
			}
			resetForm();
			await loadFestivals();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error
					? error.message
					: "Festival save failed.",
			);
		} finally {
			setSubmitting(false);
		}
	};

	const startEditFestival = (item: FestivalCatalogItem) => {
		setEditingFestivalId(item.id);
		setForm({
			name: item.name,
			date: item.date,
			boost: item.boost,
			platformText: item.platform.join(", "),
		});
	};

	const removeFestival = async (festivalId: string) => {
		if (!window.confirm("Delete this festival?")) return;
		try {
			await deleteFestival(festivalId);
			showToast("success", "Festival deleted.");
			await loadFestivals();
			if (editingFestivalId === festivalId) resetForm();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Delete failed.",
			);
		}
	};

	const toggle = (id: string) => {
		setExpanded((prev) => {
			const next = new Set(prev);
			next.has(id) ? next.delete(id) : next.add(id);
			return next;
		});
	};

	if (loading) {
		return (
			<div className="flex items-center justify-center h-80">
				<div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
			</div>
		);
	}

	const totalPotential = events.reduce(
		(s, e) =>
			s + e.skuOpportunities.reduce((ss, op) => ss + op.profitImpact, 0),
		0,
	);

	return (
		<div className="space-y-5">
			{toast && (
				<div
					className={`rounded-lg border px-4 py-2 text-sm ${toast.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"}`}
				>
					{toast.message}
				</div>
			)}

			{/* Header Banner */}
			<div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-5 text-white">
				<div className="flex items-center justify-between">
					<div>
						<h2 className="text-lg font-bold mb-1">
							Festival Pricing Planner
						</h2>
						<p className="text-blue-100 text-sm">
							Identify pricing and inventory opportunities ahead
							of key Indian shopping events.
						</p>
					</div>
					<div className="text-right">
						<p className="text-blue-200 text-xs">
							Total Profit Potential
						</p>
						<p className="text-2xl font-bold">
							{formatINR(totalPotential)}
						</p>
						<p className="text-blue-200 text-xs">
							across {events.length} upcoming events
						</p>
					</div>
				</div>
			</div>

			{/* Festival Cards */}
			<div className="space-y-4">
				{events.map((event) => {
					const isOpen = expanded.has(event.id);
					const eventProfit = event.skuOpportunities.reduce(
						(s, op) => s + op.profitImpact,
						0,
					);
					return (
						<div
							key={event.id}
							className={clsx(
								"rounded-xl border shadow-sm overflow-hidden",
								urgencyColor(event.daysUntil),
							)}
						>
							{/* Festival Header */}
							<button
								onClick={() => toggle(event.id)}
								className="w-full px-5 py-4 flex items-center justify-between hover:opacity-80 transition-opacity"
							>
								<div className="flex items-center gap-3">
									<div className="w-10 h-10 bg-white rounded-lg border border-slate-200 flex items-center justify-center shadow-sm">
										<Calendar
											size={18}
											className="text-blue-500"
										/>
									</div>
									<div className="text-left">
										<div className="flex items-center gap-2">
											<h3 className="font-bold text-slate-800">
												{event.name}
											</h3>
											{urgencyBadge(event.daysUntil)}
										</div>
										<div className="flex items-center gap-2 mt-1">
											<p className="text-xs text-slate-500">
												{new Date(
													event.date,
												).toLocaleDateString("en-IN", {
													day: "2-digit",
													month: "long",
													year: "numeric",
												})}
											</p>
											<div className="flex gap-1">
												{event.platform.map((p) => (
													<MarketplaceBadge
														key={p}
														value={p}
													/>
												))}
											</div>
										</div>
									</div>
								</div>
								<div className="flex items-center gap-4">
									<div className="text-right">
										<p className="text-xs text-slate-500">
											Profit Opportunity
										</p>
										<p className="font-bold text-emerald-600">
											{formatINR(eventProfit)}
										</p>
									</div>
									<div className="text-slate-400">
										{isOpen ? (
											<ChevronUp size={18} />
										) : (
											<ChevronDown size={18} />
										)}
									</div>
								</div>
							</button>

							{/* SKU Opportunities Table */}
							{isOpen && (
								<div className="border-t border-slate-200 bg-white">
									<table className="w-full text-sm">
										<thead>
											<tr className="border-b border-slate-100 bg-slate-50">
												<th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">
													SKU
												</th>
												<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
													Current Price
												</th>
												<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
													Festival Price
												</th>
												<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
													Expected Units
												</th>
												<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
													Stock Required
												</th>
												<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
													Profit Impact
												</th>
												<th className="px-3 py-3"></th>
											</tr>
										</thead>
										<tbody>
											{event.skuOpportunities.map(
												(opp) => (
													<tr
														key={opp.skuId}
														className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
													>
														<td className="px-5 py-3.5 font-medium text-slate-800">
															{opp.skuName}
														</td>
														<td className="px-3 py-3.5 text-right font-mono text-slate-500">
															₹{opp.currentPrice}
														</td>
														<td className="px-3 py-3.5 text-right">
															<span
																className={clsx(
																	"font-bold font-mono",
																	opp.suggestedPrice <
																		opp.currentPrice
																		? "text-orange-600"
																		: "text-emerald-600",
																)}
															>
																₹
																{
																	opp.suggestedPrice
																}
																<span className="text-xs ml-1 font-normal">
																	(
																	{opp.suggestedPrice <
																	opp.currentPrice
																		? `-${(((opp.currentPrice - opp.suggestedPrice) / opp.currentPrice) * 100).toFixed(0)}%`
																		: `+${(((opp.suggestedPrice - opp.currentPrice) / opp.currentPrice) * 100).toFixed(0)}%`}
																	)
																</span>
															</span>
														</td>
														<td className="px-3 py-3.5 text-right font-mono text-slate-700">
															{opp.expectedUnits}
														</td>
														<td className="px-3 py-3.5 text-right">
															<span className="font-mono text-slate-700">
																{
																	opp.inventoryRequired
																}
															</span>
														</td>
														<td className="px-3 py-3.5 text-right font-semibold text-emerald-600">
															{formatINR(
																opp.profitImpact,
															)}
														</td>
														<td className="px-3 py-3.5">
															<Link
																href={`/skus/${opp.skuId}`}
																className="text-xs text-blue-600 hover:underline whitespace-nowrap"
															>
																Deep Dive →
															</Link>
														</td>
													</tr>
												),
											)}
										</tbody>
									</table>
								</div>
							)}
						</div>
					);
				})}
			</div>

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
				<div className="px-5 py-4 border-b border-slate-100">
					<h3 className="font-semibold text-slate-800">
						Festival Catalog
					</h3>
					<p className="text-xs text-slate-500 mt-0.5">
						Manage the events used for planning and demand boosts.
					</p>
				</div>

				<div className="px-5 py-4 border-b border-slate-100 bg-slate-50">
					<div className="grid grid-cols-1 md:grid-cols-4 gap-3">
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
							Date
							<input
								type="date"
								value={form.date}
								onChange={(e) =>
									setForm((prev) => ({
										...prev,
										date: e.target.value,
									}))
								}
								className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
							/>
						</label>
						<label className="text-xs text-slate-600">
							Boost
							<input
								type="number"
								step="0.1"
								min={1}
								max={5}
								value={form.boost}
								onChange={(e) =>
									setForm((prev) => ({
										...prev,
										boost: Number(e.target.value),
									}))
								}
								className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
							/>
						</label>
						<label className="text-xs text-slate-600">
							Platforms (comma separated)
							<input
								value={form.platformText}
								onChange={(e) =>
									setForm((prev) => ({
										...prev,
										platformText: e.target.value,
									}))
								}
								className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
							/>
						</label>
					</div>
					<div className="mt-3 flex items-center gap-2">
						<button
							disabled={submitting}
							onClick={submitFestival}
							className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-xs font-semibold px-3 py-2 rounded-lg"
						>
							{editingFestivalId
								? "Save Festival"
								: "Add Festival"}
						</button>
						{editingFestivalId && (
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
									Date
								</th>
								<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
									Boost
								</th>
								<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase">
									Platforms
								</th>
								<th className="px-3 py-3"></th>
							</tr>
						</thead>
						<tbody>
							{catalog.map((item) => (
								<tr
									key={item.id}
									className="border-b border-slate-100 last:border-0"
								>
									<td className="px-5 py-3.5 font-medium text-slate-800">
										{item.name}
									</td>
									<td className="px-3 py-3.5 text-slate-600">
										{item.date}
									</td>
									<td className="px-3 py-3.5 text-right font-mono text-slate-700">
										{item.boost.toFixed(2)}x
									</td>
									<td className="px-3 py-3.5 text-xs text-slate-500">
										{item.platform.join(", ")}
									</td>
									<td className="px-3 py-3.5 text-right">
										<div className="flex items-center justify-end gap-2">
											<button
												onClick={() =>
													startEditFestival(item)
												}
												className="text-xs text-blue-600 hover:underline"
											>
												Edit
											</button>
											<button
												onClick={() =>
													removeFestival(item.id)
												}
												className="text-xs text-red-600 hover:underline"
											>
												Delete
											</button>
										</div>
									</td>
								</tr>
							))}
							{catalog.length === 0 && (
								<tr>
									<td
										colSpan={5}
										className="px-5 py-6 text-sm text-slate-500"
									>
										No festivals configured yet.
									</td>
								</tr>
							)}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
}
