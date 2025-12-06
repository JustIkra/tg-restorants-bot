"use client";

import React from "react";
import { FaLightbulb } from "react-icons/fa6";
import type { RecommendationsResponse } from "@/lib/api/types";

interface ProfileRecommendationsProps {
  recommendations: RecommendationsResponse;
}

const ProfileRecommendations: React.FC<ProfileRecommendationsProps> = ({
  recommendations,
}) => {
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
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
            <FaLightbulb className="text-white text-lg" />
          </div>
          <h2 className="text-white text-xl font-bold">AI-рекомендации</h2>
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
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
          <FaLightbulb className="text-white text-lg" />
        </div>
        <h2 className="text-white text-xl font-bold">AI-рекомендации</h2>
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
