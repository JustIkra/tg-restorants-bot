"use client";

import { useState } from "react";
import { MenuItem } from "@/lib/api/types";
import { FaTimes } from "react-icons/fa";

const CATEGORIES = [
  { id: "soup", label: "Первое" },
  { id: "salad", label: "Салат" },
  { id: "main", label: "Второе" },
  { id: "extra", label: "Дополнительно" },
];

interface MenuItemFormProps {
  mode: "create" | "edit";
  cafeId: number;
  initialData?: MenuItem;
  onSubmit: (data: { name: string; description?: string; category: string; price?: string }) => void;
  onCancel: () => void;
}

export default function MenuItemForm({ mode, cafeId, initialData, onSubmit, onCancel }: MenuItemFormProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [category, setCategory] = useState(initialData?.category || "soup");
  const [price, setPrice] = useState(initialData?.price?.toString() || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !category) {
      alert("Заполните обязательные поля");
      return;
    }

    // Price is required only for "extra" category
    if (category === "extra" && !price) {
      alert("Для категории 'Дополнительно' необходимо указать цену");
      return;
    }

    onSubmit({
      name: name.trim(),
      description: description.trim() || undefined,
      category,
      price: category === "extra" && price ? price : undefined,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">
            {mode === "create" ? "Создать блюдо" : "Редактировать блюдо"}
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
              placeholder="Например: Борщ с курицей"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Описание
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0] resize-none"
              placeholder="Необязательно"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Категория
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.id} value={cat.id} className="bg-gray-800">
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {category === "extra" && (
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
                placeholder="50.00"
              />
            </div>
          )}

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
