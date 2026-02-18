import {
	SKUS,
	DASHBOARD_KPIS,
	RECOMMENDED_ACTIONS,
	ALERTS,
	FESTIVAL_EVENTS,
	getCompetitorHistory,
	getProfitCurveData,
	getPortfolioData,
} from "./mockData";
import { SKU, SimulatorOutput } from "./types";

const delay = (ms = 600) => new Promise((res) => setTimeout(res, ms));

export async function getDashboardData() {
	await delay();
	return {
		kpis: DASHBOARD_KPIS,
		recommendedActions: RECOMMENDED_ACTIONS,
		alerts: ALERTS,
	};
}

export async function getSKUs() {
	await delay(500);
	return SKUS;
}

export async function getSKUById(id: string) {
	await delay(400);
	return SKUS.find((s) => s.id === id) ?? null;
}

export async function simulatePriceChange(
	sku: SKU,
	price: number,
	competitorPrice: number,
	festivalBoost: boolean,
): Promise<SimulatorOutput> {
	await delay(300);
	const sensitivityFactor =
		sku.priceSensitivity === "High"
			? 0.08
			: sku.priceSensitivity === "Medium"
				? 0.04
				: 0.015;
	let demand = Math.max(
		0,
		sku.baseDemand - (price - competitorPrice) * sensitivityFactor,
	);
	if (festivalBoost) {
		demand =
			demand *
			(sku.festivalBoostPotential === "High"
				? 1.6
				: sku.festivalBoostPotential === "Medium"
					? 1.3
					: 1.1);
	}
	const dailyDemand = Math.round(demand * 10) / 10;
	const revenue = Math.round(price * dailyDemand * 30);
	const profit = Math.round((price - sku.cost) * dailyDemand * 30);
	const daysUntilStockout =
		dailyDemand > 0 ? Math.floor(sku.inventory / dailyDemand) : 999;
	const stockoutDate =
		daysUntilStockout >= 999
			? "No stockout risk"
			: new Date(
					Date.now() + daysUntilStockout * 86400000,
				).toLocaleDateString("en-IN", {
					day: "2-digit",
					month: "short",
					year: "numeric",
				});
	return {
		expectedUnits: Math.round(dailyDemand * 30),
		revenue,
		profit,
		stockoutDate,
	};
}

export async function getFestivalData() {
	await delay(500);
	return FESTIVAL_EVENTS;
}

export async function getCompetitorData(skuId: string) {
	await delay(500);
	const sku = SKUS.find((s) => s.id === skuId);
	if (!sku) return null;
	const history = getCompetitorHistory(skuId);
	const undercutCount = history.filter(
		(h) => h.competitorPrice < h.ourPrice,
	).length;
	return {
		sku,
		history,
		undercutFrequency: Math.round((undercutCount / history.length) * 100),
		risk: sku.competitorRisk,
	};
}

export async function getProfitCurve(skuId: string) {
	await delay(300);
	const sku = SKUS.find((s) => s.id === skuId);
	if (!sku) return null;
	return { data: getProfitCurveData(sku), sku };
}

export async function getPortfolioAnalytics() {
	await delay(500);
	return getPortfolioData();
}

export async function getInventoryData() {
	await delay(400);
	return SKUS.map((sku) => {
		const daysUntilStockout =
			sku.dailyDemand > 0
				? Math.floor(sku.inventory / sku.dailyDemand)
				: 999;
		const reorderPoint = sku.dailyDemand * sku.leadTimeDays * 1.2;
		const suggestedOrderQty = Math.max(
			0,
			Math.ceil(reorderPoint * 2 - sku.inventory),
		);
		return {
			...sku,
			daysUntilStockout,
			reorderPoint: Math.round(reorderPoint),
			suggestedOrderQty,
			storageCostImpact: Math.round(
				suggestedOrderQty * sku.storageCostPerUnit,
			),
			orderCost: Math.round(suggestedOrderQty * sku.cost),
		};
	});
}
