"use client";

import { useState } from "react";
import { FaWallet, FaEdit, FaTimes, FaCheck, FaSpinner } from "react-icons/fa";
import { User } from "@/lib/api/types";
import { useUsers, useUserBalance, useUpdateBalanceLimit } from "@/lib/api/hooks";

interface UserBalanceRowProps {
  user: User;
  onEdit: (user: User, currentLimit: number | null) => void;
}

function UserBalanceRow({ user, onEdit }: UserBalanceRowProps) {
  const { data: balance, isLoading } = useUserBalance(user.tgid);

  if (isLoading) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 animate-pulse">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="h-5 bg-white/10 rounded w-1/3"></div>
            <div className="h-4 bg-white/10 rounded w-1/4"></div>
          </div>
          <div className="flex gap-4">
            <div className="h-4 w-20 bg-white/10 rounded"></div>
            <div className="h-4 w-20 bg-white/10 rounded"></div>
            <div className="h-4 w-20 bg-white/10 rounded"></div>
            <div className="h-10 w-10 bg-white/10 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 transition-all duration-300 hover:bg-white/10">
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <p className="text-white font-semibold text-base truncate">
              {user.name}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-gray-400 text-sm">{user.office || "—"}</p>
            <p className="text-gray-500 text-xs">@{user.tgid}</p>
          </div>
        </div>

        <div className="flex items-center gap-4 flex-shrink-0">
          <div className="text-center min-w-[100px]">
            <p className="text-xs text-gray-400 mb-1">Лимит</p>
            <p className="text-white font-medium">
              {balance?.weekly_limit !== null && balance?.weekly_limit !== undefined
                ? `${Number(balance.weekly_limit).toFixed(2)} ₽`
                : "—"}
            </p>
          </div>
          <div className="text-center min-w-[100px]">
            <p className="text-xs text-gray-400 mb-1">Потрачено</p>
            <p className="text-white font-medium">
              {balance ? `${Number(balance.spent_this_week).toFixed(2)} ₽` : "—"}
            </p>
          </div>
          <div className="text-center min-w-[100px]">
            <p className="text-xs text-gray-400 mb-1">Остаток</p>
            <p className="text-white font-medium">
              {balance?.remaining !== null && balance?.remaining !== undefined
                ? `${Number(balance.remaining).toFixed(2)} ₽`
                : "—"}
            </p>
          </div>
          <button
            onClick={() => onEdit(user, balance?.weekly_limit ?? null)}
            className="p-2 rounded-lg bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white hover:opacity-90 transition-opacity"
            aria-label="Редактировать лимит"
          >
            <FaEdit size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BalanceManager() {
  const { data: users, isLoading, error } = useUsers();
  const { updateLimit } = useUpdateBalanceLimit();

  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [newLimit, setNewLimit] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  const handleEdit = (user: User, currentLimit: number | null) => {
    setEditingUser(user);
    setNewLimit(currentLimit !== null ? currentLimit.toString() : "");
  };

  const handleSave = async () => {
    if (!editingUser) return;

    const limitValue = newLimit.trim() === "" ? null : parseFloat(newLimit);

    if (limitValue !== null && (isNaN(limitValue) || limitValue < 0)) {
      alert("Введите корректное положительное число");
      return;
    }

    setIsSaving(true);
    try {
      await updateLimit(editingUser.tgid, limitValue);
      setEditingUser(null);
      setNewLimit("");
    } catch (error) {
      alert("Ошибка при обновлении лимита");
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveLimit = async () => {
    if (!editingUser) return;

    if (!confirm(`Снять лимит для пользователя ${editingUser.name}?`)) {
      return;
    }

    setIsSaving(true);
    try {
      await updateLimit(editingUser.tgid, null);
      setEditingUser(null);
      setNewLimit("");
    } catch (error) {
      alert("Ошибка при снятии лимита");
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditingUser(null);
    setNewLimit("");
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
              </div>
              <div className="flex gap-4">
                <div className="h-10 w-24 bg-white/10 rounded"></div>
                <div className="h-10 w-24 bg-white/10 rounded"></div>
                <div className="h-10 w-24 bg-white/10 rounded"></div>
                <div className="h-10 w-10 bg-white/10 rounded"></div>
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
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
          <FaWallet className="text-white text-lg" />
        </div>
        <h2 className="text-white text-xl font-bold">Управление балансами</h2>
      </div>

      {users.map((user) => (
        <UserBalanceRow key={user.tgid} user={user} onEdit={handleEdit} />
      ))}

      {editingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1535] rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
                <FaWallet className="text-white text-lg" />
              </div>
              <h3 className="text-white text-lg font-bold">Редактировать лимит</h3>
            </div>

            <div className="mb-4">
              <p className="text-gray-300 text-sm mb-1">Пользователь:</p>
              <p className="text-white font-semibold">{editingUser.name}</p>
              <p className="text-gray-400 text-sm">{editingUser.office}</p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Недельный лимит (₽)
              </label>
              <input
                type="number"
                value={newLimit}
                onChange={(e) => setNewLimit(e.target.value)}
                placeholder="Введите лимит или оставьте пустым"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
                min="0"
                step="0.01"
                disabled={isSaving}
              />
              <p className="text-xs text-gray-400 mt-1">
                Оставьте пустым для снятия лимита
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white px-4 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? (
                  <>
                    <FaSpinner className="animate-spin" />
                    <span>Сохранение...</span>
                  </>
                ) : (
                  <>
                    <FaCheck />
                    <span>Сохранить</span>
                  </>
                )}
              </button>
              <button
                onClick={handleRemoveLimit}
                disabled={isSaving}
                className="flex-1 flex items-center justify-center gap-2 bg-red-500/20 text-red-400 border border-red-500/30 px-4 py-3 rounded-lg font-medium hover:bg-red-500/30 hover:border-red-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaTimes />
                <span>Снять лимит</span>
              </button>
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="bg-white/10 text-white px-4 py-3 rounded-lg font-medium hover:bg-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaTimes />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
