"use client";

import React, { useState, useEffect, useRef } from "react";
import { FaLightbulb, FaEllipsisVertical } from "react-icons/fa6";
import type { RecommendationsResponse } from "@/lib/api/types";
import { useGenerateRecommendations } from "@/lib/api/hooks";

interface ProfileRecommendationsProps {
  recommendations: RecommendationsResponse;
  tgid: number;
}

const ProfileRecommendations: React.FC<ProfileRecommendationsProps> = ({
  recommendations,
  tgid,
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { generateRecommendations, isLoading, error } = useGenerateRecommendations();

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showDropdown]);

  // Handle generate recommendations
  const handleGenerateClick = async () => {
    try {
      await generateRecommendations(tgid);
      setShowDropdown(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Не удалось сгенерировать рекомендации";
      alert(errorMessage);
    }
  };

  // Format date
  const formatDate = (isoString: string | null) => {
    if (!isoString) return null;
    return new Date(isoString).toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // Empty state
  if (recommendations.summary === null) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
        <div className="relative">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
                <FaLightbulb className="text-white text-lg" />
              </div>
              <h2 className="text-white text-xl font-bold">AI-рекомендации</h2>
            </div>

            {/* Three dots menu */}
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="p-2 rounded-lg hover:bg-white/10 transition"
            >
              <FaEllipsisVertical className="text-white/70 text-lg" />
            </button>
          </div>

          {/* Dropdown menu */}
          {showDropdown && (
            <div
              ref={dropdownRef}
              className="absolute right-0 top-12 z-20 w-48 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl overflow-hidden"
            >
              <button
                onClick={handleGenerateClick}
                disabled={isLoading}
                className="w-full p-3 text-left text-white hover:bg-white/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Генерация..." : "Получить сейчас"}
              </button>
            </div>
          )}
        </div>

        <div className="text-center py-8">
          <p className="text-gray-400">
            Сделайте минимум 5 заказов для получения рекомендаций
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
      <div className="relative">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
              <FaLightbulb className="text-white text-lg" />
            </div>
            <h2 className="text-white text-xl font-bold">AI-рекомендации</h2>
          </div>

          {/* Three dots menu */}
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="p-2 rounded-lg hover:bg-white/10 transition"
          >
            <FaEllipsisVertical className="text-white/70 text-lg" />
          </button>
        </div>

        {/* Dropdown menu */}
        {showDropdown && (
          <div
            ref={dropdownRef}
            className="absolute right-0 top-12 z-20 w-48 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl overflow-hidden"
          >
            <button
              onClick={handleGenerateClick}
              disabled={isLoading}
              className="w-full p-3 text-left text-white hover:bg-white/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Генерация..." : "Получить сейчас"}
            </button>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {/* Summary */}
        {recommendations.summary && (
          <div className="bg-white/5 rounded-lg p-4">
            <p className="text-white leading-relaxed">
              {recommendations.summary}
            </p>
          </div>
        )}

        {/* Tips */}
        {recommendations.tips.length > 0 && (
          <div className="bg-white/5 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-3">Советы</p>
            <ul className="space-y-2 list-disc list-inside">
              {recommendations.tips.map((tip, index) => (
                <li key={index} className="text-white leading-relaxed">
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Generated date */}
        {recommendations.generated_at && (
          <div className="text-gray-400 text-sm text-right">
            Сгенерировано: {formatDate(recommendations.generated_at)}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileRecommendations;
