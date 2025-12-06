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
  FaCartShopping,
  FaWallet,
} from "react-icons/fa6";

import { authenticateWithTelegram } from "@/lib/api/client";
import {
  isTelegramWebApp,
  initTelegramWebApp,
  getTelegramInitData,
} from "@/lib/telegram/webapp";
import {
  useUsers,
  useCreateUser,
  useUpdateUserAccess,
  useDeleteUser,
} from "@/lib/api/hooks";
import type { Cafe } from "@/lib/api/types";
import UserList from "@/components/Manager/UserList";
import UserForm from "@/components/Manager/UserForm";
import CafeList from "@/components/Manager/CafeList";
import CafeForm from "@/components/Manager/CafeForm";
import MenuManager from "@/components/Manager/MenuManager";
import RequestsList from "@/components/Manager/RequestsList";
import ReportsList from "@/components/Manager/ReportsList";
import BalanceManager from "@/components/Manager/BalanceManager";

type TabId = "users" | "balances" | "cafes" | "menu" | "requests" | "reports";

interface Tab {
  id: TabId;
  name: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  { id: "users", name: "Пользователи", icon: <FaUsers /> },
  { id: "balances", name: "Балансы", icon: <FaWallet /> },
  { id: "cafes", name: "Кафе", icon: <FaStore /> },
  { id: "menu", name: "Меню", icon: <FaUtensils /> },
  { id: "requests", name: "Запросы", icon: <FaEnvelope /> },
  { id: "reports", name: "Отчёты", icon: <FaChartBar /> },
];

export default function ManagerPage() {
  const router = useRouter();
  const [isInTelegram, setIsInTelegram] = useState<boolean | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("users");
  const tabsContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftGradient, setShowLeftGradient] = useState(false);
  const [showRightGradient, setShowRightGradient] = useState(false);

  // Users tab state
  const [showUserForm, setShowUserForm] = useState(false);
  const { data: users, error: usersError, isLoading: usersLoading } = useUsers();
  const { createUser } = useCreateUser();
  const { updateAccess } = useUpdateUserAccess();
  const { deleteUser } = useDeleteUser();

  // Cafes tab state
  const [showCafeForm, setShowCafeForm] = useState(false);
  const [editingCafe, setEditingCafe] = useState<Cafe | null>(null);

  // Check if running in Telegram and authenticate
  useEffect(() => {
    const inTelegram = isTelegramWebApp();
    setIsInTelegram(inTelegram);

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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">
                Панель менеджера
              </h1>
              <p className="text-gray-300 text-sm md:text-base">
                Управление системой заказов обедов
              </p>
            </div>
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white shadow-lg hover:opacity-90 transition-opacity"
              aria-label="Сделать заказ"
            >
              <FaCartShopping className="text-lg" />
              <span className="hidden sm:inline text-sm font-medium">Сделать заказ</span>
            </button>
          </div>
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
            <div className="text-white space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Управление пользователями</h2>
                <button
                  onClick={() => setShowUserForm(!showUserForm)}
                  className="px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white font-medium hover:opacity-90 transition-opacity"
                >
                  {showUserForm ? "Отмена" : "Добавить пользователя"}
                </button>
              </div>

              {showUserForm && (
                <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                  <UserForm
                    onSubmit={async (data) => {
                      try {
                        await createUser(data);
                        setShowUserForm(false);
                      } catch (err) {
                        console.error("Failed to create user:", err);
                        // UserForm should show error if needed
                      }
                    }}
                    onCancel={() => setShowUserForm(false)}
                  />
                </div>
              )}

              <UserList
                users={users}
                isLoading={usersLoading}
                error={usersError}
                onToggleAccess={async (tgid, newStatus) => {
                  try {
                    await updateAccess(tgid, newStatus);
                  } catch (err) {
                    console.error("Failed to toggle access:", err);
                  }
                }}
                onDelete={async (tgid) => {
                  try {
                    await deleteUser(tgid);
                  } catch (err) {
                    console.error("Failed to delete user:", err);
                  }
                }}
              />
            </div>
          )}

          {activeTab === "balances" && (
            <div className="text-white">
              <BalanceManager />
            </div>
          )}

          {activeTab === "cafes" && (
            <div className="text-white space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Управление кафе</h2>
                <button
                  onClick={() => {
                    setEditingCafe(null);
                    setShowCafeForm(!showCafeForm);
                  }}
                  className="px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-lg text-white font-medium hover:opacity-90 transition-opacity"
                >
                  {showCafeForm ? "Отмена" : "Добавить кафе"}
                </button>
              </div>

              {(showCafeForm || editingCafe) && (
                <CafeForm
                  mode={editingCafe ? "edit" : "create"}
                  initialData={editingCafe || undefined}
                  onSubmit={() => {
                    setShowCafeForm(false);
                    setEditingCafe(null);
                  }}
                  onCancel={() => {
                    setShowCafeForm(false);
                    setEditingCafe(null);
                  }}
                />
              )}

              <CafeList
                onEdit={(cafe) => {
                  setEditingCafe(cafe);
                  setShowCafeForm(false);
                }}
              />
            </div>
          )}

          {activeTab === "menu" && (
            <div className="text-white">
              <MenuManager />
            </div>
          )}

          {activeTab === "requests" && (
            <div className="text-white">
              <RequestsList />
            </div>
          )}

          {activeTab === "reports" && (
            <div className="text-white">
              <ReportsList />
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
