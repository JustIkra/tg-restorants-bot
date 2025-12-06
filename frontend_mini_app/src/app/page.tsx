"use client";

import { useState, useMemo, useEffect } from "react";
import {
  FaBowlFood, FaDrumstickBite, FaCarrot, FaIceCream, FaMugHot, FaCookie, FaBurger, FaPizzaSlice, FaFish, FaBacon, FaLeaf, FaUtensils, FaCartShopping, FaSpinner, FaExclamationTriangle
} from "react-icons/fa6";

import CafeSelector from "@/components/CafeSelector/CafeSelector";
import CategorySelector from "@/components/CategorySelector/CategorySelector";
import MenuSection from "@/components/Menu/MenuSection";
import ExtrasSection from "@/components/ExtrasSection/ExtrasSection";
import CartSummary from "@/components/Cart/CartSummary";
import CheckoutButton from "@/components/Cart/CheckoutButton";
import { useCafes, useCombos, useMenu } from "@/lib/api/hooks";

export default function Home() {
  const [activeCafeId, setActiveCafeId] = useState<number | null>(null);
  const [activeCategoryId, setActiveCategoryId] = useState<string>("all");
  const [cart, setCart] = useState<{ [key: number]: number }>({});

  // Fetch real data from API using SWR hooks
  const { data: cafesData, error: cafesError, isLoading: cafesLoading } = useCafes(true);
  const { data: combosData, error: combosError, isLoading: combosLoading } = useCombos(activeCafeId);
  const { data: menuItems, error: menuError, isLoading: menuLoading } = useMenu(activeCafeId);
  const { data: extraItems, error: extrasError, isLoading: extrasLoading } = useMenu(activeCafeId, "extra");

  // Map cafes data to CafeSelector format
  const cafes = useMemo(() => {
    if (!cafesData) return [];
    return cafesData.map(cafe => ({ id: cafe.id, name: cafe.name }));
  }, [cafesData]);

  // Auto-select first cafe when data loads
  useEffect(() => {
    if (cafes.length > 0 && activeCafeId === null) {
      setActiveCafeId(cafes[0].id);
    }
  }, [cafes, activeCafeId]);

  // Extract unique categories from menu items
  const categories = useMemo(() => {
    const categorySet = new Set<string>();
    if (menuItems) {
      menuItems.forEach(item => categorySet.add(item.category));
    }

    const categoryList = [{ id: "all", name: "Все", icon: <FaBowlFood /> }];

    // Map category names to icons
    const categoryIcons: { [key: string]: JSX.Element } = {
      soup: <FaBowlFood />,
      main: <FaDrumstickBite />,
      salad: <FaCarrot />,
      dessert: <FaIceCream />,
      drink: <FaMugHot />,
      snack: <FaCookie />,
      burger: <FaBurger />,
      pizza: <FaPizzaSlice />,
      sushi: <FaFish />,
      steak: <FaBacon />,
      vegetarian: <FaLeaf />,
      pasta: <FaUtensils />,
    };

    categorySet.forEach(cat => {
      categoryList.push({
        id: cat,
        name: cat.charAt(0).toUpperCase() + cat.slice(1),
        icon: categoryIcons[cat] || <FaUtensils />
      });
    });

    return categoryList;
  }, [menuItems]);

  // Map menu items to dishes format for MenuSection
  const dishes = useMemo(() => {
    if (!menuItems) return [];
    return menuItems.map(item => ({
      id: item.id,
      name: item.name,
      description: item.description || "",
      price: item.price || 0,
      categoryId: item.category,
    }));
  }, [menuItems]);

  const handleCafeClick = (id: number) => {
    setActiveCafeId(id);
    setCart({}); // Reset cart when switching cafes
  };

  const handleCategoryClick = (id: string) => setActiveCategoryId(id);

  const addToCart = (dishId: number) =>
    setCart(prev => ({ ...prev, [dishId]: (prev[dishId] || 0) + 1 }));

  const removeFromCart = (dishId: number) =>
    setCart(prev => {
      const copy = { ...prev };
      if (!copy[dishId]) return copy;
      if (copy[dishId] > 1) copy[dishId]--;
      else delete copy[dishId];
      return copy;
    });

  const totalItems = Object.values(cart).reduce((s, v) => s + v, 0);

  const totalPrice = dishes
    .filter(d => !!cart[d.id])
    .reduce((sum, d) => sum + d.price * (cart[d.id] || 0), 0);

  const filteredDishes = activeCategoryId === "all"
    ? dishes
    : dishes.filter(d => d.categoryId === activeCategoryId);

  // Combined loading state
  const isLoading = cafesLoading || (activeCafeId !== null && (menuLoading || combosLoading));

  // Combined error state
  const error = cafesError || menuError || combosError || extrasError;

  return (
    <div className="relative w-full min-h-screen bg-[#130F30] overflow-x-hidden">

      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      <div className="relative w-full md:w-[90%] min-h-[90vh] mx-auto bg-white/5 backdrop-blur-md border border-white/10 rounded-none md:rounded-2xl overflow-visible">
        <div className="px-4 pt-6 md:px-6">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">Food Delivery</h1>
          <p className="text-gray-300 text-sm md:text-base">Выберите категорию и блюдо</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-4 md:mx-6 mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex items-center gap-3">
            <FaExclamationTriangle className="text-red-400 text-xl flex-shrink-0" />
            <div>
              <p className="text-red-200 font-semibold">Ошибка загрузки данных</p>
              <p className="text-red-300 text-sm">{error.message}</p>
            </div>
          </div>
        )}

        <div className="px-4 md:px-6 py-4">
          <h2 className="text-white text-base md:text-lg font-semibold mb-3">Названия заведений</h2>
          {cafesLoading ? (
            <div className="flex items-center justify-center py-8">
              <FaSpinner className="text-white text-2xl animate-spin" />
              <span className="ml-3 text-white">Загрузка кафе...</span>
            </div>
          ) : cafes.length === 0 ? (
            <div className="text-gray-400 text-center py-8">Нет доступных кафе</div>
          ) : (
            <div className="flex overflow-x-auto pb-4 scrollbar-hide">
              <CafeSelector cafes={cafes} activeCafeId={activeCafeId ?? -1} onCafeClick={handleCafeClick} />
            </div>
          )}
        </div>

        {activeCafeId && (
          <>
            <div className="px-4 md:px-6">
              <h2 className="text-white text-base md:text-lg font-semibold mb-3">Категории блюд</h2>
              {menuLoading ? (
                <div className="flex items-center justify-center py-4">
                  <FaSpinner className="text-white text-xl animate-spin" />
                  <span className="ml-2 text-white text-sm">Загрузка категорий...</span>
                </div>
              ) : (
                <div className="flex overflow-x-auto pb-2 scrollbar-hide">
                  <CategorySelector categories={categories} activeCategoryId={activeCategoryId} onCategoryClick={handleCategoryClick} />
                </div>
              )}
            </div>

            <div className="px-4 md:px-6 pt-4">
              <h3 className="text-white text-lg md:text-xl font-semibold mb-4">Меню кафе</h3>
              {menuLoading ? (
                <div className="flex items-center justify-center py-12">
                  <FaSpinner className="text-white text-3xl animate-spin" />
                  <span className="ml-3 text-white">Загрузка меню...</span>
                </div>
              ) : filteredDishes.length === 0 ? (
                <div className="text-gray-400 text-center py-12">
                  {dishes.length === 0 ? "Меню пока не добавлено" : "Нет блюд в этой категории"}
                </div>
              ) : (
                <MenuSection dishes={filteredDishes} cart={cart} addToCart={addToCart} removeFromCart={removeFromCart} />
              )}
            </div>

            <div className="px-4 md:px-6 pt-4 pb-[180px]">
              {extrasLoading ? (
                <div className="flex items-center justify-center py-4">
                  <FaSpinner className="text-white animate-spin" />
                  <span className="ml-2 text-white">Загрузка дополнений...</span>
                </div>
              ) : extraItems && extraItems.length > 0 ? (
                <ExtrasSection extras={extraItems} cart={cart} addToCart={addToCart} removeFromCart={removeFromCart} />
              ) : null}
            </div>
          </>
        )}

        {!activeCafeId && !cafesLoading && cafes.length > 0 && (
          <div className="px-4 md:px-6 py-12 text-center">
            <p className="text-gray-400">Выберите кафе, чтобы увидеть меню</p>
          </div>
        )}
      </div>

     <div
  style={{
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 50,
    padding: "16px",
    backdropFilter: "blur(20px)",
    WebkitBackdropFilter: "blur(20px)",
    background: "rgba(255, 255, 255, 0.05)", 
  }}
>
  <div className="max-w-2xl mx-auto bg-[#7B6F9C]/30 border border-white/10 backdrop-blur-xl rounded-xl p-4 shadow-lg">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="relative">
          <FaCartShopping className="text-white text-xl" />
          {totalItems > 0 && (
            <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-gradient-to-br from-[#8B23CB] to-[#A020F0] text-white text-xs flex items-center justify-center font-bold">
              {totalItems}
            </span>
          )}
        </div>
        <CartSummary totalItems={totalItems} totalPrice={totalPrice} />
      </div>
      <CheckoutButton disabled={totalItems === 0} />
    </div>
  </div>
</div>


      <style jsx global>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
