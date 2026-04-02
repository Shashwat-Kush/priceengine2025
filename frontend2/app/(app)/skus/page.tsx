"use client";

import { useEffect, useState } from "react";
import { createSKU, deleteSKU, getSKUs, updateSKU } from "@/lib/services";
import { EngineRecord, SKUCreateInput, SKUProfile } from "@/lib/types";
import Link from "next/link";
import { ChevronRight, Filter, Search } from "lucide-react";

const defaultForm: SKUCreateInput = {
	id: "",
	name: "",
	category: "General",
	demandScale: "medium",
	priceSensitivity: "medium",
	festivalSensitivity: "medium",
};

function mapSkuToForm(sku: SKUProfile): SKUCreateInput {
	return {
		id: sku.id,
		name: sku.name,
		category: sku.category,
		demandScale: sku.demandScale.toLowerCase() as "low" | "medium" | "high",
		priceSensitivity: sku.priceSensitivity.toLowerCase() as
			| "low"
			| "medium"
			| "high",
		festivalSensitivity: sku.festivalSensitivity.toLowerCase() as
			| "low"
			| "medium"
			| "high",
	};
}

export default function SKUsPage() {
	const [records, setRecords] = useState<EngineRecord[]>([]);
	const [loading, setLoading] = useState(true);
	const [submitting, setSubmitting] = useState(false);

	const [search, setSearch] = useState("");
	const [filterDemand, setFilterDemand] = useState("");
	const [filterPriceSensitivity, setFilterPriceSensitivity] = useState("");

	const [modalMode, setModalMode] = useState<"create" | "edit" | null>(null);
	const [form, setForm] = useState<SKUCreateInput>(defaultForm);
	const [toast, setToast] = useState<{
		type: "success" | "error";
		message: string;
	} | null>(null);

	const showToast = (type: "success" | "error", message: string) => {
		setToast({ type, message });
		window.setTimeout(() => setToast(null), 2800);
	};

	const loadSkus = async () => {
		setLoading(true);
		const data = await getSKUs();
		setRecords(data);
		setLoading(false);
	};

	useEffect(() => {
		loadSkus();
	}, []);

	const openCreateModal = () => {
		setForm(defaultForm);
		setModalMode("create");
	};

	const openEditModal = (sku: SKUProfile) => {
		setForm(mapSkuToForm(sku));
		setModalMode("edit");
	};

	const closeModal = () => {
		if (submitting) return;
		setModalMode(null);
	};

	const submitModal = async () => {
		if (!form.id.trim() || !form.name.trim()) {
			showToast("error", "SKU ID and name are required.");
			return;
		}

		setSubmitting(true);
		try {
			if (modalMode === "create") {
				await createSKU({
					...form,
					id: form.id.trim(),
					name: form.name.trim(),
					category: form.category.trim(),
				});
				showToast("success", "SKU created successfully.");
			} else if (modalMode === "edit") {
				await updateSKU(form.id, {
					name: form.name.trim(),
					category: form.category.trim(),
					demandScale: form.demandScale,
					priceSensitivity: form.priceSensitivity,
					festivalSensitivity: form.festivalSensitivity,
				});
				showToast("success", "SKU updated successfully.");
			}

			setModalMode(null);
			await loadSkus();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Operation failed.",
			);
		} finally {
			setSubmitting(false);
		}
	};

	const onDeleteSku = async (skuId: string) => {
		if (!window.confirm("Delete this SKU and all related data?")) return;
		try {
			await deleteSKU(skuId);
			showToast("success", "SKU deleted.");
			await loadSkus();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Delete failed.",
			);
		}
	};

	const filtered = records.filter((record) => {
		const sku = record.sku;
		const matchSearch =
			!search ||
			sku.name.toLowerCase().includes(search.toLowerCase()) ||
			sku.id.toLowerCase().includes(search.toLowerCase()) ||
			sku.category.toLowerCase().includes(search.toLowerCase());
		const matchDemand = !filterDemand || sku.demandScale === filterDemand;
		const matchSensitivity =
			!filterPriceSensitivity ||
			sku.priceSensitivity === filterPriceSensitivity;

		return matchSearch && matchDemand && matchSensitivity;
	});

	return (
		<div className="space-y-4">
			{toast && (
				<div
					className={`rounded-lg border px-4 py-2 text-sm ${toast.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"}`}
				>
					{toast.message}
				</div>
			)}

			<div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
				<div className="flex flex-wrap gap-3 items-center">
					<button
						onClick={openCreateModal}
						className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-3 py-2 rounded-lg"
					>
						+ New SKU
					</button>
					<div className="relative flex-1 min-w-[200px]">
						<Search
							size={15}
							className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
						/>
						<input
							type="text"
							placeholder="Search SKU, category..."
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
						value={filterDemand}
						onChange={(e) => setFilterDemand(e.target.value)}
						className="border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white"
					>
						<option value="">All Demand Scales</option>
						<option value="Low">Low</option>
						<option value="Medium">Medium</option>
						<option value="High">High</option>
					</select>
					<select
						value={filterPriceSensitivity}
						onChange={(e) =>
							setFilterPriceSensitivity(e.target.value)
						}
						className="border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white"
					>
						<option value="">All Price Sensitivities</option>
						<option value="Low">Low</option>
						<option value="Medium">Medium</option>
						<option value="High">High</option>
					</select>
				</div>
				<p className="text-xs text-slate-400 mt-2">
					{filtered.length} of {records.length} SKUs
				</p>
			</div>

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
										Demand Scale
									</th>
									<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Price Sensitivity
									</th>
									<th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
										Festival Sensitivity
									</th>
									<th className="px-3 py-3"></th>
								</tr>
							</thead>
							<tbody>
								{filtered.map((record) => {
									const sku = record.sku;
									return (
										<tr
											key={sku.id}
											className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
										>
											<td className="px-5 py-3.5">
												<Link
													href={`/skus/${sku.id}`}
													className="block"
												>
													<p className="font-medium text-slate-800 hover:text-blue-600">
														{sku.name}
													</p>
													<p className="text-xs text-slate-400 mt-0.5">
														{sku.category} ·{" "}
														{sku.id}
													</p>
												</Link>
											</td>
											<td className="px-3 py-3.5 text-slate-700 font-medium">
												{sku.demandScale}
											</td>
											<td className="px-3 py-3.5 text-slate-700">
												{sku.priceSensitivity}
											</td>
											<td className="px-3 py-3.5 text-slate-700">
												{sku.festivalSensitivity}
											</td>
											<td className="px-3 py-3.5">
												<div className="flex items-center gap-2 justify-end">
													<button
														onClick={() =>
															openEditModal(sku)
														}
														className="text-xs text-blue-600 hover:underline"
													>
														Edit
													</button>
													<button
														onClick={() =>
															onDeleteSku(sku.id)
														}
														className="text-xs text-red-600 hover:underline"
													>
														Delete
													</button>
													<Link
														href={`/skus/${sku.id}`}
														className="text-blue-500 hover:text-blue-700"
													>
														<ChevronRight
															size={16}
														/>
													</Link>
												</div>
											</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
				)}
			</div>

			{modalMode && (
				<div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
					<div className="w-full max-w-2xl bg-white rounded-xl border border-slate-200 shadow-xl p-5 space-y-4">
						<div className="flex items-center justify-between">
							<h3 className="text-lg font-semibold text-slate-800">
								{modalMode === "create"
									? "Create SKU"
									: "Edit SKU"}
							</h3>
							<button
								onClick={closeModal}
								className="text-sm text-slate-500 hover:text-slate-700"
							>
								Close
							</button>
						</div>

						<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
							<label className="text-sm text-slate-600">
								SKU ID
								<input
									disabled={modalMode === "edit"}
									value={form.id}
									onChange={(e) =>
										setForm((prev) => ({
											...prev,
											id: e.target.value,
										}))
									}
									className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm disabled:bg-slate-100"
								/>
							</label>
							<label className="text-sm text-slate-600">
								Name
								<input
									value={form.name}
									onChange={(e) =>
										setForm((prev) => ({
											...prev,
											name: e.target.value,
										}))
									}
									className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
								/>
							</label>
							<label className="text-sm text-slate-600">
								Category
								<input
									value={form.category}
									onChange={(e) =>
										setForm((prev) => ({
											...prev,
											category: e.target.value,
										}))
									}
									className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
								/>
							</label>
							<label className="text-sm text-slate-600">
								Demand Scale
								<select
									value={form.demandScale}
									onChange={(e) =>
										setForm((prev) => ({
											...prev,
											demandScale: e.target.value as
												| "low"
												| "medium"
												| "high",
										}))
									}
									className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
								>
									<option value="low">Low</option>
									<option value="medium">Medium</option>
									<option value="high">High</option>
								</select>
							</label>
							<label className="text-sm text-slate-600">
								Price Sensitivity
								<select
									value={form.priceSensitivity}
									onChange={(e) =>
										setForm((prev) => ({
											...prev,
											priceSensitivity: e.target.value as
												| "low"
												| "medium"
												| "high",
										}))
									}
									className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
								>
									<option value="low">Low</option>
									<option value="medium">Medium</option>
									<option value="high">High</option>
								</select>
							</label>
							<label className="text-sm text-slate-600">
								Festival Sensitivity
								<select
									value={form.festivalSensitivity}
									onChange={(e) =>
										setForm((prev) => ({
											...prev,
											festivalSensitivity: e.target
												.value as
												| "low"
												| "medium"
												| "high",
										}))
									}
									className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
								>
									<option value="low">Low</option>
									<option value="medium">Medium</option>
									<option value="high">High</option>
								</select>
							</label>
						</div>

						<div className="flex items-center justify-end gap-2 pt-2">
							<button
								onClick={closeModal}
								className="px-3 py-2 text-sm border border-slate-300 rounded-lg"
							>
								Cancel
							</button>
							<button
								disabled={submitting}
								onClick={submitModal}
								className="px-3 py-2 text-sm font-semibold rounded-lg bg-blue-600 text-white disabled:bg-blue-400"
							>
								{submitting ? "Saving..." : "Save"}
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
