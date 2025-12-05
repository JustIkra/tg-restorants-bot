import React from "react";

interface CheckoutButtonProps {
  disabled: boolean;
  onClick?: () => void;
}

const CheckoutButton: React.FC<CheckoutButtonProps> = ({ disabled, onClick }) => (
  <button 
    className={`px-8 py-3 rounded-lg font-medium transition-all duration-300 flex items-center gap-2 backdrop-blur-sm
      ${!disabled 
        ? 'bg-gradient-to-r from-[#8B23CB]/80 to-[#A020F0]/80 text-white hover:opacity-90' 
        : 'bg-[#7B6F9C]/40 text-gray-400 cursor-not-allowed'
      }`}
    disabled={disabled}
    onClick={onClick}
  >
    Оформить заказ
  </button>
);

export default CheckoutButton;
