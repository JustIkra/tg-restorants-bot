"use client";

import { useState } from "react";
import { Combo } from "@/lib/api/types";
import { FaTimes } from "react-icons/fa";

const CATEGORIES = [
  { id: "soup", label: "Первое" },
  { id: "salad", label: "Салат" },
  { id: "main", label: "Второе" },
  { id: "extra", label: "Десерт" },
];

interface ComboFormProps {
  mode: "create" | "edit";
  cafeId: number;
  initialData?: Combo;
  onSubmit: (data: { name: string; categories: string[]; price: number }) => void;
  onCancel: () => void;
}

export default function ComboForm({ mode, cafeId, initialData, onSubmit, onCancel }: ComboFormProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [selectedCategories, setSelectedCategories] = useState<string[]>(initialData?.categories || []);
  const [price, setPrice] = useState(initialData?.price?.toString() || "");

  const handleCategoryToggle = (categoryId: string) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((c) => c !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || selectedCategories.length === 0 || !price) {
      alert("Заполните все поля");
      return;
    }
    onSubmit({
      name: name.trim(),
      categories: selectedCategories,
      price: parseFloat(price),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">
            {mode === "create" ? "Создать комбо" : "Редактировать комбо"}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-white transition"
          >
            <FaTimes size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Название
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
              placeholder="Например: Салат + Суп"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Категории
            </label>
            <div className="space-y-2">
              {CATEGORIES.map((category) => (
                <label
                  key={category.id}
                  className="flex items-center space-x-3 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category.id)}
                    onChange={() => handleCategoryToggle(category.id)}
                    className="w-5 h-5 rounded border-white/20 bg-white/10 text-[#A020F0] focus:ring-[#A020F0]"
                  />
                  <span className="text-white">{category.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Цена (₽)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
              placeholder="450.00"
            />
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              type="submit"
              className="flex-1 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white font-semibold py-3 rounded-lg hover:opacity-90 transition"
            >
              {mode === "create" ? "Создать" : "Сохранить"}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-white/10 text-white font-semibold py-3 rounded-lg hover:bg-white/20 transition"
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
