// SWR hooks for API requests

"use client";

import useSWR, { useSWRConfig } from "swr";
import { useState } from "react";
import { apiRequest } from "./client";
import type {
  User,
  Cafe,
  Combo,
  MenuItem,
  Order,
  CreateOrderRequest,
  ListResponse,
  CafeRequest,
  Summary,
  BalanceResponse,
  RecommendationsResponse,
} from "./types";

interface UseDataResult<T> {
  data: T[] | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
}

/**
 * SWR fetcher function
 */
const fetcher = <T,>(endpoint: string) => apiRequest<T>(endpoint);

/**
 * Hook to fetch cafes
 * @param shouldFetch - If false, skip fetching (useful for waiting for auth)
 * @param activeOnly - If true, filter only active cafes
 */
export function useCafes(shouldFetch = true, activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<Cafe>>(
    shouldFetch ? `/cafes${activeOnly ? "?active_only=true" : ""}` : null,
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to fetch combos for a specific cafe
 * @param cafeId - Cafe ID (null to skip fetching)
 */
export function useCombos(cafeId: number | null): UseDataResult<Combo> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<Combo>>(
    cafeId ? `/cafes/${cafeId}/combos` : null,
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to fetch menu items for a specific cafe
 * @param cafeId - Cafe ID (null to skip fetching)
 * @param category - Optional category filter (e.g., "soup", "salad", "main", "extra")
 */
export function useMenu(
  cafeId: number | null,
  category?: string
): UseDataResult<MenuItem> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<MenuItem>>(
    cafeId
      ? `/cafes/${cafeId}/menu${category ? `?category=${category}` : ""}`
      : null,
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to create an order (mutation)
 * Returns a function to create order and loading state
 */
export function useCreateOrder(): {
  createOrder: (data: CreateOrderRequest) => Promise<Order>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createOrder = async (data: CreateOrderRequest): Promise<Order> => {
    setIsLoading(true);
    setError(null);

    try {
      const order = await apiRequest<Order>("/orders", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setIsLoading(false);
      return order;
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to create order");
      setError(error);
      setIsLoading(false);
      throw error;
    }
  };

  return {
    createOrder,
    isLoading,
    error,
  };
}

/**
 * Hook to fetch user's orders
 * @param filters - Optional filters for orders
 */
export function useOrders(filters?: {
  date?: string;
  cafeId?: number;
  status?: "pending" | "confirmed" | "cancelled";
}): UseDataResult<Order> {
  const params = new URLSearchParams();
  if (filters?.date) params.append("date", filters.date);
  if (filters?.cafeId) params.append("cafe_id", filters.cafeId.toString());
  if (filters?.status) params.append("status", filters.status);

  const queryString = params.toString();
  const endpoint = `/orders${queryString ? `?${queryString}` : ""}`;
  const { data, error, isLoading, mutate } = useSWR<ListResponse<Order>>(
    endpoint,
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to fetch cafe requests (manager only)
 */
export function useCafeRequests(): UseDataResult<CafeRequest> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<CafeRequest>>(
    "/cafe-requests",
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to approve cafe request (manager only)
 */
export function useApproveCafeRequest(): {
  approveRequest: (requestId: number) => Promise<void>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const approveRequest = async (requestId: number): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await apiRequest(`/cafe-requests/${requestId}/approve`, {
        method: "POST",
      });
      setIsLoading(false);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to approve request");
      setError(error);
      setIsLoading(false);
      throw error;
    }
  };

  return {
    approveRequest,
    isLoading,
    error,
  };
}

/**
 * Hook to reject cafe request (manager only)
 */
export function useRejectCafeRequest(): {
  rejectRequest: (requestId: number) => Promise<void>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const rejectRequest = async (requestId: number): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await apiRequest(`/cafe-requests/${requestId}/reject`, {
        method: "POST",
      });
      setIsLoading(false);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to reject request");
      setError(error);
      setIsLoading(false);
      throw error;
    }
  };

  return {
    rejectRequest,
    isLoading,
    error,
  };
}

/**
 * Hook to fetch summaries (manager only)
 */
export function useSummaries(): UseDataResult<Summary> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<Summary>>(
    "/summaries",
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to create summary (manager only)
 */
export function useCreateSummary(): {
  createSummary: (cafeId: number, date: string) => Promise<Summary>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createSummary = async (cafeId: number, date: string): Promise<Summary> => {
    setIsLoading(true);
    setError(null);

    try {
      const summary = await apiRequest<Summary>("/summaries", {
        method: "POST",
        body: JSON.stringify({ cafe_id: cafeId, date }),
      });
      setIsLoading(false);
      return summary;
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to create summary");
      setError(error);
      setIsLoading(false);
      throw error;
    }
  };

  return {
    createSummary,
    isLoading,
    error,
  };
}

/**
 * Hook to delete summary (manager only)
 */
export function useDeleteSummary(): {
  deleteSummary: (summaryId: number) => Promise<void>;
  isLoading: boolean;
  error: Error | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const deleteSummary = async (summaryId: number): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await apiRequest(`/summaries/${summaryId}`, {
        method: "DELETE",
      });
      setIsLoading(false);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to delete summary");
      setError(error);
      setIsLoading(false);
      throw error;
    }
  };

  return {
    deleteSummary,
    isLoading,
    error,
  };
}

// ========================================
// User Management Hooks (Manager Only)
// ========================================

/**
 * Hook to fetch all users (manager only)
 */
export function useUsers(): UseDataResult<User> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<User>>(
    "/users",
    fetcher
  );
  return {
    data: data?.items,
    error,
    isLoading,
    mutate
  };
}

/**
 * Hook to create a new user (manager only)
 */
export function useCreateUser() {
  const { mutate } = useSWRConfig();
  const createUser = async (data: { tgid: number; name: string; office: string }) => {
    const result = await apiRequest<User>("/users", { method: "POST", body: JSON.stringify(data) });
    mutate("/users");
    return result;
  };
  return { createUser };
}

/**
 * Hook to update user access (manager only)
 */
export function useUpdateUserAccess() {
  const { mutate } = useSWRConfig();
  const updateAccess = async (tgid: number, is_active: boolean) => {
    const result = await apiRequest<User>(`/users/${tgid}/access`, {
      method: "PATCH",
      body: JSON.stringify({ is_active })
    });
    mutate("/users");
    return result;
  };
  return { updateAccess };
}

/**
 * Hook to delete a user (manager only)
 */
export function useDeleteUser() {
  const { mutate } = useSWRConfig();
  const deleteUser = async (tgid: number) => {
    await apiRequest(`/users/${tgid}`, { method: "DELETE" });
    mutate("/users");
  };
  return { deleteUser };
}

// ========================================
// Cafe Management Hooks (Manager Only)
// ========================================

/**
 * Hook to create a new cafe (manager only)
 */
export function useCreateCafe() {
  const { mutate } = useSWRConfig();
  const createCafe = async (data: { name: string; description?: string }) => {
    const result = await apiRequest<Cafe>("/cafes", { method: "POST", body: JSON.stringify(data) });
    mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
    return result;
  };
  return { createCafe };
}

/**
 * Hook to update cafe details (manager only)
 */
export function useUpdateCafe() {
  const { mutate } = useSWRConfig();
  const updateCafe = async (cafeId: number, data: { name?: string; description?: string }) => {
    const result = await apiRequest<Cafe>(`/cafes/${cafeId}`, { method: "PATCH", body: JSON.stringify(data) });
    mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
    return result;
  };
  return { updateCafe };
}

/**
 * Hook to delete a cafe (manager only)
 */
export function useDeleteCafe() {
  const { mutate } = useSWRConfig();
  const deleteCafe = async (cafeId: number) => {
    await apiRequest(`/cafes/${cafeId}`, { method: "DELETE" });
    mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
  };
  return { deleteCafe };
}

/**
 * Hook to update cafe status (manager only)
 */
export function useUpdateCafeStatus() {
  const { mutate } = useSWRConfig();
  const updateStatus = async (cafeId: number, is_active: boolean) => {
    const result = await apiRequest<Cafe>(`/cafes/${cafeId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active })
    });
    mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"), undefined, { revalidate: true });
    return result;
  };
  return { updateStatus };
}

// ========================================
// Combo Management Hooks (Manager Only)
// ========================================

/**
 * Hook to create a new combo (manager only)
 */
export function useCreateCombo() {
  const { mutate } = useSWRConfig();
  const createCombo = async (cafeId: number, data: { name: string; categories: string[]; price: number }) => {
    const result = await apiRequest<Combo>(`/cafes/${cafeId}/combos`, { method: "POST", body: JSON.stringify(data) });
    mutate(`/cafes/${cafeId}/combos`);
    return result;
  };
  return { createCombo };
}

/**
 * Hook to update a combo (manager only)
 */
export function useUpdateCombo() {
  const { mutate } = useSWRConfig();
  const updateCombo = async (cafeId: number, comboId: number, data: Partial<Combo>) => {
    const result = await apiRequest<Combo>(`/cafes/${cafeId}/combos/${comboId}`, { method: "PATCH", body: JSON.stringify(data) });
    mutate(`/cafes/${cafeId}/combos`);
    return result;
  };
  return { updateCombo };
}

/**
 * Hook to delete a combo (manager only)
 */
export function useDeleteCombo() {
  const { mutate } = useSWRConfig();
  const deleteCombo = async (cafeId: number, comboId: number) => {
    await apiRequest(`/cafes/${cafeId}/combos/${comboId}`, { method: "DELETE" });
    mutate(`/cafes/${cafeId}/combos`);
  };
  return { deleteCombo };
}

// ========================================
// Menu Item Management Hooks (Manager Only)
// ========================================

/**
 * Hook to create a new menu item (manager only)
 */
export function useCreateMenuItem() {
  const { mutate } = useSWRConfig();
  const createMenuItem = async (cafeId: number, data: { name: string; description?: string; category: string; price?: number }) => {
    const result = await apiRequest<MenuItem>(`/cafes/${cafeId}/menu`, { method: "POST", body: JSON.stringify(data) });
    mutate(`/cafes/${cafeId}/menu`);
    return result;
  };
  return { createMenuItem };
}

/**
 * Hook to update a menu item (manager only)
 */
export function useUpdateMenuItem() {
  const { mutate } = useSWRConfig();
  const updateMenuItem = async (cafeId: number, itemId: number, data: Partial<MenuItem>) => {
    const result = await apiRequest<MenuItem>(`/cafes/${cafeId}/menu/${itemId}`, { method: "PATCH", body: JSON.stringify(data) });
    mutate(`/cafes/${cafeId}/menu`);
    return result;
  };
  return { updateMenuItem };
}

/**
 * Hook to delete a menu item (manager only)
 */
export function useDeleteMenuItem() {
  const { mutate } = useSWRConfig();
  const deleteMenuItem = async (cafeId: number, itemId: number) => {
    await apiRequest(`/cafes/${cafeId}/menu/${itemId}`, { method: "DELETE" });
    mutate(`/cafes/${cafeId}/menu`);
  };
  return { deleteMenuItem };
}

// ========================================
// User Profile Hooks
// ========================================

/**
 * Hook to fetch user recommendations
 * @param tgid - User's Telegram ID (null to skip fetching)
 */
export function useUserRecommendations(tgid: number | null) {
  const { data, error, isLoading, mutate } = useSWR<RecommendationsResponse>(
    tgid ? `/users/${tgid}/recommendations` : null,
    fetcher
  );
  return { data, error, isLoading, mutate };
}

/**
 * Hook to fetch user balance
 * @param tgid - User's Telegram ID (null to skip fetching)
 */
export function useUserBalance(tgid: number | null) {
  const { data, error, isLoading, mutate } = useSWR<BalanceResponse>(
    tgid ? `/users/${tgid}/balance` : null,
    fetcher
  );
  return { data, error, isLoading, mutate };
}

/**
 * Hook to update user balance limit (manager only)
 */
export function useUpdateBalanceLimit() {
  const { mutate } = useSWRConfig();
  const updateLimit = async (tgid: number, weekly_limit: number | null) => {
    const result = await apiRequest<User>(`/users/${tgid}/balance/limit`, {
      method: "PATCH",
      body: JSON.stringify({ weekly_limit })
    });
    mutate(`/users/${tgid}/balance`);
    mutate("/users");
    return result;
  };
  return { updateLimit };
}
