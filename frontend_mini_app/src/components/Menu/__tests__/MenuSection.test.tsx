/**
 * Tests for MenuSection component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MenuSection from '../MenuSection';
import { MenuItem } from '@/lib/api/types';

describe('MenuSection', () => {
  const mockItems: MenuItem[] = [
    {
      id: 1,
      cafe_id: 1,
      name: 'Борщ украинский',
      description: 'Традиционный украинский борщ',
      category: 'soup',
      price: 120,
      is_available: true,
    },
    {
      id: 2,
      cafe_id: 1,
      name: 'Куриный бульон',
      description: 'Легкий бульон с лапшой',
      category: 'soup',
      price: 100,
      is_available: true,
    },
    {
      id: 3,
      cafe_id: 1,
      name: 'Солянка сборная',
      description: null,
      category: 'soup',
      price: 150,
      is_available: true,
    },
  ];

  it('should render category label', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={null}
        onItemSelect={jest.fn()}
      />
    );

    expect(screen.getByText('Супы')).toBeInTheDocument();
  });

  it('should render all menu items', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={null}
        onItemSelect={jest.fn()}
      />
    );

    expect(screen.getByText('Борщ украинский')).toBeInTheDocument();
    expect(screen.getByText('Куриный бульон')).toBeInTheDocument();
    expect(screen.getByText('Солянка сборная')).toBeInTheDocument();
  });

  it('should render item descriptions when available', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={null}
        onItemSelect={jest.fn()}
      />
    );

    expect(screen.getByText('Традиционный украинский борщ')).toBeInTheDocument();
    expect(screen.getByText('Легкий бульон с лапшой')).toBeInTheDocument();
  });

  it('should not render description when null', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={null}
        onItemSelect={jest.fn()}
      />
    );

    const solyankaItem = screen.getByText('Солянка сборная').closest('button');
    const descriptionElements = solyankaItem?.querySelectorAll('.text-gray-300');

    expect(descriptionElements?.length).toBe(0);
  });

  it('should call onItemSelect when item is clicked', () => {
    const handleSelect = jest.fn();

    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={null}
        onItemSelect={handleSelect}
      />
    );

    const firstItem = screen.getByText('Борщ украинский').closest('button');
    fireEvent.click(firstItem!);

    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('should highlight selected item with radio button', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={2}
        onItemSelect={jest.fn()}
      />
    );

    const selectedButton = screen.getByText('Куриный бульон').closest('button');

    // Check for gradient background on selected item
    expect(selectedButton).toHaveClass('from-[#7B6F9C]/40');
    expect(selectedButton).toHaveClass('to-[#9B8BBF]/40');

    // Check for filled radio button
    const radioOuter = selectedButton?.querySelector('.w-5.h-5.rounded-full');
    expect(radioOuter).toHaveClass('border-white');
    expect(radioOuter).toHaveClass('bg-white');

    const radioInner = radioOuter?.querySelector('.w-2\\.5.h-2\\.5');
    expect(radioInner).toBeInTheDocument();
  });

  it('should show empty radio button for unselected items', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={2}
        onItemSelect={jest.fn()}
      />
    );

    const unselectedButton = screen.getByText('Борщ украинский').closest('button');
    const radioOuter = unselectedButton?.querySelector('.w-5.h-5.rounded-full');

    expect(radioOuter).toHaveClass('border-white/40');
    expect(radioOuter).not.toHaveClass('bg-white');

    const radioInner = radioOuter?.querySelector('.w-2\\.5.h-2\\.5');
    expect(radioInner).not.toBeInTheDocument();
  });

  it('should allow changing selection', () => {
    const handleSelect = jest.fn();

    const { rerender } = render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={1}
        onItemSelect={handleSelect}
      />
    );

    const secondItem = screen.getByText('Куриный бульон').closest('button');
    fireEvent.click(secondItem!);

    expect(handleSelect).toHaveBeenCalledWith(2);

    // Update selection
    rerender(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={mockItems}
        selectedItemId={2}
        onItemSelect={handleSelect}
      />
    );

    const newSelectedButton = screen.getByText('Куриный бульон').closest('button');
    expect(newSelectedButton).toHaveClass('from-[#7B6F9C]/40');
  });

  it('should render with empty items array', () => {
    render(
      <MenuSection
        category="soup"
        categoryLabel="Супы"
        items={[]}
        selectedItemId={null}
        onItemSelect={jest.fn()}
      />
    );

    expect(screen.getByText('Супы')).toBeInTheDocument();

    const buttons = screen.queryAllByRole('button');
    expect(buttons.length).toBe(0);
  });
});
