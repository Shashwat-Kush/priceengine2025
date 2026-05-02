export type Marketplace = "Amazon" | "Flipkart" | "Meesho" | string;
export type Sensitivity = "High" | "Medium" | "Low";
export type InventoryStatus = "Healthy" | "Low" | "Critical" | "Overstock";
export type CompetitorRisk = "High" | "Medium" | "Low";

export type SKUProfile = {
	id: string;
	name: string;
	category: string;
	description?: string;
	features?: Record<string, string>;
	imageUrl?: string;
	demandScale: Sensitivity;
	priceSensitivity: Sensitivity;
	festivalSensitivity: Sensitivity;
};

export type Listing = {
	id: string;
	skuId: string;
	marketplace: Marketplace;
	price: number;
	cost: number;
	inventory: number;
	leadTimeDays: number;
	storageCostPerUnit: number;
};

export type CompetitorRecord = {
	id: string;
	listingId: string;
	skuId?: string;
	marketplace?: string;
	name: string;
	price: number;
	rating: number;
	shippingDays: number;
};

export type ComputedMetrics = {
	demand: number;
	profit: number;
	revenue: number;
	avgCompPrice: number;
	minCompPrice: number;
	daysToStockout: number;
	reorderQty: number;
};

export type EngineListingView = {
	listing: Listing;
	competitors: CompetitorRecord[];
	computed: ComputedMetrics;
};

export type EngineRecord = {
	sku: SKUProfile;
	listing: Listing | null;
	competitors: CompetitorRecord[];
	computed: ComputedMetrics;
	listings?: EngineListingView[];
};

export type DashboardKPIs = {
	totalRevenue: number;
	totalProfit: number;
	missedProfit: number;
	inventoryAlerts: number;
	undercutAlerts: number;
};

export type RecommendedAction = {
	skuId: string;
	listingId?: string;
	skuName: string;
	marketplace: Marketplace;
	currentPrice: number;
	recommendedMin: number;
	recommendedMax: number;
	estimatedProfitChange: number;
	reason: string;
};

export type Alert = {
	id: string;
	type: "low_stock" | "overpriced" | "festival_opportunity" | "undercut";
	severity: "high" | "medium" | "low";
	skuId: string;
	skuName: string;
	message: string;
};

export type FestivalEvent = {
	id: string;
	name: string;
	date: string;
	daysUntil: number;
	platform: Marketplace[];
	skuOpportunities: FestivalSKUOpportunity[];
};

export type FestivalSKUOpportunity = {
	skuId: string;
	listingId?: string;
	marketplace?: Marketplace;
	skuName: string;
	suggestedPrice: number;
	currentPrice: number;
	expectedUnits: number;
	inventoryRequired: number;
	profitImpact: number;
};

export type CompetitorHistory = {
	date: string;
	ourPrice: number;
	competitorPrice: number;
};

export type SimulatorOutput = {
	expectedUnits: number;
	demand: number;
	revenue: number;
	profit: number;
	stockoutDate: string;
};

export type PortfolioDataPoint = {
	skuId: string;
	name: string;
	margin: number;
	priceSensitivity: number;
	profit: number;
	marketplace: Marketplace;
};

export type SKUCreateInput = {
	id: string;
	name: string;
	category: string;
	description?: string;
	features?: Record<string, string>;
	imageUrl?: string;
	demandScale: "low" | "medium" | "high";
	priceSensitivity: "low" | "medium" | "high";
	festivalSensitivity: "low" | "medium" | "high";
};

export type SKUUpdateInput = Partial<{
	name: string;
	category: string;
	description: string;
	features: Record<string, string>;
	imageUrl: string;
	demandScale: "low" | "medium" | "high";
	priceSensitivity: "low" | "medium" | "high";
	festivalSensitivity: "low" | "medium" | "high";
}>;

export type ListingCreateInput = Omit<Listing, "id"> & { id?: string };

export type ListingUpdateInput = Partial<Omit<Listing, "id">>;

export type CompetitorCreateInput = {
	id?: string;
	listingId: string;
	name: string;
	price: number;
	rating: number;
	shippingDays: number;
};

export type CompetitorUpdateInput = Partial<{
	listingId: string;
	name: string;
	price: number;
	rating: number;
	shippingDays: number;
}>;

export type FestivalCatalogItem = {
	id: string;
	name: string;
	date: string;
	boost: number;
	platform: string[];
};

export type FestivalCreateInput = {
	id?: string;
	name: string;
	date: string;
	boost: number;
	platform: string[];
};

export type FestivalUpdateInput = Partial<{
	name: string;
	date: string;
	boost: number;
	platform: string[];
}>;

export type PricingAnalysisResponse = EngineRecord & {
	optimization: {
		currentPrice: number;
		currentProfit: number;
		optimalPrice: number;
		optimalProfit: number;
		recommendedMin: number;
		recommendedMax: number;
		profitCurve: { price: number; profit: number }[];
		estimatedDemand: number;
		minCompPrice: number;
		avgCompPrice: number;
		estimatedProfitChange: number;
	};
};
