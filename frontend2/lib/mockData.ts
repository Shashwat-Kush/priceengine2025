import {
	DashboardKPIs,
	RecommendedAction,
	Alert,
	FestivalEvent,
	CompetitorHistory,
	PortfolioDataPoint,
} from "./types";

export const SKUS = [
	{
		id: "sku-001",
		name: "Redmi Note 12",
		category: "Mobile",
		marketplace: "Amazon",
		currentPrice: 11999,
		cost: 6500,
		competitorPrice: 11799,
		inventory: 120,
		dailyDemand: 18,
		priceSensitivity: "High",
		competitorRisk: "High",
		inventoryStatus: "Healthy",
		margin: 45.8,
		leadTimeDays: 7,
		storageCostPerUnit: 20,
		baseDemand: 20,
		festivalBoostPotential: "High",
		marketplaceStrength: "High",
	},
	{
		id: "sku-002",
		name: "Samsung Galaxy M34",
		category: "Mobile",
		marketplace: "Flipkart",
		currentPrice: 15999,
		cost: 9000,
		competitorPrice: 15749,
		inventory: 60,
		dailyDemand: 10,
		priceSensitivity: "Medium",
		competitorRisk: "Medium",
		inventoryStatus: "Low",
		margin: 43.8,
		leadTimeDays: 10,
		storageCostPerUnit: 25,
		baseDemand: 12,
		festivalBoostPotential: "Medium",
		marketplaceStrength: "High",
	},
	{
		id: "sku-003",
		name: "iQOO Z8",
		category: "Mobile",
		marketplace: "Amazon",
		currentPrice: 13999,
		cost: 7800,
		competitorPrice: 13599,
		inventory: 80,
		dailyDemand: 14,
		priceSensitivity: "High",
		competitorRisk: "High",
		inventoryStatus: "Healthy",
		margin: 44.3,
		leadTimeDays: 8,
		storageCostPerUnit: 18,
		baseDemand: 15,
		festivalBoostPotential: "High",
		marketplaceStrength: "Medium",
	},
	{
		id: "sku-004",
		name: "OnePlus Nord CE 3",
		category: "Mobile",
		marketplace: "Amazon",
		currentPrice: 24999,
		cost: 14500,
		competitorPrice: 24499,
		inventory: 30,
		dailyDemand: 6,
		priceSensitivity: "Medium",
		competitorRisk: "Medium",
		inventoryStatus: "Low",
		margin: 41.9,
		leadTimeDays: 12,
		storageCostPerUnit: 28,
		baseDemand: 7,
		festivalBoostPotential: "Medium",
		marketplaceStrength: "High",
	},
	{
		id: "sku-005",
		name: "Realme Narzo 70 Pro",
		category: "Mobile",
		marketplace: "Flipkart",
		currentPrice: 17999,
		cost: 10000,
		competitorPrice: 17499,
		inventory: 45,
		dailyDemand: 9,
		priceSensitivity: "High",
		competitorRisk: "High",
		inventoryStatus: "Healthy",
		margin: 44.4,
		leadTimeDays: 9,
		storageCostPerUnit: 22,
		baseDemand: 11,
		festivalBoostPotential: "High",
		marketplaceStrength: "Medium",
	},
];

export const DASHBOARD_KPIS: DashboardKPIs = {
	totalRevenue: 1842600,
	totalProfit: 728400,
	missedProfit: 94250,
	inventoryAlerts: 4,
	undercutAlerts: 7,
};

export const RECOMMENDED_ACTIONS: RecommendedAction[] = [
	{
		skuId: "sku-001",
		skuName: "boAt Airdopes 141",
		marketplace: "Amazon",
		currentPrice: 1299,
		recommendedMin: 1219,
		recommendedMax: 1249,
		estimatedProfitChange: 12400,
		reason: "Competitor undercut detected. Reducing price boosts conversions.",
	},
	{
		skuId: "sku-005",
		skuName: "Lakme Compact Powder",
		marketplace: "Flipkart",
		currentPrice: 189,
		recommendedMin: 175,
		recommendedMax: 185,
		estimatedProfitChange: 8200,
		reason: "Critical stock + high demand. Act fast before stockout.",
	},
	{
		skuId: "sku-003",
		skuName: "Mamaearth Vitamin C Serum",
		marketplace: "Meesho",
		currentPrice: 349,
		recommendedMin: 299,
		recommendedMax: 319,
		estimatedProfitChange: 18700,
		reason: "Overstock detected. Price reduction increases velocity.",
	},
	{
		skuId: "sku-013",
		skuName: "Noise ColorFit Pro 4",
		marketplace: "Amazon",
		currentPrice: 2999,
		recommendedMin: 2849,
		recommendedMax: 2899,
		estimatedProfitChange: 6800,
		reason: "Pre-festival window. Match competitor to capture demand surge.",
	},
	{
		skuId: "sku-011",
		skuName: "Fastrack Analog Watch",
		marketplace: "Amazon",
		currentPrice: 1499,
		recommendedMin: 1449,
		recommendedMax: 1479,
		estimatedProfitChange: 5400,
		reason: "Competitor undercutting. Small price drop captures the buy box.",
	},
];

export const ALERTS: Alert[] = [
	{
		id: "alert-001",
		type: "low_stock",
		severity: "high",
		skuId: "sku-005",
		skuName: "Lakme Compact Powder",
		message: "Only 8 units left. At current demand, stockout in ~14 hours.",
	},
	{
		id: "alert-002",
		type: "undercut",
		severity: "high",
		skuId: "sku-001",
		skuName: "boAt Airdopes 141",
		message: "Competitor is ₹100 cheaper. You may be losing the Buy Box.",
	},
	{
		id: "alert-003",
		type: "festival_opportunity",
		severity: "medium",
		skuId: "sku-007",
		skuName: "Haldi Kumkum Gift Set",
		message:
			"Navratri is 12 days away. Overstock can be cleared profitably.",
	},
	{
		id: "alert-004",
		type: "low_stock",
		severity: "high",
		skuId: "sku-009",
		skuName: "Dove Body Wash 500ml",
		message: "15 units remain. Reorder now to avoid festival stockout.",
	},
	{
		id: "alert-005",
		type: "overpriced",
		severity: "medium",
		skuId: "sku-003",
		skuName: "Mamaearth Vitamin C Serum",
		message: "Your price is ₹50 above market. Overstock is accumulating.",
	},
	{
		id: "alert-006",
		type: "festival_opportunity",
		severity: "low",
		skuId: "sku-014",
		skuName: "Ethnic Kurti Printed",
		message:
			"Navratri demand surge expected. Increase inventory visibility.",
	},
];

export const FESTIVAL_EVENTS: FestivalEvent[] = [
	{
		id: "festival-001",
		name: "Navratri",
		date: "2026-03-22",
		daysUntil: 32,
		platform: ["Amazon", "Flipkart", "Meesho"],
		skuOpportunities: [
			{
				skuId: "sku-007",
				skuName: "Haldi Kumkum Gift Set",
				suggestedPrice: 279,
				currentPrice: 249,
				expectedUnits: 340,
				inventoryRequired: 340,
				profitImpact: 46580,
			},
			{
				skuId: "sku-014",
				skuName: "Ethnic Kurti Printed",
				suggestedPrice: 549,
				currentPrice: 499,
				expectedUnits: 280,
				inventoryRequired: 280,
				profitImpact: 38640,
			},
			{
				skuId: "sku-003",
				skuName: "Mamaearth Vitamin C Serum",
				suggestedPrice: 329,
				currentPrice: 349,
				expectedUnits: 320,
				inventoryRequired: 210,
				profitImpact: 51040,
			},
		],
	},
	{
		id: "festival-002",
		name: "Big Billion Days",
		date: "2026-04-14",
		daysUntil: 55,
		platform: ["Flipkart"],
		skuOpportunities: [
			{
				skuId: "sku-002",
				skuName: "Prestige Iron 1000W",
				suggestedPrice: 799,
				currentPrice: 849,
				expectedUnits: 90,
				inventoryRequired: 90,
				profitImpact: 27810,
			},
			{
				skuId: "sku-009",
				skuName: "Dove Body Wash 500ml",
				suggestedPrice: 249,
				currentPrice: 279,
				expectedUnits: 200,
				inventoryRequired: 200,
				profitImpact: 26800,
			},
			{
				skuId: "sku-012",
				skuName: "Saffola Honey 500g",
				suggestedPrice: 209,
				currentPrice: 219,
				expectedUnits: 180,
				inventoryRequired: 180,
				profitImpact: 17820,
			},
		],
	},
	{
		id: "festival-003",
		name: "Independence Day Sale",
		date: "2026-08-15",
		daysUntil: 178,
		platform: ["Amazon", "Flipkart"],
		skuOpportunities: [
			{
				skuId: "sku-001",
				skuName: "boAt Airdopes 141",
				suggestedPrice: 1199,
				currentPrice: 1299,
				expectedUnits: 250,
				inventoryRequired: 250,
				profitImpact: 119750,
			},
			{
				skuId: "sku-013",
				skuName: "Noise ColorFit Pro 4",
				suggestedPrice: 2799,
				currentPrice: 2999,
				expectedUnits: 120,
				inventoryRequired: 120,
				profitImpact: 137880,
			},
		],
	},
	{
		id: "festival-004",
		name: "Diwali Sale",
		date: "2026-10-20",
		daysUntil: 244,
		platform: ["Amazon", "Flipkart", "Meesho"],
		skuOpportunities: [
			{
				skuId: "sku-004",
				skuName: "Bajaj Mixer 500W",
				suggestedPrice: 2099,
				currentPrice: 2199,
				expectedUnits: 180,
				inventoryRequired: 180,
				profitImpact: 129420,
			},
			{
				skuId: "sku-008",
				skuName: "Philips Hair Dryer 1400W",
				suggestedPrice: 1549,
				currentPrice: 1599,
				expectedUnits: 95,
				inventoryRequired: 95,
				profitImpact: 56905,
			},
			{
				skuId: "sku-011",
				skuName: "Fastrack Analog Watch",
				suggestedPrice: 1449,
				currentPrice: 1499,
				expectedUnits: 160,
				inventoryRequired: 160,
				profitImpact: 102320,
			},
		],
	},
];

export function getCompetitorHistory(skuId: string): CompetitorHistory[] {
	const base = SKUS.find((s) => s.id === skuId);
	if (!base) return [];
	const result: CompetitorHistory[] = [];
	let ourPrice = base.currentPrice + 120;
	let compPrice = base.competitorPrice + 80;
	for (let i = 29; i >= 0; i--) {
		const date = new Date();
		date.setDate(date.getDate() - i);
		ourPrice = Math.round(ourPrice + (Math.random() - 0.5) * 40);
		compPrice = Math.round(compPrice + (Math.random() - 0.5) * 50);
		result.push({
			date: date.toLocaleDateString("en-IN", {
				day: "2-digit",
				month: "short",
			}),
			ourPrice: Math.max(base.cost + 50, ourPrice),
			competitorPrice: Math.max(base.cost + 30, compPrice),
		});
	}
	return result;
}

export function getProfitCurveData(sku: (typeof SKUS)[number]) {
	const prices = [];
	const minPrice = Math.round(sku.cost * 1.05);
	const maxPrice = Math.round(sku.currentPrice * 1.5);
	for (
		let p = minPrice;
		p <= maxPrice;
		p += Math.round((maxPrice - minPrice) / 40)
	) {
		const sensitivityFactor =
			sku.priceSensitivity === "High"
				? 0.08
				: sku.priceSensitivity === "Medium"
					? 0.04
					: 0.015;
		const demand = Math.max(
			0,
			sku.baseDemand - (p - sku.competitorPrice) * sensitivityFactor,
		);
		const profit = (p - sku.cost) * demand;
		prices.push({ price: p, profit: Math.round(profit * 10) / 10 });
	}
	return prices;
}

export function getPortfolioData(): PortfolioDataPoint[] {
	return SKUS.map((sku) => ({
		skuId: sku.id,
		name: sku.name.split(" ").slice(0, 2).join(" "),
		margin: sku.margin,
		priceSensitivity:
			sku.priceSensitivity === "High"
				? 3
				: sku.priceSensitivity === "Medium"
					? 2
					: 1,
		profit: Math.round(
			(sku.currentPrice - sku.cost) * sku.dailyDemand * 30,
		),
		marketplace: sku.marketplace,
	}));
}
