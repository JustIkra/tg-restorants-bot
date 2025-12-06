import React from "react";

interface CheckoutButtonProps {
  disabled: boolean;
  onClick?: () => void;
  className?: string;
}

const CheckoutButton: React.FC<CheckoutButtonProps> = ({ disabled, onClick, className = "" }) => {
  return (
    <button 
      className={`
        checkout-button 
        px-3 py-1.5 rounded-lg font-medium transition-all duration-300 
        flex items-center justify-center gap-2 backdrop-blur-sm
        text-xs
        xs:px-4 xs:py-2 xs:text-sm
        sm:px-6 sm:py-3 sm:text-base
        min-w-[120px]
        min-h-[40px]
        xs:min-w-[100px]
        sm:min-w-[140px]
        ${!disabled 
          ? 'bg-gradient-to-r from-[#8B23CB]/80 to-[#A020F0]/80 text-white hover:opacity-90 active:scale-95' 
          : 'bg-[#7B6F9C]/40 text-gray-400 cursor-not-allowed'
        }
        ${className}
      `}
      disabled={disabled}
      onClick={onClick}
    >
      <span className="truncate">Оформить заказ</span>
    </button>
  );
};

export default CheckoutButton;