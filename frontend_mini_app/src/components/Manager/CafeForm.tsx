"use client";

import React, { useState, useEffect } from "react";
import type { Cafe } from "@/lib/api/types";
import { apiRequest } from "@/lib/api/client";
import { mutate } from "swr";

interface CafeFormProps {
  mode: "create" | "edit";
  initialData?: Cafe;
  onSubmit?: () => void;
  onCancel?: () => void;
}

const CafeForm: React.FC<CafeFormProps> = ({
  mode,
  initialData,
  onSubmit,
  onCancel,
}) => {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialData) {
      setName(initialData.name);
      setDescription(initialData.description || "");
    }
  }, [initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!name.trim()) {
      setError("Название кафе обязательно");
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        name: name.trim(),
        description: description.trim() || null,
      };

      if (mode === "create") {
        await apiRequest("/cafes", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      } else if (mode === "edit" && initialData) {
        await apiRequest(`/cafes/${initialData.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      }

      // Revalidate cafes list
      mutate("/cafes");

      // Reset form
      setName("");
      setDescription("");

      // Call onSubmit callback
      if (onSubmit) {
        onSubmit();
      }
    } catch (err) {
      console.error("Failed to save cafe:", err);
      setError(err instanceof Error ? err.message : "Не удалось сохранить кафе");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelClick = () => {
    setName("");
    setDescription("");
    setError(null);
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-6">
      <h3 className="text-white font-semibold text-lg mb-4">
        {mode === "create" ? "Создать кафе" : "Редактировать кафе"}
      </h3>

      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Name field */}
        <div>
          <label htmlFor="cafe-name" className="block text-white text-sm font-medium mb-2">
            Название <span className="text-red-400">*</span>
          </label>
          <input
            id="cafe-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Например: Кафе на Пушкина"
            required
            className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 placeholder-gray-400 focus:outline-none focus:border-[#A020F0] focus:ring-1 focus:ring-[#A020F0] transition"
          />
        </div>

        {/* Description field */}
        <div>
          <label htmlFor="cafe-description" className="block text-white text-sm font-medium mb-2">
            Описание
          </label>
          <textarea
            id="cafe-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Краткое описание кафе (опционально)"
            rows={3}
            className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 placeholder-gray-400 focus:outline-none focus:border-[#A020F0] focus:ring-1 focus:ring-[#A020F0] transition resize-none"
          />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3 mt-6">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 px-4 py-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50"
        >
          {isSubmitting ? "Сохранение..." : mode === "create" ? "Создать" : "Сохранить"}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={handleCancelClick}
            disabled={isSubmitting}
            className="px-4 py-2 bg-white/10 text-gray-300 font-medium border border-white/20 rounded-lg hover:bg-white/20 transition disabled:opacity-50"
          >
            Отмена
          </button>
        )}
      </div>
    </form>
  );
};

export default CafeForm;
