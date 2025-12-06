"use client";

import React, { useState } from "react";
import {
  useCafeRequests,
  useApproveCafeRequest,
  useRejectCafeRequest,
} from "@/lib/api/hooks";
import { mutate } from "swr";

const RequestsList: React.FC = () => {
  const { data: requests, error, isLoading } = useCafeRequests();
  const { approveRequest } = useApproveCafeRequest();
  const { rejectRequest } = useRejectCafeRequest();
  const [processingId, setProcessingId] = useState<number | null>(null);

  const handleApprove = async (requestId: number) => {
    setProcessingId(requestId);
    try {
      await approveRequest(requestId);
      // Revalidate cafe requests list
      mutate("/cafe-requests");
    } catch (err) {
      console.error("Failed to approve request:", err);
      alert(
        `Ошибка: ${err instanceof Error ? err.message : "Не удалось одобрить запрос"}`
      );
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (requestId: number) => {
    if (!confirm("Вы уверены, что хотите отклонить этот запрос?")) {
      return;
    }

    setProcessingId(requestId);
    try {
      await rejectRequest(requestId);
      // Revalidate cafe requests list
      mutate("/cafe-requests");
    } catch (err) {
      console.error("Failed to reject request:", err);
      alert(
        `Ошибка: ${err instanceof Error ? err.message : "Не удалось отклонить запрос"}`
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
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
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
              <div className="flex gap-2">
                <div className="h-10 w-24 bg-white/10 rounded"></div>
                <div className="h-10 w-24 bg-white/10 rounded"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
        <p className="text-red-400 text-sm">
          Ошибка загрузки запросов: {error.message}
        </p>
      </div>
    );
  }

  if (!requests || requests.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
        <p className="text-gray-400">Нет запросов</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {requests.map((request) => {
        const isPending = request.status === "pending";
        const isProcessing = processingId === request.id;

        return (
          <div
            key={request.id}
            className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 transition-all duration-300 hover:bg-white/10"
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-white font-semibold text-base truncate">
                    {request.cafe_name}
                  </h3>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium flex-shrink-0 ${
                      request.status === "pending"
                        ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                        : request.status === "approved"
                        ? "bg-green-500/20 text-green-400 border border-green-500/30"
                        : "bg-red-500/20 text-red-400 border border-red-500/30"
                    }`}
                  >
                    {request.status === "pending"
                      ? "Ожидает"
                      : request.status === "approved"
                      ? "Одобрено"
                      : "Отклонено"}
                  </span>
                </div>
                <p className="text-gray-400 text-sm">
                  Дата запроса: {formatDate(request.created_at)}
                </p>
              </div>

              {isPending && (
                <div className="flex flex-col sm:flex-row gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleApprove(request.id)}
                    disabled={isProcessing}
                    className="px-4 py-2 rounded-lg text-sm font-medium bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 hover:border-green-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
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
                      "Одобрить"
                    )}
                  </button>

                  <button
                    onClick={() => handleReject(request.id)}
                    disabled={isProcessing}
                    className="px-4 py-2 rounded-lg text-sm font-medium bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 hover:border-red-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
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
                      "Отклонить"
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RequestsList;
