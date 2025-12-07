import React from "react";
import type { MenuItem } from "@/lib/api/types";

interface CartItem {
  quantity: number;
  options?: Record<string, string>;
}

interface ExtrasSectionProps {
  extras: MenuItem[];                      // category = "extra"
  cart: { [itemId: number]: CartItem };    // item_id -> CartItem
  addToCart: (itemId: number, options?: Record<string, string>) => void;
  removeFromCart: (itemId: number) => void;
}

const ExtrasSection: React.FC<ExtrasSectionProps> = ({
  extras,
  cart,
  addToCart,
  removeFromCart
}) => {
  if (extras.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-white font-semibold text-xl">Дополнительно</h3>
      <div className="grid grid-cols-1 gap-3">
        {extras.map((extra) => {
          const quantity = cart[extra.id]?.quantity || 0;
          return (
            <div
              key={extra.id}
              className="relative rounded-[12px] p-4 transition-all duration-300 backdrop-blur-sm border bg-[#7B6F9C]/20 border-white/5 hover:bg-[#7B6F9C]/30"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h4 className="text-white font-medium text-base">{extra.name}</h4>
                  {extra.description && (
                    <p className="text-gray-300 text-sm mt-1">{extra.description}</p>
                  )}
                  {extra.price !== null && (
                    <p className="text-white font-semibold text-base mt-2">{extra.price} ₽</p>
                  )}
                </div>
                <div className="flex-shrink-0">
                  {quantity === 0 ? (
                    <button
                      onClick={() => addToCart(extra.id)}
                      className="relative px-5 py-2.5 rounded-lg overflow-hidden group transition-all duration-300"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-[#8B23CB] via-[#A020F0] to-[#7723B6] opacity-80 group-hover:opacity-100 transition-opacity duration-300" />
                      <span className="relative text-white font-medium text-sm whitespace-nowrap">
                        + Добавить
                      </span>
                    </button>
                  ) : (
                    <div className="flex items-center gap-3 bg-[#7B6F9C]/40 rounded-lg px-2 py-1.5">
                      <button
                        onClick={() => removeFromCart(extra.id)}
                        className="w-7 h-7 flex items-center justify-center rounded-md bg-white/10 hover:bg-white/20 transition-colors duration-200"
                      >
                        <span className="text-white text-lg font-semibold leading-none">−</span>
                      </button>
                      <span className="text-white font-semibold text-base min-w-[20px] text-center">
                        {quantity}
                      </span>
                      <button
                        onClick={() => addToCart(extra.id)}
                        className="w-7 h-7 flex items-center justify-center rounded-md bg-white/10 hover:bg-white/20 transition-colors duration-200"
                      >
                        <span className="text-white text-lg font-semibold leading-none">+</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ExtrasSection;
