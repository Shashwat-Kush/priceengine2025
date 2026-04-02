import {
	Alert,
	CompetitorCreateInput,
	CompetitorHistory,
	CompetitorRecord,
	CompetitorUpdateInput,
	DashboardKPIs,
	FestivalCatalogItem,
	FestivalCreateInput,
	FestivalEvent,
	FestivalUpdateInput,
	Listing,
	ListingCreateInput,
	ListingUpdateInput,
	PortfolioDataPoint,
	RecommendedAction,
	SKU,
	SKUCreateInput,
	SKUUpdateInput,
	SimulatorOutput,
} from "./types";

const API_BASE_URL =
	process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const AUTH_TOKEN_KEY = "priceiq.auth.token";
const AUTH_USER_KEY = "priceiq.auth.user";

export type AuthUser = {
	id: string;
	email: string;
	orgId: string;
	organizationName?: string;
};

type AuthResponse = {
	token: string;
	user: AuthUser;
};

function isBrowser() {
	return typeof window !== "undefined";
}

function isJwtToken(token: string | null): token is string {
	return !!token && token.split(".").length === 3;
}

export function getAuthToken(): string | null {
	if (!isBrowser()) return null;
	return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

function setAuthSession(token: string, user: AuthUser) {
	if (!isBrowser()) return;
	window.localStorage.setItem(AUTH_TOKEN_KEY, token);
	window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function getAuthUser(): AuthUser | null {
	if (!isBrowser()) return null;
	const raw = window.localStorage.getItem(AUTH_USER_KEY);
	if (!raw) return null;

	try {
		return JSON.parse(raw) as AuthUser;
	} catch {
		return null;
	}
}

export function clearAuthSession() {
	if (!isBrowser()) return;
	window.localStorage.removeItem(AUTH_TOKEN_KEY);
	window.localStorage.removeItem(AUTH_USER_KEY);
}

export function hasClientSession() {
	if (!isBrowser()) return false;
	return isJwtToken(window.localStorage.getItem(AUTH_TOKEN_KEY));
}

export async function loginWithPassword(email: string, password: string) {
	const normalizedEmail = email.trim().toLowerCase();
	const response = await apiRequest<AuthResponse>("/auth/login", {
		method: "POST",
		body: JSON.stringify({ email: normalizedEmail, password }),
	});
	setAuthSession(response.token, response.user);
	return response;
}

export async function registerUser(
	email: string,
	password: string,
	organizationName: string,
) {
	const response = await apiRequest<AuthResponse>("/auth/register", {
		method: "POST",
		body: JSON.stringify({
			email: email.trim().toLowerCase(),
			password,
			organization_name: organizationName,
		}),
	});
	setAuthSession(response.token, response.user);
	return response;
}

export async function logoutUser() {
	try {
		if (hasClientSession()) {
			await apiRequest<{ success: boolean }>("/auth/logout", {
				method: "POST",
			});
		}
	} catch {
		// Token may already be expired/invalid; local cleanup still applies.
	} finally {
		clearAuthSession();
	}
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
	const token = getAuthToken();
	const headers = new Headers(init?.headers ?? {});
	headers.set("Content-Type", "application/json");
	if (isJwtToken(token)) {
		headers.set("Authorization", `Bearer ${token}`);
	}

	const response = await fetch(`${API_BASE_URL}${path}`, {
		...init,
		headers,
		cache: "no-store",
	});

	if (!response.ok) {
		if (response.status === 401) {
			clearAuthSession();
		}
		const detail = await response.text();
		throw new Error(`API ${response.status}: ${detail}`);
	}

	return (await response.json()) as T;
}

export async function getDashboardData() {
	try {
		return await apiRequest<{
			kpis: DashboardKPIs;
			recommendedActions: RecommendedAction[];
			alerts: Alert[];
		}>("/dashboard");
	} catch {
		return {
			kpis: {
				totalRevenue: 0,
				totalProfit: 0,
				missedProfit: 0,
				inventoryAlerts: 0,
				undercutAlerts: 0,
			},
			recommendedActions: [],
			alerts: [],
		};
	}
}

export async function getSKUs() {
	try {
		return await apiRequest<SKU[]>("/skus");
	} catch {
		return [];
	}
}

export async function getSKUById(id: string) {
	try {
		return await apiRequest<SKU>(`/skus/${id}`);
	} catch {
		return null;
	}
}

export async function createSKU(input: SKUCreateInput) {
	return await apiRequest<SKU>("/skus", {
		method: "POST",
		body: JSON.stringify({
			id: input.id,
			name: input.name,
			category: input.category,
			base_demand: input.baseDemand,
			price_sensitivity: input.priceSensitivity,
			festival_boost_potential: input.festivalBoostPotential,
			marketplace: input.marketplace,
			current_price: input.currentPrice,
			cost: input.cost,
			competitor_price: input.competitorPrice,
			inventory: input.inventory,
			daily_demand: input.dailyDemand,
			lead_time_days: input.leadTimeDays,
			storage_cost_per_unit: input.storageCostPerUnit,
		}),
	});
}

export async function updateSKU(skuId: string, input: SKUUpdateInput) {
	return await apiRequest<SKU>(`/skus/${skuId}`, {
		method: "PUT",
		body: JSON.stringify({
			name: input.name,
			category: input.category,
			base_demand: input.baseDemand,
			price_sensitivity: input.priceSensitivity,
			festival_boost_potential: input.festivalBoostPotential,
			marketplace: input.marketplace,
			current_price: input.currentPrice,
			cost: input.cost,
			competitor_price: input.competitorPrice,
			inventory: input.inventory,
			daily_demand: input.dailyDemand,
			lead_time_days: input.leadTimeDays,
			storage_cost_per_unit: input.storageCostPerUnit,
		}),
	});
}

export async function deleteSKU(skuId: string) {
	return await apiRequest<{ deleted: boolean; id: string }>(
		`/skus/${skuId}`,
		{
			method: "DELETE",
		},
	);
}

export async function getListingsBySku(skuId: string) {
	try {
		return await apiRequest<Listing[]>(
			`/listings/by-sku/${encodeURIComponent(skuId)}`,
		);
	} catch {
		return [];
	}
}

export async function createListing(input: ListingCreateInput) {
	return await apiRequest<Listing>("/listings", {
		method: "POST",
		body: JSON.stringify({
			id: input.id,
			sku_id: input.skuId,
			marketplace: input.marketplace,
			current_price: input.currentPrice,
			cost: input.cost,
			inventory: input.inventory,
			daily_demand: input.dailyDemand,
			lead_time_days: input.leadTimeDays,
			storage_cost_per_unit: input.storageCostPerUnit,
		}),
	});
}

export async function updateListing(
	listingId: string,
	input: ListingUpdateInput,
) {
	return await apiRequest<Listing>(`/listings/${listingId}`, {
		method: "PUT",
		body: JSON.stringify({
			sku_id: input.skuId,
			marketplace: input.marketplace,
			current_price: input.currentPrice,
			cost: input.cost,
			inventory: input.inventory,
			daily_demand: input.dailyDemand,
			lead_time_days: input.leadTimeDays,
			storage_cost_per_unit: input.storageCostPerUnit,
		}),
	});
}

export async function deleteListing(listingId: string) {
	return await apiRequest<{ deleted: boolean; id: string }>(
		`/listings/${listingId}`,
		{
			method: "DELETE",
		},
	);
}

export async function getCompetitorItemsBySku(skuId: string) {
	try {
		return await apiRequest<CompetitorRecord[]>(
			`/competitor/by-sku/${encodeURIComponent(skuId)}`,
		);
	} catch {
		return [];
	}
}

export async function createCompetitor(input: CompetitorCreateInput) {
	return await apiRequest<CompetitorRecord>("/competitor", {
		method: "POST",
		body: JSON.stringify({
			id: input.id,
			listing_id: input.listingId,
			name: input.name,
			price: input.price,
			rating: input.rating,
			shipping_days: input.shippingDays,
		}),
	});
}

export async function updateCompetitor(
	competitorId: string,
	input: CompetitorUpdateInput,
) {
	return await apiRequest<CompetitorRecord>(`/competitor/${competitorId}`, {
		method: "PUT",
		body: JSON.stringify({
			listing_id: input.listingId,
			name: input.name,
			price: input.price,
			rating: input.rating,
			shipping_days: input.shippingDays,
		}),
	});
}

export async function deleteCompetitor(competitorId: string) {
	return await apiRequest<{ deleted: boolean; id: string }>(
		`/competitor/${competitorId}`,
		{
			method: "DELETE",
		},
	);
}

export async function getFestivalCatalog() {
	try {
		return await apiRequest<FestivalCatalogItem[]>("/festivals/catalog");
	} catch {
		return [];
	}
}

export async function createFestival(input: FestivalCreateInput) {
	return await apiRequest<FestivalCatalogItem>("/festivals/catalog", {
		method: "POST",
		body: JSON.stringify({
			id: input.id,
			name: input.name,
			date: input.date,
			boost: input.boost,
			platform: input.platform,
		}),
	});
}

export async function updateFestival(
	festivalId: string,
	input: FestivalUpdateInput,
) {
	return await apiRequest<FestivalCatalogItem>(
		`/festivals/catalog/${festivalId}`,
		{
			method: "PUT",
			body: JSON.stringify({
				name: input.name,
				date: input.date,
				boost: input.boost,
				platform: input.platform,
			}),
		},
	);
}

export async function deleteFestival(festivalId: string) {
	return await apiRequest<{ deleted: boolean; id: string }>(
		`/festivals/catalog/${festivalId}`,
		{
			method: "DELETE",
		},
	);
}

export async function simulatePriceChange(
	sku: SKU,
	price: number,
	competitorPrice: number,
	festivalBoost: boolean,
): Promise<SimulatorOutput> {
	return await apiRequest<SimulatorOutput>(`/pricing/simulate/${sku.id}`, {
		method: "POST",
		body: JSON.stringify({
			price,
			competitorPrice,
			festivalBoost,
		}),
	});
}

export async function getFestivalData() {
	try {
		return await apiRequest<FestivalEvent[]>("/festivals");
	} catch {
		return [];
	}
}

export async function getCompetitorData(skuId: string) {
	try {
		return await apiRequest<{
			sku: SKU;
			history: CompetitorHistory[];
			undercutFrequency: number;
			risk: SKU["competitorRisk"];
		}>(`/competitor/${skuId}`);
	} catch {
		return null;
	}
}

export async function getProfitCurve(skuId: string) {
	try {
		const [response, sku] = await Promise.all([
			apiRequest<{
				skuId: string;
				profitCurve: { price: number; profit: number }[];
			}>(`/pricing/${skuId}`),
			apiRequest<SKU>(`/skus/${skuId}`),
		]);
		return { data: response.profitCurve, sku };
	} catch {
		return null;
	}
}

export async function getPortfolioAnalytics() {
	try {
		return await apiRequest<PortfolioDataPoint[]>("/portfolio");
	} catch {
		return [];
	}
}

export async function getInventoryData() {
	try {
		return await apiRequest<
			Array<
				SKU & {
					daysUntilStockout: number;
					reorderPoint: number;
					suggestedOrderQty: number;
					storageCostImpact: number;
					orderCost: number;
				}
			>
		>("/inventory");
	} catch {
		return [];
	}
}
