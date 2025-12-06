"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FaArrowLeft } from "react-icons/fa6";
import { User } from "@/lib/api/types";
import { useUserRecommendations, useUserBalance } from "@/lib/api/hooks";
import ProfileStats from "@/components/Profile/ProfileStats";
import ProfileRecommendations from "@/components/Profile/ProfileRecommendations";
import ProfileBalance from "@/components/Profile/ProfileBalance";

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 animate-pulse">
      <div className="h-6 bg-white/10 rounded w-1/2 mb-4"></div>
      <div className="space-y-2">
        <div className="h-4 bg-white/10 rounded w-3/4"></div>
        <div className="h-4 bg-white/10 rounded w-1/2"></div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const [user] = useState<User | null>(() => {
    // Initialize user from localStorage
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem("user");
      if (storedUser) {
        try {
          return JSON.parse(storedUser);
        } catch (err) {
          console.error("Failed to parse user from localStorage:", err);
          return null;
        }
      }
    }
    return null;
  });

  useEffect(() => {
    // Redirect to home if no user found
    if (!user) {
      router.push("/");
    }
  }, [user, router]);

  const { data: recommendations, isLoading: recLoading, error: recError } = useUserRecommendations(user?.tgid ?? null);
  const { data: balance, isLoading: balLoading, error: balError } = useUserBalance(user?.tgid ?? null);

  return (
    <main className="min-h-screen bg-[#130F30] p-4">
      {/* Background gradients */}
      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => router.push("/")}
            className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors"
            aria-label="Назад"
          >
            <FaArrowLeft className="text-white" />
          </button>
          <h1 className="text-white text-2xl font-bold">Мой профиль</h1>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {/* Profile Stats */}
          {recLoading ? (
            <LoadingSkeleton />
          ) : recError ? (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
              <p className="text-red-200">Ошибка загрузки статистики: {recError.message}</p>
            </div>
          ) : recommendations?.stats ? (
            <ProfileStats stats={recommendations.stats} />
          ) : (
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
              <p className="text-gray-400 text-center">Нет данных о статистике</p>
            </div>
          )}

          {/* Profile Recommendations */}
          {recLoading ? (
            <LoadingSkeleton />
          ) : recError ? (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
              <p className="text-red-200">Ошибка загрузки рекомендаций: {recError.message}</p>
            </div>
          ) : recommendations ? (
            <ProfileRecommendations recommendations={recommendations} />
          ) : (
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
              <p className="text-gray-400 text-center">Нет данных о рекомендациях</p>
            </div>
          )}

          {/* Profile Balance */}
          {balLoading ? (
            <LoadingSkeleton />
          ) : balError ? (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6">
              <p className="text-red-200">Ошибка загрузки баланса: {balError.message}</p>
            </div>
          ) : balance ? (
            <ProfileBalance balance={balance} />
          ) : (
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
              <p className="text-gray-400 text-center">Нет данных о балансе</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
