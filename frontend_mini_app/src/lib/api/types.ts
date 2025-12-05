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

export interface MenuItem {
  id: number;
  cafe_id: number;
  name: string;
  description: string | null;
  category: string;
  price: number | null;
  is_available: boolean;
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

export interface Order {
  id: number;
  user_tgid: number;
  user_name: string;
  cafe_id: number;
  cafe_name: string;
  order_date: string;
  status: "pending" | "confirmed" | "cancelled";
  combo: OrderCombo;
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
  combo_id: number;
  combo_items: {
    category: string;
    menu_item_id: number;
  }[];
  extras?: {
    menu_item_id: number;
    quantity: number;
  }[];
  notes?: string;
}

// Response wrappers
export interface ListResponse<T> {
  items: T[];
  total?: number;
}

export interface BalanceResponse {
  balance: number;
  weekly_limit: number;
  spent_this_week: number;
}

export interface OrderAvailabilityResponse {
  can_order: boolean;
  deadline: string | null;
  time_remaining: string | null;
  reason: string | null;
}
