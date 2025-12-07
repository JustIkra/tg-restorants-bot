"use client";

import React, { useState } from "react";
import {
  useUserRequests,
  useApproveRequest,
  useRejectRequest,
} from "@/lib/api/hooks";
import UserRequestCard from "./UserRequestCard";
import type { UserAccessRequestStatus } from "@/lib/api/types";
import { useConfirm } from "@/hooks/useConfirm";

const UserRequestsList: React.FC = () => {
  const { confirm } = useConfirm();
  const [statusFilter, setStatusFilter] = useState<UserAccessRequestStatus | "all">("pending");
  const { data: requests, error, isLoading } = useUserRequests(
    statusFilter === "all" ? undefined : statusFilter
  );
  const { approveRequest } = useApproveRequest();
  const { rejectRequest } = useRejectRequest();
  const [processingId, setProcessingId] = useState<number | null>(null);

  const handleApprove = async (requestId: number) => {
    setProcessingId(requestId);
    try {
      await approveRequest(requestId);
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
    const confirmed = await confirm({
      title: "Отклонение запроса",
      message: "Вы уверены, что хотите отклонить этот запрос?",
      confirmText: "Отклонить",
      cancelText: "Отмена",
    });

    if (!confirmed) {
      return;
    }

    setProcessingId(requestId);
    try {
      await rejectRequest(requestId);
    } catch (err) {
      console.error("Failed to reject request:", err);
      alert(
        `Ошибка: ${err instanceof Error ? err.message : "Не удалось отклонить запрос"}`
      );
    } finally {
      setProcessingId(null);
    }
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

  return (
    <div className="space-y-6">
      {/* Status Filter */}
      <div className="flex gap-2 flex-wrap">
        {[
          { value: "all", label: "Все" },
          { value: "pending", label: "Ожидают" },
          { value: "approved", label: "Одобрено" },
          { value: "rejected", label: "Отклонено" },
        ].map((filter) => (
          <button
            key={filter.value}
            onClick={() => setStatusFilter(filter.value as UserAccessRequestStatus | "all")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              statusFilter === filter.value
                ? "bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/10"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Requests List */}
      {!requests || requests.length === 0 ? (
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
          <p className="text-gray-400">
            {statusFilter === "all"
              ? "Нет запросов на доступ"
              : `Нет запросов со статусом "${statusFilter}"`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((request) => (
            <UserRequestCard
              key={request.id}
              request={request}
              onApprove={handleApprove}
              onReject={handleReject}
              isProcessing={processingId === request.id}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default UserRequestsList;
