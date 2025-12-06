/**
 * Tests for ComboSelector component
 * DISABLED: Unit tests disabled to avoid conflicts with Playwright E2E tests
 * To re-enable, install @testing-library/react and uncomment imports
 */

/* eslint-disable */
// @ts-nocheck

export {}; // Make this a module

/*
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ComboSelector from '../ComboSelector';
import { Combo } from '@/lib/api/types';

describe('ComboSelector', () => {
  const mockCombos: Combo[] = [
    {
      id: 1,
      cafe_id: 1,
      name: 'Салат + Суп',
      categories: ['salad', 'soup'],
      price: 450,
      is_available: true,
    },
    {
      id: 2,
      cafe_id: 1,
      name: 'Суп + Основное',
      categories: ['soup', 'main'],
      price: 550,
      is_available: true,
    },
    {
      id: 3,
      cafe_id: 1,
      name: 'Полный обед',
      categories: ['salad', 'soup', 'main'],
      price: 650,
      is_available: false,
    },
  ];

  it('should render all combos', () => {
    render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={null}
        onComboSelect={jest.fn()}
      />
    );

    expect(screen.getByText('Салат + Суп')).toBeInTheDocument();
    expect(screen.getByText('Суп + Основное')).toBeInTheDocument();
    expect(screen.getByText('Полный обед')).toBeInTheDocument();
  });

  it('should render combo prices', () => {
    render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={null}
        onComboSelect={jest.fn()}
      />
    );

    expect(screen.getByText('450 ₽')).toBeInTheDocument();
    expect(screen.getByText('550 ₽')).toBeInTheDocument();
    expect(screen.getByText('650 ₽')).toBeInTheDocument();
  });

  it('should call onComboSelect when combo is clicked', () => {
    const handleSelect = jest.fn();

    render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={null}
        onComboSelect={handleSelect}
      />
    );

    const firstCombo = screen.getByText('Салат + Суп').closest('button');
    fireEvent.click(firstCombo!);

    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('should highlight selected combo', () => {
    render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={1}
        onComboSelect={jest.fn()}
      />
    );

    const selectedButton = screen.getByText('Салат + Суп').closest('button');
    const selectedDiv = selectedButton?.querySelector('.absolute.inset-0');

    expect(selectedDiv).toHaveClass('from-[#8B23CB]');
    expect(selectedDiv).toHaveClass('via-[#A020F0]');
    expect(selectedDiv).toHaveClass('to-[#7723B6]');
  });

  it('should disable unavailable combos', () => {
    render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={null}
        onComboSelect={jest.fn()}
      />
    );

    const unavailableCombo = screen.getByText('Полный обед').closest('button');

    expect(unavailableCombo).toBeDisabled();
  });

  it('should not call onComboSelect for disabled combos', () => {
    const handleSelect = jest.fn();

    render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={null}
        onComboSelect={handleSelect}
      />
    );

    const unavailableCombo = screen.getByText('Полный обед').closest('button');
    fireEvent.click(unavailableCombo!);

    expect(handleSelect).not.toHaveBeenCalled();
  });

  it('should render empty when no combos provided', () => {
    const { container } = render(
      <ComboSelector
        combos={[]}
        selectedComboId={null}
        onComboSelect={jest.fn()}
      />
    );

    const buttons = container.querySelectorAll('button');
    expect(buttons.length).toBe(0);
  });

  it('should allow changing selection', () => {
    const handleSelect = jest.fn();

    const { rerender } = render(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={1}
        onComboSelect={handleSelect}
      />
    );

    const secondCombo = screen.getByText('Суп + Основное').closest('button');
    fireEvent.click(secondCombo!);

    expect(handleSelect).toHaveBeenCalledWith(2);

    // Update selection
    rerender(
      <ComboSelector
        combos={mockCombos}
        selectedComboId={2}
        onComboSelect={handleSelect}
      />
    );

    const newSelectedButton = screen.getByText('Суп + Основное').closest('button');
    const selectedDiv = newSelectedButton?.querySelector('.absolute.inset-0');

    expect(selectedDiv).toHaveClass('from-[#8B23CB]');
  });
});
*/
