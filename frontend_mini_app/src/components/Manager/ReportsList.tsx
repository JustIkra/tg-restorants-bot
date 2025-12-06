"use client";

import React, { useState } from "react";
import {
  useSummaries,
  useCreateSummary,
  useDeleteSummary,
  useCafes,
} from "@/lib/api/hooks";
import { mutate } from "swr";

const ReportsList: React.FC = () => {
  const { data: summaries, error, isLoading } = useSummaries();
  const { data: cafes } = useCafes(false); // Get all cafes, not just active
  const { createSummary } = useCreateSummary();
  const { deleteSummary } = useDeleteSummary();

  const [processingId, setProcessingId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    cafeId: "",
    date: "",
  });
  const [formError, setFormError] = useState<string | null>(null);

  const handleDelete = async (summaryId: number) => {
    if (!confirm("Вы уверены, что хотите удалить этот отчёт?")) {
      return;
    }

    setProcessingId(summaryId);
    try {
      await deleteSummary(summaryId);
      // Revalidate summaries list
      mutate("/summaries");
    } catch (err) {
      console.error("Failed to delete summary:", err);
      alert(
        `Ошибка: ${err instanceof Error ? err.message : "Не удалось удалить отчёт"}`
      );
    } finally {
      setProcessingId(null);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.cafeId || !formData.date) {
      setFormError("Пожалуйста, заполните все поля");
      return;
    }

    setProcessingId(-1); // Use -1 to indicate form processing
    try {
      await createSummary(parseInt(formData.cafeId), formData.date);
      // Revalidate summaries list
      mutate("/summaries");
      // Reset form
      setFormData({ cafeId: "", date: "" });
      setShowCreateForm(false);
    } catch (err) {
      console.error("Failed to create summary:", err);
      setFormError(
        err instanceof Error ? err.message : "Не удалось создать отчёт"
      );
    } finally {
      setProcessingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">Отчёты</h2>
          <div className="h-10 w-40 bg-white/10 rounded animate-pulse"></div>
        </div>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 animate-pulse"
          >
            <div className="flex justify-between items-center gap-4">
              <div className="space-y-2 flex-1">
                <div className="h-5 bg-white/10 rounded w-1/3"></div>
                <div className="h-4 bg-white/10 rounded w-1/4"></div>
              </div>
              <div className="h-10 w-24 bg-white/10 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">Отчёты</h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white text-sm font-medium rounded-lg hover:opacity-90 transition"
          >
            {showCreateForm ? "Отмена" : "Создать отчёт"}
          </button>
        </div>
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <p className="text-red-400 text-sm">
            Ошибка загрузки отчётов: {error.message}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Отчёты</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white text-sm font-medium rounded-lg hover:opacity-90 transition"
        >
          {showCreateForm ? "Отмена" : "Создать отчёт"}
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6 mb-6">
          <h3 className="text-white font-semibold text-lg mb-4">
            Создать новый отчёт
          </h3>
          <form onSubmit={handleCreateSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Кафе
              </label>
              <select
                value={formData.cafeId}
                onChange={(e) =>
                  setFormData({ ...formData, cafeId: e.target.value })
                }
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                disabled={processingId === -1}
              >
                <option value="" className="bg-[#130F30]">
                  Выберите кафе
                </option>
                {cafes?.map((cafe) => (
                  <option
                    key={cafe.id}
                    value={cafe.id}
                    className="bg-[#130F30]"
                  >
                    {cafe.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Дата
              </label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) =>
                  setFormData({ ...formData, date: e.target.value })
                }
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                disabled={processingId === -1}
              />
            </div>

            {formError && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <p className="text-red-400 text-sm">{formError}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={processingId === -1}
              className="w-full px-4 py-3 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {processingId === -1 ? (
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
                  Создание...
                </span>
              ) : (
                "Создать отчёт"
              )}
            </button>
          </form>
        </div>
      )}

      {!summaries || summaries.length === 0 ? (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
          <p className="text-gray-400">Нет отчётов</p>
        </div>
      ) : (
        <div className="space-y-4">
          {summaries.map((summary) => {
            const isProcessing = processingId === summary.id;

            return (
              <div
                key={summary.id}
                className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 transition-all duration-300 hover:bg-white/10"
              >
                <div className="flex justify-between items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-white font-semibold text-base truncate">
                        {summary.cafe_name}
                      </h3>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium flex-shrink-0 ${
                          summary.status === "pending"
                            ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                            : "bg-green-500/20 text-green-400 border border-green-500/30"
                        }`}
                      >
                        {summary.status === "pending" ? "В обработке" : "Готово"}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm mb-1">
                      Дата отчёта: {formatDate(summary.date)}
                    </p>
                    <p className="text-gray-400 text-xs">
                      Создан: {formatDateTime(summary.created_at)}
                    </p>
                  </div>

                  <button
                    onClick={() => handleDelete(summary.id)}
                    disabled={isProcessing}
                    className="px-4 py-2 rounded-lg text-sm font-medium bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 hover:border-red-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px] flex-shrink-0"
                  >
                    {isProcessing ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg
                          className="animate-spin h-4 w-4"
                          viewBox="0 0 24 24"
                        >
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
                        ...
                      </span>
                    ) : (
                      "Удалить"
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ReportsList;
