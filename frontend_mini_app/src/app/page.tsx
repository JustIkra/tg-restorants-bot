"use client";

import { useState, useMemo, useEffect, useRef, type ReactElement } from "react";
import {
  FaBowlFood,
  FaDrumstickBite,
  FaCarrot,
  FaIceCream,
  FaMugHot,
  FaCookie,
  FaBurger,
  FaPizzaSlice,
  FaFish,
  FaBacon,
  FaLeaf,
  FaUtensils,
  FaCartShopping,
  FaSpinner,
  FaTriangleExclamation,
  FaUserShield,
  FaUser
} from "react-icons/fa6";
import { useRouter } from "next/navigation";

import CafeSelector from "@/components/CafeSelector/CafeSelector";
import CategorySelector from "@/components/CategorySelector/CategorySelector";
import MenuSection from "@/components/Menu/MenuSection";
import DishModal from "@/components/Menu/DishModal";
import ExtrasSection from "@/components/ExtrasSection/ExtrasSection";
import CartSummary from "@/components/Cart/CartSummary";
import CheckoutButton from "@/components/Cart/CheckoutButton";
import TelegramFallback from "@/components/TelegramFallback/TelegramFallback";
import AccessRequestForm from "@/components/AccessRequestForm/AccessRequestForm";
import { useCafes, useMenu } from "@/lib/api/hooks";
import { apiRequest, authenticateWithTelegram } from "@/lib/api/client";
import { isTelegramWebApp, initTelegramWebApp, getTelegramInitData, getTelegramUser } from "@/lib/telegram/webapp";

type AuthState = "loading" | "needs_request" | "success" | "pending" | "rejected" | "error";

export default function Home() {
  const router = useRouter();
  const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);
  const [authState, setAuthState] = useState<AuthState>("loading");
  const [authError, setAuthError] = useState<string | null>(null);
  const [user, setUser] = useState<{ role: string } | null>(null);
  const [telegramUserData, setTelegramUserData] = useState<{ name: string; username: string | null } | null>(null);
  const [activeCafeId, setActiveCafeId] = useState<number | null>(null);
  const [activeCategoryId, setActiveCategoryId] = useState<string | number>("all");

  interface CartItem {
    quantity: number;
    options?: Record<string, string>;
  }

  const [cart, setCart] = useState<{ [key: number]: CartItem }>({});
  const [selectedDish, setSelectedDish] = useState<{ id: number; name: string; description: string; price: number; categoryId: string } | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [availableDays, setAvailableDays] = useState<
    { date: string; weekday: string; can_order: boolean; deadline: string | null; reason: string | null }[]
  >([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [availabilityError, setAvailabilityError] = useState<Error | null>(null);
  const [availabilityLoading, setAvailabilityLoading] = useState(false);

  const rotation = useRef(0);
  const imgRef = useRef<HTMLImageElement>(null);

  const isAuthenticated = authState === "success";

  // Fetch real data from API using SWR hooks (only after authentication)
  const { data: cafesData, error: cafesError, isLoading: cafesLoading } = useCafes(isAuthenticated, true);
  const { data: menuItems, error: menuError, isLoading: menuLoading } = useMenu(isAuthenticated ? activeCafeId : null);
  const { data: extraItems, error: extrasError, isLoading: extrasLoading } = useMenu(isAuthenticated ? activeCafeId : null, "extra");

  // Map cafes data to CafeSelector format
  const cafes = useMemo(() => {
    if (!cafesData) return [];
    return cafesData.map(cafe => ({ id: cafe.id, name: cafe.name }));
  }, [cafesData]);

  // Check if running in Telegram and initialize
  useEffect(() => {
    const inTelegram = isTelegramWebApp();
    setIsInTelegram(inTelegram);

    if (!inTelegram) {
      return;
    }

    // Initialize Telegram WebApp
    initTelegramWebApp();

    // Get Telegram user data
    const telegramUser = getTelegramUser();
    if (telegramUser) {
      const fullName = `${telegramUser.first_name}${telegramUser.last_name ? ' ' + telegramUser.last_name : ''}`;
      setTelegramUserData({
        name: fullName,
        username: telegramUser.username || null,
      });
    }

    // Check if user has already sent access request
    const hasRequestSent = localStorage.getItem("access_request_sent");
    const hasToken = localStorage.getItem("jwt_token");

    // If no token and no request sent, show form
    if (!hasToken && !hasRequestSent) {
      setAuthState("needs_request");
      return;
    }

    // Otherwise, try to authenticate
    const initData = getTelegramInitData();
    if (!initData) {
      setAuthError("Telegram initData недоступен");
      setAuthState("error");
      return;
    }

    authenticateWithTelegram(initData)
      .then((response) => {
        setAuthState("success");
        setUser(response.user);
        console.log("Telegram auth successful");

        // Save user object to localStorage
        localStorage.setItem("user", JSON.stringify(response.user));

        // Clear access request flag on success
        localStorage.removeItem("access_request_sent");

        // Manager can stay on main page - no automatic redirect
      })
      .catch(err => {
        console.error("Telegram auth failed:", err);
        const errorMessage = err instanceof Error
          ? err.message
          : typeof err === 'string'
            ? err
            : (err?.detail || err?.message || "Не удалось авторизоваться");

        // Parse error message to determine auth state
        if (errorMessage.includes("Access request created") || errorMessage.includes("Access request pending")) {
          setAuthState("pending");
        } else if (errorMessage.includes("Access request rejected")) {
          setAuthState("rejected");
        } else {
          setAuthState("error");
          setAuthError(errorMessage);
        }
      });
  }, [router]);

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
    const categoryIcons: Record<string, ReactElement> = {
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

  const handleCategoryClick = (id: string | number) => setActiveCategoryId(id);

  // Load available dates for orders (today if possible, else nearest available)
  useEffect(() => {
    if (!activeCafeId) {
      setAvailableDays([]);
      setSelectedDate(null);
      setAvailabilityError(null);
      return;
    }

    const loadAvailability = async () => {
      setAvailabilityLoading(true);
      try {
        const week = await apiRequest<{
          availability: {
            date: string;
            can_order: boolean;
            deadline: string | null;
            reason: string | null;
          }[];
        }>(`/orders/availability/week?cafe_id=${activeCafeId}`);

        const days =
          week?.availability?.map((item) => ({
            date: item.date,
            // Преобразуем дату в название дня недели для UI
            weekday: new Date(item.date).toLocaleDateString("ru-RU", { weekday: "long" }),
            can_order: item.can_order,
            deadline: item.deadline,
            reason: item.reason,
          })) ?? [];

        setAvailableDays(days);

        const todayIso = new Date().toISOString().split("T")[0];
        const today = days.find(d => d.date === todayIso && d.can_order);
        const nearest = today ?? days.find(d => d.can_order) ?? null;
        setSelectedDate(nearest?.date ?? null);
        setAvailabilityError(null);
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Не удалось загрузить доступные даты");
        setAvailabilityError(error);
        setSelectedDate(null);
        setAvailableDays([]);
      } finally {
        setAvailabilityLoading(false);
      }
    };

    void loadAvailability();
  }, [activeCafeId]);

  const addToCart = (dishId: number, options?: Record<string, string>) =>
    setCart(prev => ({
      ...prev,
      [dishId]: {
        quantity: (prev[dishId]?.quantity || 0) + 1,
        options: options || prev[dishId]?.options
      }
    }));

  const removeFromCart = (dishId: number) =>
    setCart(prev => {
      const current = prev[dishId];
      if (!current || current.quantity <= 1) {
        const { [dishId]: _, ...rest } = prev;
        return rest;
      }
      return {
        ...prev,
        [dishId]: { ...current, quantity: current.quantity - 1 }
      };
    });

  const totalItems = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = Object.entries(cart).reduce((sum, [dishId, item]) => {
    const dish = dishes.find(d => d.id === parseInt(dishId));
    return sum + (dish?.price || 0) * item.quantity;
  }, 0);

  const filteredDishes = activeCategoryId === "all"
    ? dishes
    : dishes.filter(d => d.categoryId === activeCategoryId);

  const handleDishClick = (dish: typeof dishes[0]) => { setSelectedDish(dish); setIsModalOpen(true); };
  const handleCloseModal = () => { setIsModalOpen(false); setSelectedDish(null); };
  const navigateToFortuneWheel = () => router.push("/FortuneWheel");

  const handleCheckout = () => {
    // Save cart and metadata to localStorage for order page
    localStorage.setItem("cart", JSON.stringify(cart));
    localStorage.setItem("activeCafeId", activeCafeId?.toString() || "");
    localStorage.setItem("selectedDate", selectedDate || "");
    router.push("/order");
  };

  const handleAccessRequestSubmit = async (office: string) => {
    const initData = getTelegramInitData();
    if (!initData) {
      throw new Error("Telegram initData недоступен");
    }

    await authenticateWithTelegram(initData, office);
    localStorage.setItem("access_request_sent", "true");
  };

  const handleAccessRequestSuccess = () => {
    setAuthState("pending");
  };

  useEffect(() => {
    const totalRotation = 360 * 6;
    const duration = 10000;
    let startTime: number | null = null;
    let animationFrame: number;

    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

    const animate = (time: number) => {
      if (!startTime) startTime = time;
      const elapsed = time - startTime;
      const t = Math.min(elapsed / duration, 1);
      const eased = easeOutCubic(t);
      rotation.current = totalRotation * eased;
      if (imgRef.current) imgRef.current.style.transform = `rotate(${rotation.current}deg)`;

      if (t < 1) {
        animationFrame = requestAnimationFrame(animate);
      } else {
        rotation.current = 0;
        if (imgRef.current) imgRef.current.style.transform = `rotate(0deg)`;

        setTimeout(() => requestAnimationFrame((t) => animate(t)), 60000);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, []);

  // Combined error state
  const error = cafesError || menuError || extrasError;

  const noAvailableDates = !selectedDate && !availabilityLoading && availableDays.length > 0;
  const isCheckoutDisabled = totalItems === 0 || !selectedDate || availabilityLoading || noAvailableDates;

  // DEBUG: Check why checkout is disabled
  useEffect(() => {
    console.log("Checkout Debug:", {
      totalItems,
      selectedDate,
      availabilityLoading,
      availableDays: availableDays.length,
      noAvailableDates,
      isCheckoutDisabled
    });
  }, [totalItems, selectedDate, availabilityLoading, availableDays, noAvailableDates, isCheckoutDisabled]);

  // Show loading while checking Telegram environment
  if (isInTelegram === null) {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
        <FaSpinner className="text-white text-4xl animate-spin" />
      </div>
    );
  }

  // Show fallback UI if not in Telegram
  if (!isInTelegram) {
    return <TelegramFallback />;
  }

  // Show loading while authenticating
  if (authState === "loading") {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
          <p className="text-white">Авторизация...</p>
        </div>
      </div>
    );
  }

  // Show access request form for new users
  if (authState === "needs_request") {
    if (!telegramUserData) {
      return (
        <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 max-w-md">
            <FaTriangleExclamation className="text-red-400 text-4xl mx-auto mb-4" />
            <h2 className="text-white text-xl font-bold mb-2">Ошибка</h2>
            <p className="text-red-200">Не удалось получить данные Telegram</p>
          </div>
        </div>
      );
    }

    return (
      <AccessRequestForm
        name={telegramUserData.name}
        username={telegramUserData.username}
        onSubmit={handleAccessRequestSubmit}
        onSuccess={handleAccessRequestSuccess}
      />
    );
  }

  // Show pending screen
  if (authState === "pending") {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
        <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
        <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

        <div className="relative bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 md:p-8 max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center">
            <FaSpinner className="text-white text-2xl animate-spin" />
          </div>
          <h2 className="text-white text-2xl font-bold mb-2">Ожидание одобрения</h2>
          <p className="text-gray-300 text-sm mb-4">
            Ваш запрос на доступ отправлен менеджеру. Пожалуйста, дождитесь одобрения.
          </p>
          <p className="text-gray-400 text-xs">
            Вы получите уведомление, когда ваш запрос будет обработан.
          </p>
        </div>
      </div>
    );
  }

  // Show rejected screen
  if (authState === "rejected") {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
        <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
        <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

        <div className="relative bg-red-500/20 border border-red-500/50 rounded-2xl p-6 md:p-8 max-w-md text-center">
          <FaTriangleExclamation className="text-red-400 text-4xl mx-auto mb-4" />
          <h2 className="text-white text-2xl font-bold mb-2">Доступ отклонён</h2>
          <p className="text-red-200 text-sm mb-4">
            К сожалению, ваш запрос на доступ был отклонён менеджером.
          </p>
          <p className="text-gray-400 text-xs">
            Для получения дополнительной информации обратитесь к менеджеру.
          </p>
        </div>
      </div>
    );
  }

  // Show error if auth failed
  if (authState === "error") {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
        <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
        <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

        <div className="relative bg-red-500/20 border border-red-500/50 rounded-2xl p-6 md:p-8 max-w-md text-center">
          <FaTriangleExclamation className="text-red-400 text-4xl mx-auto mb-4" />
          <h2 className="text-white text-xl font-bold mb-2">Ошибка авторизации</h2>
          <p className="text-red-200">{authError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full min-h-screen bg-[#130F30] overflow-x-hidden">

      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />


      <div className="relative w-full md:w-[90%] min-h-[90vh] mx-auto bg-white/5 backdrop-blur-md border border-white/10 rounded-none md:rounded-2xl overflow-visible">
        <div className="px-4 pt-6 md:px-6 flex justify-between items-start">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">Food Delivery</h1>
            <p className="text-gray-300 text-sm md:text-base">Выберите категорию и блюдо</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/profile")}
              className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg"
              aria-label="Профиль"
            >
              <FaUser className="text-white text-xl" />
            </button>
            {user?.role === "manager" && (
              <button
                onClick={() => router.push("/manager")}
                className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg"
                aria-label="Панель менеджера"
              >
                <FaUserShield className="text-white text-xl" />
              </button>
            )}
            <button
              onClick={navigateToFortuneWheel}
              className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B23CB]/50 to-[#A020F0]/50 border border-white/20 backdrop-blur-md shadow-lg overflow-hidden"
            >
              <img ref={imgRef} src="/image.png" alt="Колесо фортуны" className="w-8 h-8 object-contain" />
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-4 md:mx-6 mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex items-center gap-3">
            <FaTriangleExclamation className="text-red-400 text-xl flex-shrink-0" />
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
              <div className="mb-4">
                <div className="flex items-center gap-2 text-white text-sm md:text-base">
                  <span className="font-semibold">Дата заказа:</span>
                  {availabilityLoading && (
                    <span className="flex items-center gap-2 text-gray-200">
                      <FaSpinner className="animate-spin" />
                      Проверяем доступность...
                    </span>
                  )}
                  {!availabilityLoading && selectedDate && (
                    <span className="px-2 py-1 rounded-md bg-white/10 border border-white/10">
                      {selectedDate}
                    </span>
                  )}
                  {!availabilityLoading && !selectedDate && (
                    <span className="text-red-200">Нет доступных дат</span>
                  )}
                </div>
                {availabilityError && (
                  <p className="text-red-200 text-sm mt-1">{availabilityError.message}</p>
                )}
                {noAvailableDates && (
                  <p className="text-red-200 text-sm mt-1">Попробуйте выбрать другое кафе или время.</p>
                )}
              </div>

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
                <MenuSection
                  dishes={filteredDishes}
                  cart={cart}
                  addToCart={addToCart}
                  removeFromCart={removeFromCart}
                  onDishClick={handleDishClick}
                />
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

      <div style={{
          position: "fixed",
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 50,
          padding: "16px",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          background: "rgba(255, 255, 255, 0.05)",
      }}>
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
            <CheckoutButton disabled={isCheckoutDisabled} onClick={handleCheckout} />
          </div>
        </div>
      </div>

      {selectedDish && (
        <DishModal
          dish={selectedDish}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          cart={cart}
          addToCart={addToCart}
          removeFromCart={removeFromCart}
        />
      )}

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
