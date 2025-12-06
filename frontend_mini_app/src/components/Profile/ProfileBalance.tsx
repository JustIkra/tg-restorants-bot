"use client";

import React from "react";
import { FaWallet } from "react-icons/fa6";
import type { BalanceResponse } from "@/lib/api/types";

interface ProfileBalanceProps {
  balance: BalanceResponse;
}

const getProgressColor = (percent: number) => {
  if (percent < 70) return "bg-green-500";
  if (percent < 90) return "bg-yellow-500";
  return "bg-red-500";
};

const ProfileBalance: React.FC<ProfileBalanceProps> = ({ balance }) => {
  // Convert string Decimals from backend to numbers
  const weeklyLimit = balance.weekly_limit !== null ? Number(balance.weekly_limit) : null;
  const spentThisWeek = Number(balance.spent_this_week);
  const remaining = balance.remaining !== null ? Number(balance.remaining) : null;

  const percent =
    weeklyLimit !== null
      ? (spentThisWeek / weeklyLimit) * 100
      : 0;

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
          <FaWallet className="text-white text-lg" />
        </div>
        <h2 className="text-white text-xl font-bold">Корпоративный баланс</h2>
      </div>

      <div className="space-y-4">
        {/* Weekly limit */}
        <div className="bg-white/5 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Недельный лимит</p>
          <p className="text-white text-2xl font-bold">
            {weeklyLimit !== null
              ? `${weeklyLimit.toFixed(2)} ₽`
              : "Не установлен"}
          </p>
        </div>

        {/* Spent this week */}
        <div className="bg-white/5 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Потрачено</p>
          <p className="text-white text-2xl font-bold">
            {spentThisWeek.toFixed(2)} ₽
          </p>
        </div>

        {/* Remaining */}
        <div className="bg-white/5 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Остаток</p>
          <p className="text-white text-2xl font-bold">
            {remaining !== null
              ? `${remaining.toFixed(2)} ₽`
              : "—"}
          </p>
        </div>

        {/* Progress bar */}
        {weeklyLimit !== null && (
          <div className="bg-white/5 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <p className="text-gray-400 text-sm">Использовано</p>
              <p className="text-gray-400 text-sm">
                {Math.min(percent, 100).toFixed(1)}%
              </p>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${getProgressColor(
                  percent
                )}`}
                style={{ width: `${Math.min(percent, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileBalance;
