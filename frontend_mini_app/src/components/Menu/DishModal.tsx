"use client";

import React from "react";
import { FaXmark, FaLeaf, FaSeedling, FaExclamation } from "react-icons/fa6";

type Dish = {
  id: number;
  name: string;
  description: string;
  price: number;
  categoryId: string;
  composition?: string[];
  suitableFor?: string[];
};

interface DishModalProps {
  dish: Dish;
  isOpen: boolean;
  onClose: () => void;
  cart: { [key: number]: number };
  addToCart: (dishId: number) => void;
  removeFromCart: (dishId: number) => void;
}

const DishModal: React.FC<DishModalProps> = ({
  dish,
  isOpen,
  onClose,
  cart,
  addToCart,
  removeFromCart,
}) => {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  React.useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  const getSuitabilityInfo = () => {
    const veganInfo =
      dish.suitableFor?.find((item) =>
        item.toLowerCase().includes("веган")
      ) || "";
    const vegetarianInfo =
      dish.suitableFor?.find((item) =>
        item.toLowerCase().includes("вегетариан")
      ) || "";
    const allergenInfo =
      dish.suitableFor?.find((item) =>
        item.toLowerCase().includes("аллерген")
      ) || "";
    return { veganInfo, vegetarianInfo, allergenInfo };
  };

  const { veganInfo, vegetarianInfo, allergenInfo } = getSuitabilityInfo();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-md max-h-[90vh] overflow-y-auto bg-gradient-to-b from-[#1E1B3A] to-[#130F30] rounded-2xl border border-white/10 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-10 h-10 flex items-center justify-center bg-white/10 rounded-full hover:bg-white/20 transition-colors"
        >
          <FaXmark className="text-white text-lg" />
        </button>

        <div className="h-48 bg-gradient-to-r from-[#8B23CB]/20 to-[#A020F0]/20 rounded-t-2xl flex items-center justify-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-[#8B23CB]/10 to-[#A020F0]/10" />
          <div className="relative text-white text-7xl opacity-30">🍽️</div>

          <div className="absolute bottom-4 right-4 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] px-4 py-2 rounded-lg shadow-lg">
            <span className="text-white font-bold text-xl">{dish.price} ₽</span>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-3">{dish.name}</h2>
            <p className="text-gray-300 text-sm leading-relaxed">{dish.description}</p>
          </div>

          {dish.composition && dish.composition.length > 0 && (
            <div className="mb-6">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-full"></span>
                Состав:
              </h3>
              <div className="flex flex-wrap gap-2">
                {dish.composition.map((item, index) => (
                  <span
                    key={index}
                    className="px-3 py-1.5 bg-white/5 text-gray-300 rounded-lg text-sm backdrop-blur-sm border border-white/5"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {(veganInfo || vegetarianInfo || allergenInfo) && (
            <div className="mb-6">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <span className="w-2 h-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-full"></span>
                Кому подходит:
              </h3>

              {veganInfo && (
                <div className="mb-3 p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="flex items-center gap-2 mb-1">
                    <FaLeaf className="text-green-400" />
                    <span className="text-white font-medium">Веганам:</span>
                  </div>
                  <p
                    className={`text-sm ${
                      veganInfo.includes("Не подходит")
                        ? "text-red-300"
                        : veganInfo.includes("Подходит")
                        ? "text-green-300"
                        : "text-gray-400"
                    }`}
                  >
                    {veganInfo}
                  </p>
                </div>
              )}

              {vegetarianInfo && (
                <div className="mb-3 p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="flex items-center gap-2 mb-1">
                    <FaSeedling className="text-green-500" />
                    <span className="text-white font-medium">Вегетарианцам:</span>
                  </div>
                  <p
                    className={`text-sm ${
                      vegetarianInfo.includes("Не подходит")
                        ? "text-red-300"
                        : vegetarianInfo.includes("Подходит")
                        ? "text-green-300"
                        : "text-gray-400"
                    }`}
                  >
                    {vegetarianInfo}
                  </p>
                </div>
              )}

              {allergenInfo && (
                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="flex items-center gap-2 mb-1">
                    <FaExclamation className="text-yellow-400" />
                    <span className="text-white font-medium">Аллергены:</span>
                  </div>
                  <p
                    className={`text-sm ${
                      allergenInfo.includes("Нет данных")
                        ? "text-gray-400"
                        : "text-yellow-300"
                    }`}
                  >
                    {allergenInfo}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="border-t border-white/10 my-6"></div>

          <div className="flex items-center justify-between">
            <div>
              <span className="text-gray-300 text-sm">Добавить в корзину:</span>
            </div>
            <div className="flex items-center gap-4">
              {cart[dish.id] ? (
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => removeFromCart(dish.id)}
                    className="w-10 h-10 flex items-center justify-center bg-white/20 rounded-full hover:bg-white/30 transition-colors text-white text-xl"
                  >
                    -
                  </button>
                  <span className="text-white font-bold text-xl min-w-[30px] text-center">
                    {cart[dish.id]}
                  </span>
                  <button
                    onClick={() => addToCart(dish.id)}
                    className="w-10 h-10 flex items-center justify-center bg-white/20 rounded-full hover:bg-white/30 transition-colors text-white text-xl"
                  >
                    +
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => addToCart(dish.id)}
                  className="px-6 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                >
                  + Добавить в корзину
                </button>
              )}
            </div>
          </div>
          <div className="mt-6">
            <button
              onClick={() => {
                if (!cart[dish.id]) {
                  addToCart(dish.id);
                }
                onClose();
              }}
              className="w-full py-3.5 bg-gradient-to-r from-[#8B23CB]/80 to-[#A020F0]/80 rounded-lg text-white font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            >
              <span>{cart[dish.id] ? "Закрыть" : "Добавить и закрыть"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DishModal;
