"use client";

import { useEffect, useState } from "react";
import {
  createListing,
  deleteListing,
  getInventoryData,
  getListingsBySku,
  getSKUs,
  updateListing,
} from "@/lib/services";
import { Listing, ListingCreateInput, EngineRecord } from "@/lib/types";
import { KpiCard } from "@/components/KpiCard";
import Link from "next/link";
import { Package, IndianRupee, AlertTriangle } from "lucide-react";

function formatINR(n: number) {
  if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(2)}L`;
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${n}`;
}

function inventoryStatus(daysToStockout: number) {
  if (daysToStockout <= 2) return "Critical";
  if (daysToStockout <= 7) return "Low";
  if (daysToStockout >= 45) return "Overstock";
  return "Healthy";
}

type InventoryRow = EngineRecord & {
  inventory: number;
  reorderPoint: number;
  suggestedOrderQty: number;
  storageCostImpact: number;
  orderCost: number;
};

export default function InventoryPage() {
  const [rows, setRows] = useState<InventoryRow[]>([]);
  const [loading, setLoading] = useState(true);

  const [skuOptions, setSkuOptions] = useState<{ id: string; name: string }[]>([]);
  const [selectedSkuId, setSelectedSkuId] = useState("");
  const [listings, setListings] = useState<Listing[]>([]);
  const [loadingListings, setLoadingListings] = useState(false);

  const [listingMode, setListingMode] = useState<"create" | "edit">("create");
  const [editingListingId, setEditingListingId] = useState<string | null>(null);
  const [listingDraft, setListingDraft] = useState<ListingCreateInput>({
    skuId: "",
    marketplace: "Amazon",
    price: 100,
    cost: 50,
    inventory: 0,
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
    const data = await getInventoryData();
    setRows(data as InventoryRow[]);
    setLoading(false);
  };

  const loadSkuOptions = async () => {
    const skus = await getSKUs();
    const options = skus.map((row) => ({ id: row.sku.id, name: row.sku.name }));
    setSkuOptions(options);
    setSelectedSkuId((prev) => prev || options[0]?.id || "");
  };

  const loadListings = async (skuId: string) => {
    if (!skuId) {
      setListings([]);
      return;
    }
    setLoadingListings(true);
    const data = await getListingsBySku(skuId);
    setListings(data);
    setLoadingListings(false);
  };

  useEffect(() => {
    loadInventory();
    loadSkuOptions();
  }, []);

  useEffect(() => {
    if (!selectedSkuId) return;
    setListingDraft((prev) => ({ ...prev, skuId: selectedSkuId }));
    loadListings(selectedSkuId);
  }, [selectedSkuId]);

  const resetListingForm = () => {
    setListingMode("create");
    setEditingListingId(null);
    setListingDraft({
      skuId: selectedSkuId,
      marketplace: "Amazon",
      price: 100,
      cost: 50,
      inventory: 0,
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
          price: listingDraft.price,
          cost: listingDraft.cost,
          inventory: listingDraft.inventory,
          leadTimeDays: listingDraft.leadTimeDays,
          storageCostPerUnit: listingDraft.storageCostPerUnit,
        });
        showToast("success", "Listing updated.");
      }
      resetListingForm();
      await loadListings(selectedSkuId);
      await loadInventory();
    } catch (error) {
      showToast("error", error instanceof Error ? error.message : "Listing save failed.");
    }
  };

  const editListing = (listing: Listing) => {
    setListingMode("edit");
    setEditingListingId(listing.id);
    setListingDraft({
      skuId: listing.skuId,
      marketplace: listing.marketplace,
      price: listing.price,
      cost: listing.cost,
      inventory: listing.inventory,
      leadTimeDays: listing.leadTimeDays,
      storageCostPerUnit: listing.storageCostPerUnit,
    });
  };

  const removeListing = async (listingId: string) => {
    if (!window.confirm("Delete this listing? Its competitors will also be removed.")) return;
    try {
      await deleteListing(listingId);
      showToast("success", "Listing deleted.");
      await loadListings(selectedSkuId);
      await loadInventory();
      if (editingListingId === listingId) resetListingForm();
    } catch (error) {
      showToast("error", error instanceof Error ? error.message : "Delete failed.");
    }
  };

  const totalInventoryValue = rows.reduce(
    (sum, row) => sum + ((row.listing?.inventory ?? 0) * (row.listing?.cost ?? 0)),
    0,
  );
  const totalOrderCost = rows.reduce((sum, row) => sum + row.orderCost, 0);
  const criticalCount = new Set(
    rows
      .filter((row) => row.computed.daysToStockout <= 2)
      .map((row) => row.sku.id),
  ).size;
  const overstockCount = new Set(
    rows
      .filter((row) => row.computed.daysToStockout >= 45)
      .map((row) => row.sku.id),
  ).size;

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
              sub="Demand x lead time + safety buffer"
              color="orange"
              icon={<IndianRupee size={16} />}
            />
            <KpiCard
              title="Critical SKUs"
              value={criticalCount}
              sub="Stockout risk <= 2 days"
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

          <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100">
              <h2 className="font-semibold text-slate-800">Inventory & Computed Demand</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Demand is system-computed. Reorder quantity = demand x lead time + safety buffer.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">SKU</th>
                    <th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Marketplace</th>
                    <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Inventory</th>
                    <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Computed Demand</th>
                    <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Days to Stockout</th>
                    <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Lead Time</th>
                    <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Reorder Qty</th>
                    <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Order Cost</th>
                    <th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const listing = row.listing;
                    if (!listing) return null;
                    const status = inventoryStatus(row.computed.daysToStockout);
                    return (
                      <tr key={`${row.sku.id}:${listing.id}`} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                        <td className="px-5 py-3.5">
                          <Link href={`/skus/${row.sku.id}`} className="font-medium text-slate-800 hover:text-blue-600">
                            {row.sku.name}
                          </Link>
                        </td>
                        <td className="px-3 py-3.5 text-slate-600">{listing.marketplace}</td>
                        <td className="px-3 py-3.5 text-right font-mono">{listing.inventory}</td>
                        <td className="px-3 py-3.5 text-right font-mono text-blue-700">{row.computed.demand.toFixed(2)}</td>
                        <td className="px-3 py-3.5 text-right font-mono">{row.computed.daysToStockout >= 999 ? "∞" : row.computed.daysToStockout}</td>
                        <td className="px-3 py-3.5 text-right font-mono text-slate-500">{listing.leadTimeDays}d</td>
                        <td className="px-3 py-3.5 text-right font-mono font-semibold text-indigo-700">{row.suggestedOrderQty}</td>
                        <td className="px-3 py-3.5 text-right font-mono text-slate-600">{row.orderCost > 0 ? formatINR(row.orderCost) : "-"}</td>
                        <td className="px-3 py-3.5 text-xs font-medium">{status}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-slate-800">Listing Manager</h2>
                <p className="text-xs text-slate-500 mt-0.5">Edit business decisions only: price, cost, inventory, lead time.</p>
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label className="text-xs text-slate-600">
                  Marketplace
                  <select
                    value={listingDraft.marketplace}
                    onChange={(e) => setListingDraft((prev) => ({ ...prev, marketplace: e.target.value }))}
                    className="mt-1 w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
                  >
                    <option value="Amazon">Amazon</option>
                    <option value="Flipkart">Flipkart</option>
                    <option value="Meesho">Meesho</option>
                  </select>
                </label>
                {[
                  ["Price", "price"],
                  ["Cost", "cost"],
                  ["Inventory", "inventory"],
                  ["Lead Time", "leadTimeDays"],
                  ["Storage Cost", "storageCostPerUnit"],
                ].map(([label, key]) => (
                  <label key={key} className="text-xs text-slate-600">
                    {label}
                    <input
                      type="number"
                      step={key === "storageCostPerUnit" ? "0.1" : "1"}
                      value={listingDraft[key as keyof ListingCreateInput] as number}
                      onChange={(e) =>
                        setListingDraft((prev) => ({
                          ...prev,
                          [key]: Number(e.target.value),
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
                  {listingMode === "create" ? "Add Listing" : "Save Listing"}
                </button>
                {listingMode === "edit" && (
                  <button onClick={resetListingForm} className="text-xs text-slate-600 hover:underline">
                    Cancel edit
                  </button>
                )}
              </div>
            </div>

            {loadingListings ? (
              <div className="px-5 py-6 text-sm text-slate-500">Loading listings...</div>
            ) : listings.length === 0 ? (
              <div className="px-5 py-6 text-sm text-slate-500">No listings found for this SKU.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50">
                      <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Marketplace</th>
                      <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Price</th>
                      <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Cost</th>
                      <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Inventory</th>
                      <th className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase">Lead Time</th>
                      <th className="px-3 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {listings.map((listing) => (
                      <tr key={listing.id} className="border-b border-slate-100 last:border-0">
                        <td className="px-5 py-3.5 text-slate-700 font-medium">{listing.marketplace}</td>
                        <td className="px-3 py-3.5 text-right font-mono">₹{listing.price}</td>
                        <td className="px-3 py-3.5 text-right font-mono text-slate-500">₹{listing.cost}</td>
                        <td className="px-3 py-3.5 text-right font-mono">{listing.inventory}</td>
                        <td className="px-3 py-3.5 text-right font-mono text-slate-500">{listing.leadTimeDays}d</td>
                        <td className="px-3 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button onClick={() => editListing(listing)} className="text-xs text-blue-600 hover:underline">
                              Edit
                            </button>
                            <button onClick={() => removeListing(listing.id)} className="text-xs text-red-600 hover:underline">
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
