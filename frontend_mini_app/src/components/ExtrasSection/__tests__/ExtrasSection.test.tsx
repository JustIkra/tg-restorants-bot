/**
 * Tests for ExtrasSection component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ExtrasSection from '../ExtrasSection';
import { MenuItem } from '@/lib/api/types';

describe('ExtrasSection', () => {
  const mockExtras: MenuItem[] = [
    {
      id: 101,
      cafe_id: 1,
      name: 'Фокачча с пряным маслом',
      description: '60 г.',
      category: 'extra',
      price: 50,
      is_available: true,
    },
    {
      id: 102,
      cafe_id: 1,
      name: 'Морс клюквенный',
      description: '300 мл.',
      category: 'extra',
      price: 40,
      is_available: true,
    },
    {
      id: 103,
      cafe_id: 1,
      name: 'Десерт дня',
      description: 'Сюрприз от шефа',
      category: 'extra',
      price: null,
      is_available: true,
    },
  ];

  it('should render section title', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(screen.getByText('Дополнительно')).toBeInTheDocument();
  });

  it('should render all extra items', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(screen.getByText('Фокачча с пряным маслом')).toBeInTheDocument();
    expect(screen.getByText('Морс клюквенный')).toBeInTheDocument();
    expect(screen.getByText('Десерт дня')).toBeInTheDocument();
  });

  it('should render item descriptions', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(screen.getByText('60 г.')).toBeInTheDocument();
    expect(screen.getByText('300 мл.')).toBeInTheDocument();
    expect(screen.getByText('Сюрприз от шефа')).toBeInTheDocument();
  });

  it('should render prices when available', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(screen.getByText('50 ₽')).toBeInTheDocument();
    expect(screen.getByText('40 ₽')).toBeInTheDocument();
  });

  it('should not render price when null', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    const dessertCard = screen.getByText('Десерт дня').closest('div');
    const priceElements = dessertCard?.querySelectorAll('.font-semibold');

    // Should not have price element
    expect(priceElements?.length).toBe(0);
  });

  it('should show "Добавить" button when quantity is 0', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    const addButtons = screen.getAllByText('+ Добавить');
    expect(addButtons.length).toBe(3);
  });

  it('should call addToCart when "Добавить" is clicked', () => {
    const handleAdd = jest.fn();

    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{}}
        addToCart={handleAdd}
        removeFromCart={jest.fn()}
      />
    );

    const addButtons = screen.getAllByText('+ Добавить');
    fireEvent.click(addButtons[0]);

    expect(handleAdd).toHaveBeenCalledWith(101);
  });

  it('should show quantity controls when item is in cart', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{ 101: 2 }}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('−')).toBeInTheDocument();
    expect(screen.getByText('+')).toBeInTheDocument();
  });

  it('should call addToCart when + button is clicked', () => {
    const handleAdd = jest.fn();

    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{ 101: 1 }}
        addToCart={handleAdd}
        removeFromCart={jest.fn()}
      />
    );

    const plusButton = screen.getByText('+').closest('button');
    fireEvent.click(plusButton!);

    expect(handleAdd).toHaveBeenCalledWith(101);
  });

  it('should call removeFromCart when − button is clicked', () => {
    const handleRemove = jest.fn();

    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{ 101: 2 }}
        addToCart={jest.fn()}
        removeFromCart={handleRemove}
      />
    );

    const minusButton = screen.getByText('−').closest('button');
    fireEvent.click(minusButton!);

    expect(handleRemove).toHaveBeenCalledWith(101);
  });

  it('should display correct quantity from cart', () => {
    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{ 101: 3, 102: 1 }}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('should render nothing when extras array is empty', () => {
    const { container } = render(
      <ExtrasSection
        extras={[]}
        cart={{}}
        addToCart={jest.fn()}
        removeFromCart={jest.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should handle multiple items in cart', () => {
    const handleAdd = jest.fn();
    const handleRemove = jest.fn();

    render(
      <ExtrasSection
        extras={mockExtras}
        cart={{ 101: 2, 102: 1, 103: 3 }}
        addToCart={handleAdd}
        removeFromCart={handleRemove}
      />
    );

    // All items should show quantity controls
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();

    // No "Добавить" buttons should be visible
    expect(screen.queryByText('+ Добавить')).not.toBeInTheDocument();
  });
});
