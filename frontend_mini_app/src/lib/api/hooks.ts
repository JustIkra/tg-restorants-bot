// SWR hooks for API requests

"use client";

import useSWR from "swr";
import type { SWRResponse } from "swr";
import { useState } from "react";
import { apiRequest } from "./client";
import type {
  Cafe,
  Combo,
  MenuItem,
  Order,
  CreateOrderRequest,
  ListResponse,
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
 * @param activeOnly - If true, filter only active cafes
 */
export function useCafes(activeOnly = true): UseDataResult<Cafe> {
  const { data, error, isLoading, mutate } = useSWR<ListResponse<Cafe>>(
    `/cafes${activeOnly ? "?active_only=true" : ""}`,
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
