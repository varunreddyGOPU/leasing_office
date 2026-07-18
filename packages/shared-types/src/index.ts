// Shared API types — mirror apps/api/app/schemas.py. Keep in sync when the
// API surface grows in later phases.

export interface FloorPlan {
  id: number;
  name: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  base_rent: number;
  description: string | null;
  current_asking_rent: number | null;
  available_units: number;
}

export interface UnitAvailability {
  id: number;
  unit_number: string;
  tier: "standard" | "premium";
  status: "available" | "occupied" | "maintenance";
  available_date: string | null;
  floor_plan_id: number;
  floor_plan_name: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
}

export type LeaseTermMonths = 6 | 9 | 12 | 15;

export interface EstimateRequest {
  floor_plan_id: number;
  move_in_date: string;
  lease_term_months: LeaseTermMonths;
  pets: { type: "cat" | "dog"; count: number }[];
  carports: number;
  furnished: boolean;
  email: string;
  name?: string;
  phone?: string;
}

export interface EstimateLineItem {
  label: string;
  amount: number;
}

export interface EstimateResponse {
  monthly_estimate: number;
  move_in_total: number;
  monthly_breakdown: EstimateLineItem[];
  move_in_breakdown: EstimateLineItem[];
}

export interface NewsItem {
  id: number;
  title: string;
  source: string | null;
  url: string;
  category: string;
  zip: string;
  published_at: string | null;
}
