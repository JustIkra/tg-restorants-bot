import React from "react";
import { FaCreditCard } from "react-icons/fa";

interface PaymentMethodProps {
  totalPrice: number;
}

const PaymentMethod: React.FC<PaymentMethodProps> = ({ totalPrice }) => (
  <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
    <FaCreditCard className="text-white text-xl opacity-90 flex-shrink-0" />
    <div className="flex-1">
      <div className="flex items-center gap-2 mb-1">
        <span className="font-semibold text-white text-lg">Баллы обед.ру</span>
        <span className="px-2 py-1 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-xs font-bold rounded-full">1560 баллов</span>
      </div>
      <p className="text-white/70 text-sm">Доступно: 1560 баллов • Будет списано: {totalPrice} баллов</p>
    </div>
  </div>
);

export default PaymentMethod;
