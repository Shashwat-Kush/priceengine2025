"use client";

import { useEffect, useState } from "react";
import {
	createListing,
	deleteListing,
	getInventoryData,
	getListingsBySku,
	getSKUs,
	updateListing,
	updateSKU,
} from "@/lib/services";
import { MarketplaceBadge, InventoryBadge } from "@/components/Badges";
import { KpiCard } from "@/components/KpiCard";
import Link from "next/link";
import clsx from "clsx";
import { Package, IndianRupee, AlertTriangle } from "lucide-react";
import { Listing, ListingCreateInput, SKU } from "@/lib/types";

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
	storageCostPerUnit: number;
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
	const [skuOptions, setSkuOptions] = useState<SKU[]>([]);
	const [loading, setLoading] = useState(true);
	const [editingSkuId, setEditingSkuId] = useState<string | null>(null);
	const [inlineDraft, setInlineDraft] = useState({
		inventory: 0,
		dailyDemand: 0,
		leadTimeDays: 7,
		storageCostPerUnit: 5,
	});

	const [selectedSkuId, setSelectedSkuId] = useState<string>("");
	const [listings, setListings] = useState<Listing[]>([]);
	const [loadingListings, setLoadingListings] = useState(false);
	const [listingMode, setListingMode] = useState<"create" | "edit">("create");
	const [editingListingId, setEditingListingId] = useState<string | null>(
		null,
	);
	const [listingDraft, setListingDraft] = useState<ListingCreateInput>({
		skuId: "",
		marketplace: "Amazon",
		currentPrice: 100,
		cost: 50,
		inventory: 0,
		dailyDemand: 1,
		leadTimeDays: 7,
		storageCostPerUnit: 5,
	});

	const [toast, setToast] = useState<{
		type: "success" | "error";
		message: string;
	} | null>(null);

	const showToast = (type: "success" | "error", message: string) => {
		setToast({ type, message });
		window.setTimeout(() => setToast(null), 2800);
	};

	const loadInventory = async () => {
		setLoading(true);
		const inventoryRows = await getInventoryData();
		setData(inventoryRows as InventoryRow[]);
		setLoading(false);
	};

	const loadSkuOptions = async () => {
		const skus = await getSKUs();
		setSkuOptions(skus);
		setSelectedSkuId((prev) => prev || skus[0]?.id || "");
	};

	const loadListings = async (skuId: string) => {
		if (!skuId) {
			setListings([]);
			return;
		}
		setLoadingListings(true);
		const rows = await getListingsBySku(skuId);
		setListings(rows);
		setLoadingListings(false);
	};

	useEffect(() => {
		loadInventory();
		loadSkuOptions();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	useEffect(() => {
		if (!selectedSkuId) return;
		setListingDraft((prev) => ({ ...prev, skuId: selectedSkuId }));
		loadListings(selectedSkuId);
	}, [selectedSkuId]);

	const startInlineEdit = (row: InventoryRow) => {
		setEditingSkuId(row.id);
		setInlineDraft({
			inventory: row.inventory,
			dailyDemand: row.dailyDemand,
			leadTimeDays: row.leadTimeDays,
			storageCostPerUnit: row.storageCostPerUnit,
		});
	};

	const saveInlineEdit = async (skuId: string) => {
		try {
			await updateSKU(skuId, {
				inventory: inlineDraft.inventory,
				dailyDemand: inlineDraft.dailyDemand,
				leadTimeDays: inlineDraft.leadTimeDays,
				storageCostPerUnit: inlineDraft.storageCostPerUnit,
			});
			setEditingSkuId(null);
			showToast("success", "Inventory inputs updated.");
			await loadInventory();
			if (selectedSkuId) {
				await loadListings(selectedSkuId);
			}
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Update failed.",
			);
		}
	};

	const resetListingForm = () => {
		setListingMode("create");
		setEditingListingId(null);
		setListingDraft({
			skuId: selectedSkuId,
			marketplace: "Amazon",
			currentPrice: 100,
			cost: 50,
			inventory: 0,
			dailyDemand: 1,
			leadTimeDays: 7,
			storageCostPerUnit: 5,
		});
	};

	const submitListing = async () => {
		if (!selectedSkuId) return;
		try {
			if (listingMode === "create") {
				await createListing({ ...listingDraft, skuId: selectedSkuId });
				showToast("success", "Listing created.");
			} else if (editingListingId) {
				await updateListing(editingListingId, {
					skuId: selectedSkuId,
					marketplace: listingDraft.marketplace,
					currentPrice: listingDraft.currentPrice,
					cost: listingDraft.cost,
					inventory: listingDraft.inventory,
					dailyDemand: listingDraft.dailyDemand,
					leadTimeDays: listingDraft.leadTimeDays,
					storageCostPerUnit: listingDraft.storageCostPerUnit,
				});
				showToast("success", "Listing updated.");
			}
			resetListingForm();
			await loadListings(selectedSkuId);
			await loadInventory();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Listing save failed.",
			);
		}
	};

	const editListing = (listing: Listing) => {
		setListingMode("edit");
		setEditingListingId(listing.id);
		setListingDraft({
			skuId: listing.skuId,
			marketplace: listing.marketplace,
			currentPrice: listing.currentPrice,
			cost: listing.cost,
			inventory: listing.inventory,
			dailyDemand: listing.dailyDemand,
			leadTimeDays: listing.leadTimeDays,
			storageCostPerUnit: listing.storageCostPerUnit,
		});
	};

	const removeListing = async (listingId: string) => {
		if (
			!window.confirm(
				"Delete this listing? Its competitors will also be removed.",
			)
		) {
			return;
		}
		try {
			await deleteListing(listingId);
			showToast("success", "Listing deleted.");
			await loadListings(selectedSkuId);
			await loadInventory();
			if (editingListingId === listingId) resetListingForm();
		} catch (error) {
			showToast(
				"error",
				error instanceof Error ? error.message : "Delete failed.",
			);
		}
	};

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
			{toast && (
				<div
					className={`rounded-lg border px-4 py-2 text-sm ${toast.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"}`}
				>
					{toast.message}
				</div>
			)}

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
										<th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
											Actions
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
												{editingSkuId === row.id ? (
													<input
														type="number"
														value={
															inlineDraft.inventory
														}
														onChange={(e) =>
															setInlineDraft(
																(prev) => ({
																	...prev,
																	inventory:
																		Number(
																			e
																				.target
																				.value,
																		),
																}),
															)
														}
														className="w-20 border border-slate-300 rounded px-2 py-1 text-right"
													/>
												) : (
													row.inventory
												)}
											</td>
											<td className="px-3 py-3.5 text-right font-mono text-slate-600">
												{editingSkuId === row.id ? (
													<input
														type="number"
														step="0.1"
														value={
															inlineDraft.dailyDemand
														}
														onChange={(e) =>
															setInlineDraft(
																(prev) => ({
																	...prev,
																	dailyDemand:
																		Number(
																			e
																				.target
																				.value,
																		),
																}),
															)
														}
														className="w-20 border border-slate-300 rounded px-2 py-1 text-right"
													/>
												) : (
													row.dailyDemand
												)}
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
												{editingSkuId === row.id ? (
													<input
														type="number"
														value={
															inlineDraft.leadTimeDays
														}
														onChange={(e) =>
															setInlineDraft(
																(prev) => ({
																	...prev,
																	leadTimeDays:
																		Number(
																			e
																				.target
																				.value,
																		),
																}),
															)
														}
														className="w-20 border border-slate-300 rounded px-2 py-1 text-right"
													/>
												) : (
													`${row.leadTimeDays}d`
												)}
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
												{editingSkuId === row.id ? (
													<input
														type="number"
														step="0.1"
														value={
															inlineDraft.storageCostPerUnit
														}
														onChange={(e) =>
															setInlineDraft(
																(prev) => ({
																	...prev,
																	storageCostPerUnit:
																		Number(
																			e
																				.target
																				.value,
																		),
																}),
															)
														}
														className="w-20 border border-slate-300 rounded px-2 py-1 text-right"
													/>
												) : row.storageCostImpact >
												  0 ? (
													`+₹${row.storageCostImpact}/mo`
												) : (
													"—"
												)}
											</td>
											<td className="px-3 py-3.5">
												<InventoryBadge
													value={row.inventoryStatus}
												/>
											</td>
											<td className="px-3 py-3.5 text-right">
												{editingSkuId === row.id ? (
													<div className="flex items-center gap-2 justify-end">
														<button
															onClick={() =>
																setEditingSkuId(
																	null,
																)
															}
															className="text-xs text-slate-600 hover:underline"
														>
															Cancel
														</button>
														<button
															onClick={() =>
																saveInlineEdit(
																	row.id,
																)
															}
															className="text-xs text-blue-600 hover:underline"
														>
															Save
														</button>
													</div>
												) : (
													<button
														onClick={() =>
															startInlineEdit(row)
														}
														className="text-xs text-blue-600 hover:underline"
													>
														Inline Edit
													</button>
												)}
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>

					<div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
						<div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-3">
							<div>
								<h2 className="font-semibold text-slate-800">
									Listing Manager
								</h2>
								<p className="text-xs text-slate-500 mt-0.5">
									Create, update, or remove marketplace
									listings for each SKU.
								</p>
							</div>
							<select
								value={selectedSkuId}
								onChange={(e) => {
									setSelectedSkuId(e.target.value);
									resetListingForm();
								}}
								className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white"
							>
								{skuOptions.map((sku) => (
									<option key={sku.id} value={sku.id}>
										{sku.name}
									</option>
								))}
							</select>
						</div>

						<div className="px-5 py-4 border-b border-slate-100 bg-slate-50">
							<div className="grid grid-cols-1 md:grid-cols-4 gap-3">
								<label className="text-xs text-slate-600">
									Marketplace
									<select
										value={listingDraft.marketplace}
										onChange={(e) =>
											setListingDraft((prev) => ({
												...prev,
												marketplace: e.target.value,
											}))
										}
										className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
									>
										<option value="Amazon">Amazon</option>
										<option value="Flipkart">
											Flipkart
										</option>
										<option value="Meesho">Meesho</option>
									</select>
								</label>
								{[
									["Price", "currentPrice"],
									["Cost", "cost"],
									["Inventory", "inventory"],
									["Daily Demand", "dailyDemand"],
									["Lead Time", "leadTimeDays"],
									["Storage Cost", "storageCostPerUnit"],
								].map(([label, key]) => (
									<label
										key={key}
										className="text-xs text-slate-600"
									>
										{label}
										<input
											type="number"
											step={
												key === "dailyDemand" ||
												key === "storageCostPerUnit"
													? "0.1"
													: "1"
											}
											value={
												listingDraft[
													key as keyof ListingCreateInput
												] as number
											}
											onChange={(e) =>
												setListingDraft((prev) => ({
													...prev,
													[key]: Number(
														e.target.value,
													),
												}))
											}
											className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
										/>
									</label>
								))}
							</div>
							<div className="mt-3 flex items-center gap-2">
								<button
									onClick={submitListing}
									className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-2 rounded-lg"
								>
									{listingMode === "create"
										? "Add Listing"
										: "Save Listing"}
								</button>
								{listingMode === "edit" && (
									<button
										onClick={resetListingForm}
										className="text-xs text-slate-600 hover:underline"
									>
										Cancel edit
									</button>
								)}
							</div>
						</div>

						{loadingListings ? (
							<div className="px-5 py-6 text-sm text-slate-500">
								Loading listings...
							</div>
						) : listings.length === 0 ? (
							<div className="px-5 py-6 text-sm text-slate-500">
								No listings found for this SKU.
							</div>
						) : (
							<div className="overflow-x-auto">
								<table className="w-full text-sm">
									<thead>
										<tr className="border-b border-slate-100 bg-slate-50">
											<th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">
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
											<th className="px-3 py-3"></th>
										</tr>
									</thead>
									<tbody>
										{listings.map((listing) => (
											<tr
												key={listing.id}
												className="border-b border-slate-100 last:border-0"
											>
												<td className="px-5 py-3.5 text-slate-700 font-medium">
													{listing.marketplace}
												</td>
												<td className="px-3 py-3.5 text-right font-mono">
													₹{listing.currentPrice}
												</td>
												<td className="px-3 py-3.5 text-right font-mono text-slate-500">
													₹{listing.cost}
												</td>
												<td className="px-3 py-3.5 text-right font-mono">
													{listing.inventory}
												</td>
												<td className="px-3 py-3.5 text-right font-mono text-slate-500">
													{listing.dailyDemand}
												</td>
												<td className="px-3 py-3.5 text-right">
													<div className="flex items-center justify-end gap-2">
														<button
															onClick={() =>
																editListing(
																	listing,
																)
															}
															className="text-xs text-blue-600 hover:underline"
														>
															Edit
														</button>
														<button
															onClick={() =>
																removeListing(
																	listing.id,
																)
															}
															className="text-xs text-red-600 hover:underline"
														>
															Delete
														</button>
													</div>
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						)}
					</div>
				</>
			)}
		</div>
	);
}
