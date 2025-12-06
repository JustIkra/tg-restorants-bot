"use client";

import React from "react";
import { FaChartLine } from "react-icons/fa6";
import type { OrderStats } from "@/lib/api/types";

interface ProfileStatsProps {
  stats: OrderStats;
}

const categoryLabels: { [key: string]: string } = {
  soup: "Супы",
  salad: "Салаты",
  main: "Основное",
  extra: "Дополнительно",
  side: "Гарниры",
  drink: "Напитки",
  dessert: "Десерты",
};

const ProfileStats: React.FC<ProfileStatsProps> = ({ stats }) => {
  // Empty state
  if (stats.orders_last_30_days === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
            <FaChartLine className="text-white text-lg" />
          </div>
          <h2 className="text-white text-xl font-bold">Статистика заказов</h2>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-400">Пока нет заказов</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
          <FaChartLine className="text-white text-lg" />
        </div>
        <h2 className="text-white text-xl font-bold">Статистика заказов</h2>
      </div>

      <div className="space-y-4">
        {/* Orders count */}
        <div className="bg-white/5 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Заказов за 30 дней</p>
          <p className="text-white text-2xl font-bold">
            {stats.orders_last_30_days}
          </p>
        </div>

        {/* Categories */}
        {Object.keys(stats.categories).length > 0 && (
          <div className="bg-white/5 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-3">Категории</p>
            <div className="space-y-2">
              {Object.entries(stats.categories).map(([category, data]) => (
                <div key={category} className="flex justify-between items-center">
                  <span className="text-white">
                    {categoryLabels[category] || category}
                  </span>
                  <span className="text-gray-400 text-sm">
                    {data.percent.toFixed(1)}% ({data.count}{" "}
                    {data.count === 1
                      ? "заказ"
                      : data.count < 5
                      ? "заказа"
                      : "заказов"}
                    )
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Unique dishes */}
        <div className="bg-white/5 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Уникальных блюд</p>
          <p className="text-white text-2xl font-bold">
            {stats.unique_dishes}
          </p>
        </div>

        {/* Favorite dishes */}
        {stats.favorite_dishes.length > 0 && (
          <div className="bg-white/5 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-3">Топ-5 любимых блюд</p>
            <div className="space-y-2">
              {stats.favorite_dishes.slice(0, 5).map((dish, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-white">
                    {index + 1}. {dish.name}
                  </span>
                  <span className="text-gray-400 text-sm">
                    {dish.count} {dish.count === 1 ? "раз" : "раза"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileStats;
