// TypeScript types from API specification

// Entities
export interface User {
  tgid: number;
  name: string;
  office: string;
  role: "user" | "manager";
  is_active: boolean;
  created_at: string;
}

export interface Cafe {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Combo {
  id: number;
  cafe_id: number;
  name: string;
  categories: string[];
  price: number;
  is_available: boolean;
}

export interface MenuItemOption {
  id: number;
  menu_item_id: number;
  name: string;
  values: string[];
  is_required: boolean;
}

export interface MenuItem {
  id: number;
  cafe_id: number;
  name: string;
  description: string | null;
  category: string;
  price: number | null;
  is_available: boolean;
  options?: MenuItemOption[];
}

export interface OrderComboItem {
  category: string;
  menu_item_id: number;
  menu_item_name: string;
}

export interface OrderCombo {
  combo_id: number;
  combo_name: string;
  combo_price: number;
  items: OrderComboItem[];
}

export interface OrderExtra {
  menu_item_id: number;
  menu_item_name: string;
  quantity: number;
  price: number;
  subtotal: number;
}

// Order items types
export interface ComboItem {
  type: "combo";
  category: "soup" | "salad" | "main";
  menu_item_id: number;
}

export interface StandaloneItem {
  type: "standalone";
  menu_item_id: number;
  quantity: number;
  options: Record<string, string>;
}

export type OrderItem = ComboItem | StandaloneItem;

// Input types for extras
export interface ExtraInput {
  menu_item_id: number;
  quantity: number;
}

export interface Order {
  id: number;
  user_tgid: number;
  user_name: string;
  cafe_id: number;
  cafe_name: string;
  order_date: string;
  status: "pending" | "confirmed" | "cancelled";
  combo_id: number | null;
  combo?: OrderCombo;
  items: OrderItem[];
  extras: OrderExtra[];
  notes: string | null;
  total_price: number;
  created_at: string;
  updated_at: string;
}

// Request payloads
export interface CreateOrderRequest {
  cafe_id: number;
  order_date: string;
  combo_id: number | null;
  items: OrderItem[];
  extras?: ExtraInput[];
  notes?: string;
}

// Response wrappers
export interface ListResponse<T> {
  items: T[];
  total?: number;
}

export interface BalanceResponse {
  tgid: number;
  weekly_limit: number | null;
  spent_this_week: number;
  remaining: number | null;
}

export interface OrderAvailabilityResponse {
  can_order: boolean;
  deadline: string | null;
  time_remaining: string | null;
  reason: string | null;
}

export interface CafeRequest {
  id: number;
  cafe_name: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface Summary {
  id: number;
  cafe_id: number;
  cafe_name: string;
  date: string;
  status: "pending" | "completed";
  created_at: string;
}

export interface OrderStats {
  orders_last_30_days: number;
  categories: { [category: string]: { count: number; percent: number } };
  unique_dishes: number;
  favorite_dishes: { name: string; count: number }[];
}

export interface RecommendationsResponse {
  summary: string | null;
  tips: string[];
  stats: OrderStats;
  generated_at: string | null;
}

// User Access Request types
export type UserAccessRequestStatus = "pending" | "approved" | "rejected";

export interface UserAccessRequest {
  id: number;
  tgid: number;
  name: string;
  office: string;
  username: string | null;
  status: UserAccessRequestStatus;
  processed_at: string | null;
  created_at: string;
}

export interface UserAccessRequestListResponse {
  items: UserAccessRequest[];
  total?: number;
}

// User update request
export interface UserUpdate {
  name?: string;
  office?: string;
  role?: "user" | "manager";
}

// Deadlines
export interface DeadlineItem {
  weekday: number;          // 0=Mon, 1=Tue, ..., 6=Sun
  deadline_time: string;    // "10:00"
  is_enabled: boolean;
  advance_days: number;
}

export interface DeadlineScheduleResponse {
  cafe_id: number;
  schedule: DeadlineItem[];
}
