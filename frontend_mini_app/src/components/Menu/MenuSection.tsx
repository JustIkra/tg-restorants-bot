import React from "react";

type Dish = { id: number; name: string; description: string; price: number; categoryId: string };

interface MenuSectionProps {
  dishes: Dish[];
  cart: { [key: number]: number };
  addToCart: (dishId: number) => void;
  removeFromCart: (dishId: number) => void;
}

const MenuSection: React.FC<MenuSectionProps> = ({ dishes, cart, addToCart, removeFromCart }) => (
  <div className="space-y-3">
    {dishes.map((dish) => (
      <div 
        key={dish.id}
        className="relative bg-[#7B6F9C]/20 rounded-[12px] p-4 transition-all duration-300 hover:bg-[#7B6F9C]/30 backdrop-blur-sm border border-white/5"
      >
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h4 className="text-white font-medium text-lg mb-1">{dish.name}</h4>
            <p className="text-gray-300 text-sm mb-3">{dish.description}</p>
            <div className="flex items-center justify-between">
              <span className="text-white font-bold text-lg">{dish.price} ₽</span>
              {cart[dish.id] ? (
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => removeFromCart(dish.id)}
                    className="w-8 h-8 flex items-center justify-center bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                  >
                    -
                  </button>
                  <span className="text-white font-medium min-w-[24px] text-center">
                    {cart[dish.id]}
                  </span>
                  <button 
                    onClick={() => addToCart(dish.id)}
                    className="w-8 h-8 flex items-center justify-center bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                  >
                    +
                  </button>
                </div>
              ) : (
                <button 
                  onClick={() => addToCart(dish.id)}
                  className="px-4 py-2 bg-white/20 rounded-lg text-white text-sm font-medium hover:bg-white/30 transition-colors flex items-center gap-2"
                >
                  + Добавить
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    ))}
  </div>
);

export default MenuSection;
