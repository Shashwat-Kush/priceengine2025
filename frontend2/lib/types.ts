export type Marketplace = "Amazon" | "Flipkart" | "Meesho"
export type Sensitivity = "High" | "Medium" | "Low"
export type InventoryStatus = "Healthy" | "Low" | "Critical" | "Overstock"
export type CompetitorRisk = "High" | "Medium" | "Low"

export type SKU = {
  id: string
  name: string
  category: string
  marketplace: Marketplace
  currentPrice: number
  cost: number
  competitorPrice: number
  inventory: number
  dailyDemand: number
  priceSensitivity: Sensitivity
  competitorRisk: CompetitorRisk
  inventoryStatus: InventoryStatus
  margin: number
  leadTimeDays: number
  storageCostPerUnit: number
  baseDemand: number
  festivalBoostPotential: Sensitivity
  marketplaceStrength: Sensitivity
}

export type DashboardKPIs = {
  totalRevenue: number
  totalProfit: number
  missedProfit: number
  inventoryAlerts: number
  undercutAlerts: number
}

export type RecommendedAction = {
  skuId: string
  skuName: string
  marketplace: Marketplace
  currentPrice: number
  recommendedMin: number
  recommendedMax: number
  estimatedProfitChange: number
  reason: string
}

export type Alert = {
  id: string
  type: "low_stock" | "overpriced" | "festival_opportunity" | "undercut"
  severity: "high" | "medium" | "low"
  skuId: string
  skuName: string
  message: string
}

export type FestivalEvent = {
  id: string
  name: string
  date: string
  daysUntil: number
  platform: Marketplace[]
  skuOpportunities: FestivalSKUOpportunity[]
}

export type FestivalSKUOpportunity = {
  skuId: string
  skuName: string
  suggestedPrice: number
  currentPrice: number
  expectedUnits: number
  inventoryRequired: number
  profitImpact: number
}

export type CompetitorHistory = {
  date: string
  ourPrice: number
  competitorPrice: number
}

export type SimulatorOutput = {
  expectedUnits: number
  revenue: number
  profit: number
  stockoutDate: string
}

export type PortfolioDataPoint = {
  skuId: string
  name: string
  margin: number
  priceSensitivity: number
  profit: number
  marketplace: Marketplace
}

export type SKUCreateInput = {
  id: string
  name: string
  category: string
  marketplace: string
  currentPrice: number
  cost: number
  competitorPrice?: number
  inventory: number
  dailyDemand: number
  leadTimeDays: number
  storageCostPerUnit: number
  baseDemand: number
  priceSensitivity: "high" | "medium" | "low"
  festivalBoostPotential: "high" | "medium" | "low"
}

export type SKUUpdateInput = Partial<{
  name: string
  category: string
  baseDemand: number
  priceSensitivity: "high" | "medium" | "low"
  festivalBoostPotential: "high" | "medium" | "low"
  marketplace: string
  currentPrice: number
  cost: number
  competitorPrice: number
  inventory: number
  dailyDemand: number
  leadTimeDays: number
  storageCostPerUnit: number
}>

export type Listing = {
  id: string
  skuId: string
  marketplace: string
  currentPrice: number
  cost: number
  inventory: number
  dailyDemand: number
  leadTimeDays: number
  storageCostPerUnit: number
}

export type ListingCreateInput = Omit<Listing, "id"> & { id?: string }

export type ListingUpdateInput = Partial<Omit<Listing, "id">>

export type CompetitorRecord = {
  id: string
  listingId: string
  skuId?: string
  marketplace?: string
  name: string
  price: number
  rating: number
  shippingDays: number
}

export type CompetitorCreateInput = {
  id?: string
  listingId: string
  name: string
  price: number
  rating: number
  shippingDays: number
}

export type CompetitorUpdateInput = Partial<{
  listingId: string
  name: string
  price: number
  rating: number
  shippingDays: number
}>

export type FestivalCatalogItem = {
  id: string
  name: string
  date: string
  boost: number
  platform: string[]
}

export type FestivalCreateInput = {
  id?: string
  name: string
  date: string
  boost: number
  platform: string[]
}

export type FestivalUpdateInput = Partial<{
  name: string
  date: string
  boost: number
  platform: string[]
}>
