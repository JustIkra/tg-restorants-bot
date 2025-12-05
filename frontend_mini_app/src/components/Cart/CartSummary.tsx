import React from "react";

interface CartSummaryProps {
  totalItems: number;
  totalPrice: number;
}

const CartSummary: React.FC<CartSummaryProps> = ({ totalItems, totalPrice }) => (
  <div className="flex items-center gap-3">
    <div>
      <p className="text-white font-medium">Итого: {totalPrice} ₽</p>
      <p className="text-gray-300 text-sm">{totalItems} товара(ов)</p>
    </div>
  </div>
);

export default CartSummary;
