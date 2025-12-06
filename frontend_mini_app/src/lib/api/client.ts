// API client with JWT authentication

import type { User } from "./types";

// API base URL from environment or default to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Token storage key
const TOKEN_KEY = "jwt_token";

/**
 * Get JWT token from localStorage
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Save JWT token to localStorage
 */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove JWT token from localStorage
 */
export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Base fetch request with JWT authentication and error handling
 */
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Add Authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...headers,
      ...options?.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    // Handle HTTP errors
    if (!response.ok) {
      // Try to parse error message from response
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // If JSON parsing fails, use default error message
      }

      // Handle specific status codes
      if (response.status === 401) {
        // Unauthorized - clear token
        removeToken();
        throw new Error("Unauthorized. Please log in again.");
      } else if (response.status === 403) {
        // Forbidden - show alert and redirect to home
        if (typeof window !== "undefined") {
          alert("У вас нет доступа к этой функции");
          window.location.href = "/";
        }
        throw new Error("Forbidden");
      } else if (response.status === 404) {
        throw new Error("Resource not found.");
      } else if (response.status >= 500) {
        // Server error - could implement retry logic here
        throw new Error(`Server error: ${errorMessage}`);
      }

      throw new Error(errorMessage);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    // Parse JSON response
    return await response.json();
  } catch (error) {
    // Re-throw custom errors
    if (error instanceof Error) {
      throw error;
    }

    // Network or other errors
    throw new Error("Network error. Please check your connection.");
  }
}

/**
 * Authenticate with Telegram WebApp initData
 */
export async function authenticateWithTelegram(
  initData: string
): Promise<{ access_token: string; user: User }> {
  const response = await apiRequest<{ access_token: string; user: User }>(
    "/auth/telegram",
    {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    }
  );

  // Save token
  setToken(response.access_token);

  return response;
}
