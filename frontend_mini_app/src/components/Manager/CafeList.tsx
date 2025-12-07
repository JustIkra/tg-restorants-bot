"use client";

import React, { useState } from "react";
import { useCafes } from "@/lib/api/hooks";
import type { Cafe } from "@/lib/api/types";
import { apiRequest } from "@/lib/api/client";
import { mutate } from "swr";
import { useConfirm } from "@/hooks/useConfirm";

interface CafeListProps {
  onEdit?: (cafe: Cafe) => void;
  shouldFetch?: boolean;
}

const CafeList: React.FC<CafeListProps> = ({ onEdit, shouldFetch = true }) => {
  const { data: cafes, error, isLoading } = useCafes(shouldFetch, false); // Get all cafes, not just active
  const [processingId, setProcessingId] = useState<number | null>(null);
  const { confirm } = useConfirm();

  const handleToggleStatus = async (cafe: Cafe) => {
    setProcessingId(cafe.id);
    try {
      await apiRequest(`/cafes/${cafe.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !cafe.is_active }),
      });
      // Revalidate cafes list
      mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
    } catch (err) {
      console.error("Failed to toggle cafe status:", err);
      alert(`Ошибка: ${err instanceof Error ? err.message : "Не удалось изменить статус"}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleDelete = async (cafe: Cafe) => {
    const confirmed = await confirm({
      title: "Удаление кафе",
      message: `Вы уверены, что хотите удалить кафе "${cafe.name}"?`,
      confirmText: "Удалить",
      cancelText: "Отмена",
    });

    if (!confirmed) {
      return;
    }

    setProcessingId(cafe.id);
    try {
      await apiRequest(`/cafes/${cafe.id}`, {
        method: "DELETE",
      });
      // Revalidate cafes list
      mutate((key: string) => typeof key === "string" && key.startsWith("/cafes"));
    } catch (err) {
      console.error("Failed to delete cafe:", err);
      alert(`Ошибка: ${err instanceof Error ? err.message : "Не удалось удалить кафе"}`);
    } finally {
      setProcessingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-white text-center">
          <div className="animate-pulse">Загрузка кафе...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
        <p className="text-red-400">Ошибка загрузки: {error.message}</p>
      </div>
    );
  }

  if (!cafes || cafes.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
        <p className="text-gray-400 text-center">Кафе не найдены</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {cafes.map((cafe) => (
        <div
          key={cafe.id}
          className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 transition-all hover:bg-white/10"
        >
          <div className="flex justify-between items-start gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-white font-semibold text-lg">{cafe.name}</h3>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    cafe.is_active
                      ? "bg-green-500/20 text-green-400"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {cafe.is_active ? "Активно" : "Неактивно"}
                </span>
              </div>
              {cafe.description && (
                <p className="text-gray-300 text-sm mb-2">{cafe.description}</p>
              )}
              <p className="text-gray-400 text-xs">ID: {cafe.id}</p>
            </div>

            <div className="flex flex-col gap-2 flex-shrink-0">
              {onEdit && (
                <button
                  onClick={() => onEdit(cafe)}
                  disabled={processingId === cafe.id}
                  className="px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white text-sm font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50"
                >
                  Редактировать
                </button>
              )}
              <button
                onClick={() => handleToggleStatus(cafe)}
                disabled={processingId === cafe.id}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition disabled:opacity-50 ${
                  cafe.is_active
                    ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/30"
                    : "bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30"
                }`}
              >
                {processingId === cafe.id
                  ? "..."
                  : cafe.is_active
                  ? "Деактивировать"
                  : "Активировать"}
              </button>
              <button
                onClick={() => handleDelete(cafe)}
                disabled={processingId === cafe.id}
                className="px-4 py-2 bg-red-500/20 text-red-400 text-sm font-medium border border-red-500/30 rounded-lg hover:bg-red-500/30 transition disabled:opacity-50"
              >
                {processingId === cafe.id ? "..." : "Удалить"}
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default CafeList;
