/**
 * Tests for SWR hooks
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useCafes, useCombos, useMenu, useCreateOrder } from '../hooks';
import * as client from '../client';

// Mock apiRequest
jest.mock('../client', () => ({
  apiRequest: jest.fn(),
}));

describe('API Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useCafes', () => {
    it('should fetch cafes with active_only=true by default', async () => {
      const mockCafes = {
        items: [
          { id: 1, name: 'Cafe 1', description: 'Test', is_active: true },
          { id: 2, name: 'Cafe 2', description: 'Test', is_active: true },
        ],
        total: 2,
      };

      (client.apiRequest as jest.Mock).mockResolvedValue(mockCafes);

      const { result } = renderHook(() => useCafes());

      await waitFor(() => expect(result.current.data).toBeDefined());

      expect(client.apiRequest).toHaveBeenCalledWith('/cafes?active_only=true');
      expect(result.current.data).toEqual(mockCafes.items);
    });

    it('should fetch all cafes when activeOnly=false', async () => {
      const mockCafes = {
        items: [{ id: 1, name: 'Cafe 1', description: 'Test', is_active: true }],
        total: 1,
      };

      (client.apiRequest as jest.Mock).mockResolvedValue(mockCafes);

      const { result } = renderHook(() => useCafes(false));

      await waitFor(() => expect(result.current.data).toBeDefined());

      expect(client.apiRequest).toHaveBeenCalledWith('/cafes');
    });
  });

  describe('useCombos', () => {
    it('should fetch combos for a cafe', async () => {
      const mockCombos = {
        items: [
          { id: 1, cafe_id: 1, name: 'Combo 1', categories: ['soup', 'salad'], price: 450, is_available: true },
        ],
        total: 1,
      };

      (client.apiRequest as jest.Mock).mockResolvedValue(mockCombos);

      const { result } = renderHook(() => useCombos(1));

      await waitFor(() => expect(result.current.data).toBeDefined());

      expect(client.apiRequest).toHaveBeenCalledWith('/cafes/1/combos');
      expect(result.current.data).toEqual(mockCombos.items);
    });

    it('should not fetch when cafeId is null', async () => {
      const { result } = renderHook(() => useCombos(null));

      expect(client.apiRequest).not.toHaveBeenCalled();
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('useMenu', () => {
    it('should fetch menu items for a cafe', async () => {
      const mockMenu = {
        items: [
          { id: 1, cafe_id: 1, name: 'Soup', description: 'Test', category: 'soup', price: 100, is_available: true },
        ],
        total: 1,
      };

      (client.apiRequest as jest.Mock).mockResolvedValue(mockMenu);

      const { result } = renderHook(() => useMenu(1));

      await waitFor(() => expect(result.current.data).toBeDefined());

      expect(client.apiRequest).toHaveBeenCalledWith('/cafes/1/menu');
      expect(result.current.data).toEqual(mockMenu.items);
    });

    it('should fetch menu items filtered by category', async () => {
      const mockMenu = {
        items: [
          { id: 1, cafe_id: 1, name: 'Soup', description: 'Test', category: 'soup', price: 100, is_available: true },
        ],
        total: 1,
      };

      (client.apiRequest as jest.Mock).mockResolvedValue(mockMenu);

      const { result } = renderHook(() => useMenu(1, 'soup'));

      await waitFor(() => expect(result.current.data).toBeDefined());

      expect(client.apiRequest).toHaveBeenCalledWith('/cafes/1/menu?category=soup');
    });

    it('should not fetch when cafeId is null', async () => {
      const { result } = renderHook(() => useMenu(null));

      expect(client.apiRequest).not.toHaveBeenCalled();
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('useCreateOrder', () => {
    it('should create order successfully', async () => {
      const mockOrder = {
        id: 1,
        user_tgid: 123,
        cafe_id: 1,
        combo: {
          combo_id: 1,
          combo_name: 'Test Combo',
          combo_price: 450,
          items: [],
        },
        extras: [],
        total_price: 450,
        status: 'pending' as const,
        order_date: '2025-12-06',
        created_at: '2025-12-06T10:00:00',
      };

      (client.apiRequest as jest.Mock).mockResolvedValue(mockOrder);

      const { result } = renderHook(() => useCreateOrder());

      const orderData = {
        cafe_id: 1,
        order_date: '2025-12-06',
        combo_id: 1,
        combo_items: [{ category: 'soup', menu_item_id: 1 }],
        extras: [],
      };

      const createdOrder = await result.current.createOrder(orderData);

      expect(client.apiRequest).toHaveBeenCalledWith('/orders', {
        method: 'POST',
        body: JSON.stringify(orderData),
      });

      expect(createdOrder).toEqual(mockOrder);
    });

    it('should handle order creation errors', async () => {
      const mockError = new Error('Order deadline passed');
      (client.apiRequest as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useCreateOrder());

      const orderData = {
        cafe_id: 1,
        order_date: '2025-12-06',
        combo_id: 1,
        combo_items: [],
        extras: [],
      };

      await expect(result.current.createOrder(orderData)).rejects.toThrow('Order deadline passed');
      await waitFor(() => {
        expect(result.current.error?.message).toBe('Order deadline passed');
      });
    });
  });
});
