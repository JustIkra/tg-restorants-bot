"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  FaSpinner,
  FaTriangleExclamation,
  FaUsers,
  FaStore,
  FaUtensils,
  FaEnvelope,
  FaChartBar,
  FaChevronLeft,
  FaChevronRight,
} from "react-icons/fa6";

import { authenticateWithTelegram } from "@/lib/api/client";
import {
  isTelegramWebApp,
  initTelegramWebApp,
  getTelegramInitData,
} from "@/lib/telegram/webapp";

type TabId = "users" | "cafes" | "menu" | "requests" | "reports";

interface Tab {
  id: TabId;
  name: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  { id: "users", name: "Пользователи", icon: <FaUsers /> },
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "requests", name: "Запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaChartBar /> },
];

export default function ManagerPage() {
  const router = useRouter();
  const [isInTelegram] = useState<boolean | null>(() => {
    if (typeof window !== 'undefined') {
      return isTelegramWebApp();
    }
    return null;
  });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("users");
  const tabsContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftGradient, setShowLeftGradient] = useState(false);
  const [showRightGradient, setShowRightGradient] = useState(false);

  // Check if running in Telegram and authenticate
  useEffect(() => {
    const inTelegram = isInTelegram;

    if (!inTelegram) {
      return;
    }

    // Initialize Telegram WebApp
    initTelegramWebApp();

    // Authenticate with backend
    const initData = getTelegramInitData();
    if (!initData) {
      setAuthError("Telegram initData недоступен");
      return;
    }

    authenticateWithTelegram(initData)
      .then((response) => {
        // Check if user is manager
        if (response.user.role !== "manager") {
          // Redirect non-managers to main page
          router.push("/");
          return;
        }

        // Store user in localStorage for other components
        if (typeof window !== "undefined") {
          localStorage.setItem("user", JSON.stringify(response.user));
        }

        setIsAuthenticated(true);
        console.log("Manager authenticated successfully");
      })
      .catch((err) => {
        console.error("Telegram auth failed:", err);
        const errorMessage =
          err instanceof Error
            ? err.message
            : typeof err === "string"
            ? err
            : err?.detail || err?.message || "Не удалось авторизоваться";
        setAuthError(errorMessage);
      });
  }, [router]);

  // Handle tabs scroll gradient visibility
  useEffect(() => {
    const container = tabsContainerRef.current;
    if (!container) return;

    const updateGradients = () => {
      const { scrollLeft, scrollWidth, clientWidth } = container;
      setShowLeftGradient(scrollLeft > 0);
      setShowRightGradient(scrollLeft < scrollWidth - clientWidth - 1);
    };

    updateGradients();
    container.addEventListener("scroll", updateGradients);
    window.addEventListener("resize", updateGradients);

    return () => {
      container.removeEventListener("scroll", updateGradients);
      window.removeEventListener("resize", updateGradients);
    };
  }, []);

  const scrollTabs = (direction: "left" | "right") => {
    const container = tabsContainerRef.current;
    if (!container) return;

    const scrollAmount = 200;
    container.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  // Show loading while checking Telegram environment
  if (isInTelegram === null) {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
        <FaSpinner className="text-white text-4xl animate-spin" />
      </div>
    );
  }

  // Show error if not in Telegram
  if (!isInTelegram) {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 max-w-md">
          <FaTriangleExclamation className="text-yellow-400 text-4xl mx-auto mb-4" />
          <h2 className="text-white text-xl font-bold mb-2 text-center">
            Доступ через Telegram
          </h2>
          <p className="text-gray-300 text-center">
            Эта панель доступна только через Telegram Mini App.
          </p>
        </div>
      </div>
    );
  }

  // Show loading while authenticating
  if (isInTelegram && !isAuthenticated && !authError) {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="text-white text-4xl animate-spin mx-auto mb-4" />
          <p className="text-white">Авторизация...</p>
        </div>
      </div>
    );
  }

  // Show error if auth failed
  if (isInTelegram && authError) {
    return (
      <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 max-w-md">
          <FaTriangleExclamation className="text-red-400 text-4xl mx-auto mb-4" />
          <h2 className="text-white text-xl font-bold mb-2">
            Ошибка авторизации
          </h2>
          <p className="text-red-200">{authError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full min-h-screen bg-[#130F30] overflow-x-hidden">
      {/* Background gradients */}
      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      <div className="relative w-full md:w-[90%] min-h-screen mx-auto bg-white/5 backdrop-blur-md border border-white/10 rounded-none md:rounded-2xl overflow-visible">
        {/* Header */}
        <div className="px-4 pt-6 md:px-6 pb-4 border-b border-white/10">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">
            Панель менеджера
          </h1>
          <p className="text-gray-300 text-sm md:text-base">
            Управление системой заказов обедов
          </p>
        </div>

        {/* Tabs navigation */}
        <div className="relative px-4 md:px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            {/* Left gradient button */}
            {showLeftGradient && (
              <button
                onClick={() => scrollTabs("left")}
                className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r from-[#8B23CB] to-[#A020F0] flex items-center justify-center text-white hover:opacity-80 transition-opacity"
                aria-label="Scroll left"
              >
                <FaChevronLeft />
              </button>
            )}

            {/* Tabs container */}
            <div
              ref={tabsContainerRef}
              className="flex-1 flex gap-2 overflow-x-auto scrollbar-hide"
            >
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg transition-all
                    ${
                      activeTab === tab.id
                        ? "bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white"
                        : "bg-transparent text-gray-400 hover:text-white hover:bg-white/5"
                    }
                  `}
                >
                  <span className="text-lg">{tab.icon}</span>
                  <span className="text-sm md:text-base font-medium whitespace-nowrap">
                    {tab.name}
                  </span>
                </button>
              ))}
            </div>

            {/* Right gradient button */}
            {showRightGradient && (
              <button
                onClick={() => scrollTabs("right")}
                className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r from-[#8B23CB] to-[#A020F0] flex items-center justify-center text-white hover:opacity-80 transition-opacity"
                aria-label="Scroll right"
              >
                <FaChevronRight />
              </button>
            )}
          </div>
        </div>

        {/* Content area */}
        <div className="px-4 md:px-6 py-6">
          {activeTab === "users" && (
            <div className="text-white">
              <h2 className="text-xl font-bold mb-4">Управление пользователями</h2>
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-300 text-center">
                  Компонент UserList будет здесь (Подзадача 4)
                </p>
              </div>
            </div>
          )}

          {activeTab === "cafes" && (
            <div className="text-white">
              <h2 className="text-xl font-bold mb-4">Управление кафе</h2>
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-300 text-center">
                  Компонент CafeList будет здесь (Подзадача 5)
                </p>
              </div>
            </div>
          )}

          {activeTab === "menu" && (
            <div className="text-white">
              <h2 className="text-xl font-bold mb-4">Управление меню</h2>
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-300 text-center">
                  Компонент MenuManager будет здесь (Подзадача 6)
                </p>
              </div>
            </div>
          )}

          {activeTab === "requests" && (
            <div className="text-white">
              <h2 className="text-xl font-bold mb-4">Запросы на подключение</h2>
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-300 text-center">
                  Компонент RequestsList будет здесь (Подзадача 7)
                </p>
              </div>
            </div>
          )}

          {activeTab === "reports" && (
            <div className="text-white">
              <h2 className="text-xl font-bold mb-4">Отчёты</h2>
              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-300 text-center">
                  Компонент ReportsList будет здесь (Подзадача 7)
                </p>
              </div>
            </div>
          )}
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
