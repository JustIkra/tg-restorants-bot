"use client";

import React, { useState, useEffect } from "react";
import type { User } from "@/lib/api/types";

interface UserEditModalProps {
  user: User;
  onSubmit: (data: { name?: string; office?: string; role?: "user" | "manager" }) => Promise<void>;
  onClose: () => void;
}

interface FormData {
  name: string;
  office: string;
  role: "user" | "manager";
}

const UserEditModal: React.FC<UserEditModalProps> = ({ user, onSubmit, onClose }) => {
  const [formData, setFormData] = useState<FormData>({
    name: user.name,
    office: user.office,
    role: user.role,
  });
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  const validate = (): boolean => {
    const newErrors: Partial<FormData> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Имя обязательно";
    } else if (formData.name.trim().length < 2) {
      newErrors.name = "Имя должно содержать минимум 2 символа";
    }

    if (!formData.office.trim()) {
      newErrors.office = "Офис обязателен";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Only send changed fields
      const updates: { name?: string; office?: string; role?: "user" | "manager" } = {};

      if (formData.name.trim() !== user.name) {
        updates.name = formData.name.trim();
      }
      if (formData.office.trim() !== user.office) {
        updates.office = formData.office.trim();
      }
      if (formData.role !== user.role) {
        updates.role = formData.role;
      }

      if (Object.keys(updates).length === 0) {
        // No changes
        onClose();
        return;
      }

      await onSubmit(updates);
      onClose();
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Не удалось обновить пользователя"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-[#130F30] border border-white/10 rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-xl font-bold text-white">Редактировать пользователя</h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Submit Error */}
          {submitError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <p className="text-red-400 text-sm">{submitError}</p>
            </div>
          )}

          {/* Telegram ID (read-only) */}
          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Telegram ID
            </label>
            <input
              type="text"
              value={user.tgid}
              disabled
              className="w-full bg-white/5 border border-white/10 text-gray-400 rounded-lg px-4 py-2 cursor-not-allowed"
            />
          </div>

          {/* Name Field */}
          <div>
            <label htmlFor="name" className="block text-white text-sm font-medium mb-2">
              Имя <span className="text-red-400">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={handleChange("name")}
              disabled={isSubmitting}
              placeholder="Введите имя пользователя"
              className={`w-full bg-white/10 border ${
                errors.name ? "border-red-500/50" : "border-white/20"
              } text-white rounded-lg px-4 py-2 focus:outline-none focus:border-[#A020F0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
            />
            {errors.name && (
              <p className="text-red-400 text-xs mt-1">{errors.name}</p>
            )}
          </div>

          {/* Office Field */}
          <div>
            <label htmlFor="office" className="block text-white text-sm font-medium mb-2">
              Офис <span className="text-red-400">*</span>
            </label>
            <input
              id="office"
              type="text"
              value={formData.office}
              onChange={handleChange("office")}
              disabled={isSubmitting}
              placeholder="Введите офис"
              className={`w-full bg-white/10 border ${
                errors.office ? "border-red-500/50" : "border-white/20"
              } text-white rounded-lg px-4 py-2 focus:outline-none focus:border-[#A020F0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
            />
            {errors.office && (
              <p className="text-red-400 text-xs mt-1">{errors.office}</p>
            )}
          </div>

          {/* Role Field */}
          <div>
            <label htmlFor="role" className="block text-white text-sm font-medium mb-2">
              Роль <span className="text-red-400">*</span>
            </label>
            <select
              id="role"
              value={formData.role}
              onChange={handleChange("role")}
              disabled={isSubmitting}
              className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:border-[#A020F0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="user" className="bg-[#130F30]">Сотрудник</option>
              <option value="manager" className="bg-[#130F30]">Менеджер</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-medium py-3 px-6 rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
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
                "Сохранить"
              )}
            </button>

            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-6 py-3 bg-white/10 text-white rounded-lg border border-white/20 hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserEditModal;
