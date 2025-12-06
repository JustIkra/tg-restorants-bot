"use client";

import React, { useState } from "react";

interface UserFormData {
  tgid: string;
  name: string;
  office: string;
}

interface UserFormProps {
  onSubmit: (data: { tgid: number; name: string; office: string }) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
}

const UserForm: React.FC<UserFormProps> = ({ onSubmit, onCancel, isLoading = false }) => {
  const [formData, setFormData] = useState<UserFormData>({
    tgid: "",
    name: "",
    office: "",
  });

  const [errors, setErrors] = useState<Partial<UserFormData>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = (): boolean => {
    const newErrors: Partial<UserFormData> = {};

    if (!formData.tgid.trim()) {
      newErrors.tgid = "Telegram ID обязателен";
    } else if (!/^\d+$/.test(formData.tgid)) {
      newErrors.tgid = "Telegram ID должен быть числом";
    }

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
      await onSubmit({
        tgid: parseInt(formData.tgid, 10),
        name: formData.name.trim(),
        office: formData.office.trim(),
      });

      // Reset form on success
      setFormData({ tgid: "", name: "", office: "" });
      setErrors({});
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Не удалось создать пользователя"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof UserFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Submit Error */}
      {submitError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <p className="text-red-400 text-sm">{submitError}</p>
        </div>
      )}

      {/* Telegram ID Field */}
      <div>
        <label htmlFor="tgid" className="block text-white text-sm font-medium mb-2">
          Telegram ID <span className="text-red-400">*</span>
        </label>
        <input
          id="tgid"
          type="text"
          value={formData.tgid}
          onChange={handleChange("tgid")}
          disabled={isSubmitting || isLoading}
          placeholder="Введите Telegram ID"
          className={`w-full bg-white/10 border ${
            errors.tgid ? "border-red-500/50" : "border-white/20"
          } text-white rounded-lg px-4 py-2 focus:outline-none focus:border-[#A020F0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
        />
        {errors.tgid && (
          <p className="text-red-400 text-xs mt-1">{errors.tgid}</p>
        )}
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
          disabled={isSubmitting || isLoading}
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
          disabled={isSubmitting || isLoading}
          placeholder="Введите офис (например, Москва)"
          className={`w-full bg-white/10 border ${
            errors.office ? "border-red-500/50" : "border-white/20"
          } text-white rounded-lg px-4 py-2 focus:outline-none focus:border-[#A020F0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
        />
        {errors.office && (
          <p className="text-red-400 text-xs mt-1">{errors.office}</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isSubmitting || isLoading}
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
              Создание...
            </span>
          ) : (
            "Создать пользователя"
          )}
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting || isLoading}
            className="px-6 py-3 bg-white/10 text-white rounded-lg border border-white/20 hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Отмена
          </button>
        )}
      </div>
    </form>
  );
};

export default UserForm;
