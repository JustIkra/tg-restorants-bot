"use client";

import React from "react";
import type { User } from "@/lib/api/types";
import { useConfirm } from "@/hooks/useConfirm";

interface UserListProps {
  users: User[] | undefined;
  isLoading: boolean;
  error: Error | undefined;
  onToggleAccess: (tgid: number, newStatus: boolean) => Promise<void>;
  onEdit: (user: User) => void;
  onDelete: (tgid: number) => Promise<void>;
}

const UserList: React.FC<UserListProps> = ({
  users,
  isLoading,
  error,
  onToggleAccess,
  onEdit,
  onDelete,
}) => {
  const { confirm } = useConfirm();
  const [actionLoading, setActionLoading] = React.useState<{
    [key: number]: "toggle" | "delete" | null;
  }>({});

  const handleToggleAccess = async (tgid: number, currentStatus: boolean) => {
    setActionLoading((prev) => ({ ...prev, [tgid]: "toggle" }));
    try {
      await onToggleAccess(tgid, !currentStatus);
    } finally {
      setActionLoading((prev) => ({ ...prev, [tgid]: null }));
    }
  };

  const handleDelete = async (tgid: number) => {
    const confirmed = await confirm({
      title: "Удаление пользователя",
      message: "Вы уверены, что хотите удалить этого пользователя?",
      confirmText: "Удалить",
      cancelText: "Отмена",
    });

    if (!confirmed) {
      return;
    }

    setActionLoading((prev) => ({ ...prev, [tgid]: "delete" }));
    try {
      await onDelete(tgid);
    } finally {
      setActionLoading((prev) => ({ ...prev, [tgid]: null }));
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
            <div className="flex justify-between items-center">
              <div className="space-y-2 flex-1">
                <div className="h-5 bg-white/10 rounded w-1/3"></div>
                <div className="h-4 bg-white/10 rounded w-1/4"></div>
                <div className="h-4 bg-white/10 rounded w-1/5"></div>
              </div>
              <div className="flex gap-2">
                <div className="h-10 w-28 bg-white/10 rounded"></div>
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
          Ошибка загрузки пользователей: {error.message}
        </p>
      </div>
    );
  }

  if (!users || users.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-8 text-center">
        <p className="text-gray-400">Нет пользователей</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {users.map((user) => {
        const loading = actionLoading[user.tgid];
        return (
          <div
            key={user.tgid}
            className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 transition-all duration-300 hover:bg-white/10"
          >
            <div className="flex justify-between items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <p className="text-white font-semibold text-base truncate">
                    {user.name}
                  </p>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                      user.is_active
                        ? "bg-green-500/20 text-green-400 border border-green-500/30"
                        : "bg-red-500/20 text-red-400 border border-red-500/30"
                    }`}
                  >
                    {user.is_active ? "Активен" : "Заблокирован"}
                  </span>
                </div>
                <p className="text-gray-400 text-sm">@{user.tgid}</p>
                <p className="text-gray-400 text-sm">{user.office}</p>
                <p className="text-gray-500 text-xs mt-1">
                  Роль: {user.role === "manager" ? "Менеджер" : "Сотрудник"}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 flex-shrink-0">
                <button
                  onClick={() => onEdit(user)}
                  disabled={!!loading}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-500/40 text-blue-300 border border-blue-500/50 hover:bg-blue-500/60 hover:border-blue-500/70 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
                >
                  Изменить
                </button>

                <button
                  onClick={() => handleToggleAccess(user.tgid, user.is_active)}
                  disabled={!!loading}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 min-w-[120px] ${
                    user.is_active
                      ? "bg-red-500/40 text-red-300 border border-red-500/50 hover:bg-red-500/60 hover:border-red-500/70"
                      : "bg-green-500/40 text-green-300 border border-green-500/50 hover:bg-green-500/60 hover:border-green-500/70"
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {loading === "toggle" ? (
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
                  ) : user.is_active ? (
                    "Заблокировать"
                  ) : (
                    "Разблокировать"
                  )}
                </button>

                <button
                  onClick={() => handleDelete(user.tgid)}
                  disabled={!!loading}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-red-500/40 text-red-300 border border-red-500/50 hover:bg-red-500/60 hover:border-red-500/70 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
                >
                  {loading === "delete" ? (
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
          </div>
        );
      })}
    </div>
  );
};

export default UserList;
