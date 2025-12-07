"use client";

import React from "react";
import type { UserAccessRequest } from "@/lib/api/types";

interface UserRequestCardProps {
  request: UserAccessRequest;
  onApprove: (requestId: number) => Promise<void>;
  onReject: (requestId: number) => Promise<void>;
  isProcessing: boolean;
}

const UserRequestCard: React.FC<UserRequestCardProps> = ({
  request,
  onApprove,
  onReject,
  isProcessing,
}) => {
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

  const isPending = request.status === "pending";

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 transition-all duration-300 hover:bg-white/10">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-white font-semibold text-base truncate">
              {request.name}
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
            {request.username ? `@${request.username}` : `ID: ${request.tgid}`}
          </p>
          <p className="text-gray-400 text-sm">Офис: {request.office}</p>
          <p className="text-gray-500 text-xs mt-1">
            Запрос: {formatDate(request.created_at)}
          </p>
          {request.processed_at && (
            <p className="text-gray-500 text-xs">
              Обработан: {formatDate(request.processed_at)}
            </p>
          )}
        </div>

        {isPending && (
          <div className="flex flex-col sm:flex-row gap-2 flex-shrink-0">
            <button
              onClick={() => onApprove(request.id)}
              disabled={isProcessing}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 hover:border-green-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
            >
              {isProcessing ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
              onClick={() => onReject(request.id)}
              disabled={isProcessing}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 hover:border-red-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
            >
              {isProcessing ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
};

export default UserRequestCard;
