"use client";

import React, { useState, useEffect } from "react";
import {
  useCafes,
  useDeadlineSchedule,
  useUpdateDeadlineSchedule,
} from "@/lib/api/hooks";
import type { DeadlineItem } from "@/lib/api/types";

const WEEKDAY_NAMES = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
  "Воскресенье",
];

const DeadlineSchedule: React.FC = () => {
  const { data: cafes } = useCafes(true, false); // Get all cafes
  const [selectedCafeId, setSelectedCafeId] = useState<number | null>(null);
  const { data: scheduleData, isLoading } = useDeadlineSchedule(selectedCafeId);
  const { updateSchedule, isLoading: isUpdating } = useUpdateDeadlineSchedule();

  const [formData, setFormData] = useState<DeadlineItem[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initialize form data when schedule loads
  useEffect(() => {
    if (scheduleData?.schedule) {
      setFormData(scheduleData.schedule);
    } else if (selectedCafeId) {
      // Initialize with default schedule if no schedule exists
      setFormData(
        Array.from({ length: 7 }, (_, i) => ({
          weekday: i,
          deadline_time: "10:00",
          is_enabled: false,
          advance_days: 0,
        }))
      );
    }
  }, [scheduleData, selectedCafeId]);

  const handleCafeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const cafeId = e.target.value ? parseInt(e.target.value) : null;
    setSelectedCafeId(cafeId);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  const handleFieldChange = (
    weekday: number,
    field: keyof DeadlineItem,
    value: string | boolean | number
  ) => {
    setFormData((prev) =>
      prev.map((item) =>
        item.weekday === weekday ? { ...item, [field]: value } : item
      )
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);

    if (!selectedCafeId) {
      setErrorMessage("Пожалуйста, выберите кафе");
      return;
    }

    try {
      await updateSchedule(selectedCafeId, formData);
      setSuccessMessage("Расписание успешно обновлено");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error("Failed to update schedule:", err);
      setErrorMessage(
        err instanceof Error ? err.message : "Не удалось обновить расписание"
      );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Расписание дедлайнов</h2>
      </div>

      {/* Cafe selector */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Выберите кафе
        </label>
        <select
          value={selectedCafeId || ""}
          onChange={handleCafeChange}
          className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
          disabled={isUpdating}
        >
          <option value="" className="bg-[#130F30]">
            -- Выберите кафе --
          </option>
          {cafes?.map((cafe) => (
            <option key={cafe.id} value={cafe.id} className="bg-[#130F30]">
              {cafe.name}
            </option>
          ))}
        </select>
      </div>

      {/* Loading state */}
      {isLoading && selectedCafeId && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
          <div className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="text-gray-400">Загрузка...</span>
          </div>
        </div>
      )}

      {/* Schedule form */}
      {!isLoading && selectedCafeId && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
            <h3 className="text-white font-semibold text-lg mb-4">
              Настройка расписания
            </h3>

            <div className="space-y-4">
              {formData.map((item) => (
                <div
                  key={item.weekday}
                  className="bg-white/10 border border-white/20 rounded-lg p-4"
                >
                  <div className="flex items-center gap-4 mb-3">
                    <input
                      type="checkbox"
                      id={`enabled-${item.weekday}`}
                      checked={item.is_enabled}
                      onChange={(e) =>
                        handleFieldChange(
                          item.weekday,
                          "is_enabled",
                          e.target.checked
                        )
                      }
                      className="w-5 h-5 rounded bg-white/10 border-white/20 text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
                      disabled={isUpdating}
                    />
                    <label
                      htmlFor={`enabled-${item.weekday}`}
                      className="text-white font-medium flex-1"
                    >
                      {WEEKDAY_NAMES[item.weekday]}
                    </label>
                  </div>

                  {item.is_enabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 pl-9">
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">
                          Время дедлайна
                        </label>
                        <input
                          type="time"
                          value={item.deadline_time}
                          onChange={(e) =>
                            handleFieldChange(
                              item.weekday,
                              "deadline_time",
                              e.target.value
                            )
                          }
                          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                          disabled={isUpdating}
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">
                          Дней заранее
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="6"
                          value={item.advance_days}
                          onChange={(e) =>
                            handleFieldChange(
                              item.weekday,
                              "advance_days",
                              parseInt(e.target.value) || 0
                            )
                          }
                          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                          disabled={isUpdating}
                        />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Success message */}
          {successMessage && (
            <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-3">
              <p className="text-green-400 text-sm">{successMessage}</p>
            </div>
          )}

          {/* Error message */}
          {errorMessage && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3">
              <p className="text-red-400 text-sm">{errorMessage}</p>
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={isUpdating}
            className="w-full px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUpdating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Сохранение...
              </span>
            ) : (
              "Сохранить расписание"
            )}
          </button>
        </form>
      )}

      {/* No cafe selected */}
      {!selectedCafeId && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
          <p className="text-gray-400">Выберите кафе для настройки расписания</p>
        </div>
      )}
    </div>
  );
};

export default DeadlineSchedule;
