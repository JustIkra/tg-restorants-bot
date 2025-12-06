"use client";

import { useState } from "react";
import { useCafes, useCombos, useMenu, useCreateCombo, useUpdateCombo, useDeleteCombo, useCreateMenuItem, useUpdateMenuItem, useDeleteMenuItem } from "@/lib/api/hooks";
import { Combo, MenuItem } from "@/lib/api/types";
import { FaPlus, FaEdit, FaTrash, FaSpinner, FaToggleOn, FaToggleOff } from "react-icons/fa";
import ComboForm from "./ComboForm";
import MenuItemForm from "./MenuItemForm";

const CATEGORY_LABELS: Record<string, string> = {
  soup: "Первое",
  salad: "Салат",
  main: "Второе",
  extra: "Дополнительно",
};

export default function MenuManager() {
  const [selectedCafeId, setSelectedCafeId] = useState<number | null>(null);
  const [showComboForm, setShowComboForm] = useState(false);
  const [showMenuItemForm, setShowMenuItemForm] = useState(false);
  const [editingCombo, setEditingCombo] = useState<Combo | null>(null);
  const [editingMenuItem, setEditingMenuItem] = useState<MenuItem | null>(null);

  const { data: cafes, isLoading: cafesLoading } = useCafes(false);
  const { data: combos, isLoading: combosLoading, mutate: mutateCombos } = useCombos(selectedCafeId);
  const { data: menuItems, isLoading: menuLoading, mutate: mutateMenu } = useMenu(selectedCafeId);

  const { createCombo } = useCreateCombo();
  const { updateCombo } = useUpdateCombo();
  const { deleteCombo } = useDeleteCombo();
  const { createMenuItem } = useCreateMenuItem();
  const { updateMenuItem } = useUpdateMenuItem();
  const { deleteMenuItem } = useDeleteMenuItem();

  // Combo handlers
  const handleCreateCombo = async (data: { name: string; categories: string[]; price: number }) => {
    if (!selectedCafeId) return;
    try {
      await createCombo(selectedCafeId, data);
      mutateCombos();
      setShowComboForm(false);
    } catch (error) {
      alert("Ошибка при создании комбо");
      console.error(error);
    }
  };

  const handleUpdateCombo = async (data: { name: string; categories: string[]; price: number }) => {
    if (!selectedCafeId || !editingCombo) return;
    try {
      await updateCombo(selectedCafeId, editingCombo.id, data);
      mutateCombos();
      setEditingCombo(null);
    } catch (error) {
      alert("Ошибка при обновлении комбо");
      console.error(error);
    }
  };

  const handleDeleteCombo = async (comboId: number) => {
    if (!selectedCafeId) return;
    if (!confirm("Удалить комбо?")) return;
    try {
      await deleteCombo(selectedCafeId, comboId);
      mutateCombos();
    } catch (error) {
      alert("Ошибка при удалении комбо");
      console.error(error);
    }
  };

  const handleToggleComboAvailability = async (combo: Combo) => {
    if (!selectedCafeId) return;
    try {
      await updateCombo(selectedCafeId, combo.id, { is_available: !combo.is_available });
      mutateCombos();
    } catch (error) {
      alert("Ошибка при изменении доступности");
      console.error(error);
    }
  };

  // Menu item handlers
  const handleCreateMenuItem = async (formData: { name: string; description?: string; category: string; price?: string }) => {
    if (!selectedCafeId) return;
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        price: formData.price ? parseFloat(formData.price) : undefined,
      };
      await createMenuItem(selectedCafeId, data);
      mutateMenu();
      setShowMenuItemForm(false);
    } catch (error) {
      alert("Ошибка при создании блюда");
      console.error(error);
    }
  };

  const handleUpdateMenuItem = async (formData: { name: string; description?: string; category: string; price?: string }) => {
    if (!selectedCafeId || !editingMenuItem) return;
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        price: formData.price ? parseFloat(formData.price) : undefined,
      };
      await updateMenuItem(selectedCafeId, editingMenuItem.id, data);
      mutateMenu();
      setEditingMenuItem(null);
    } catch (error) {
      alert("Ошибка при обновлении блюда");
      console.error(error);
    }
  };

  const handleDeleteMenuItem = async (itemId: number) => {
    if (!selectedCafeId) return;
    if (!confirm("Удалить блюдо?")) return;
    try {
      await deleteMenuItem(selectedCafeId, itemId);
      mutateMenu();
    } catch (error) {
      alert("Ошибка при удалении блюда");
      console.error(error);
    }
  };

  const handleToggleMenuItemAvailability = async (item: MenuItem) => {
    if (!selectedCafeId) return;
    try {
      await updateMenuItem(selectedCafeId, item.id, { is_available: !item.is_available });
      mutateMenu();
    } catch (error) {
      alert("Ошибка при изменении доступности");
      console.error(error);
    }
  };

  // Group menu items by category
  const groupedMenuItems = menuItems?.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, MenuItem[]>);

  return (
    <div className="space-y-6">
      {/* Cafe selector */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Выберите кафе
        </label>
        <select
          value={selectedCafeId || ""}
          onChange={(e) => setSelectedCafeId(e.target.value ? Number(e.target.value) : null)}
          className="w-full bg-white/10 border border-white/20 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#A020F0]"
        >
          <option value="" className="bg-gray-800">Выберите кафе</option>
          {cafes?.map(cafe => (
            <option key={cafe.id} value={cafe.id} className="bg-gray-800">
              {cafe.name}
            </option>
          ))}
        </select>
      </div>

      {selectedCafeId && (
        <>
          {/* Combos section */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Комбо-наборы</h3>
              <button
                onClick={() => setShowComboForm(true)}
                className="flex items-center space-x-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white px-4 py-2 rounded-lg hover:opacity-90 transition"
              >
                <FaPlus />
                <span>Добавить</span>
              </button>
            </div>

            {combosLoading ? (
              <div className="flex justify-center py-8">
                <FaSpinner className="animate-spin text-[#A020F0]" size={32} />
              </div>
            ) : combos && combos.length > 0 ? (
              <div className="space-y-3">
                {combos.map(combo => (
                  <div
                    key={combo.id}
                    className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 flex justify-between items-start"
                  >
                    <div className="flex-1">
                      <h4 className="text-white font-semibold">{combo.name}</h4>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {combo.categories.map(cat => (
                          <span
                            key={cat}
                            className="bg-white/10 text-gray-300 px-2 py-1 rounded text-sm"
                          >
                            {CATEGORY_LABELS[cat] || cat}
                          </span>
                        ))}
                      </div>
                      <p className="text-[#A020F0] font-semibold mt-2">{combo.price} ₽</p>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => handleToggleComboAvailability(combo)}
                        className="text-gray-400 hover:text-white transition"
                        title={combo.is_available ? "Отключить" : "Включить"}
                      >
                        {combo.is_available ? (
                          <FaToggleOn size={24} className="text-green-500" />
                        ) : (
                          <FaToggleOff size={24} className="text-gray-500" />
                        )}
                      </button>
                      <button
                        onClick={() => setEditingCombo(combo)}
                        className="text-gray-400 hover:text-white transition"
                      >
                        <FaEdit size={20} />
                      </button>
                      <button
                        onClick={() => handleDeleteCombo(combo.id)}
                        className="text-gray-400 hover:text-red-500 transition"
                      >
                        <FaTrash size={20} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Нет комбо-наборов</p>
            )}
          </div>

          {/* Menu items section */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Блюда</h3>
              <button
                onClick={() => setShowMenuItemForm(true)}
                className="flex items-center space-x-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] text-white px-4 py-2 rounded-lg hover:opacity-90 transition"
              >
                <FaPlus />
                <span>Добавить</span>
              </button>
            </div>

            {menuLoading ? (
              <div className="flex justify-center py-8">
                <FaSpinner className="animate-spin text-[#A020F0]" size={32} />
              </div>
            ) : groupedMenuItems && Object.keys(groupedMenuItems).length > 0 ? (
              <div className="space-y-6">
                {Object.entries(groupedMenuItems).map(([category, items]) => (
                  <div key={category}>
                    <h4 className="text-white font-semibold mb-3">
                      {CATEGORY_LABELS[category] || category}
                    </h4>
                    <div className="space-y-3">
                      {items.map(item => (
                        <div
                          key={item.id}
                          className="bg-white/5 backdrop-blur-md border border-white/10 rounded-lg p-4 flex justify-between items-start"
                        >
                          <div className="flex-1">
                            <h5 className="text-white font-semibold">{item.name}</h5>
                            {item.description && (
                              <p className="text-gray-400 text-sm mt-1">{item.description}</p>
                            )}
                            {item.price !== null && (
                              <p className="text-[#A020F0] font-semibold mt-2">{item.price} ₽</p>
                            )}
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <button
                              onClick={() => handleToggleMenuItemAvailability(item)}
                              className="text-gray-400 hover:text-white transition"
                              title={item.is_available ? "Отключить" : "Включить"}
                            >
                              {item.is_available ? (
                                <FaToggleOn size={24} className="text-green-500" />
                              ) : (
                                <FaToggleOff size={24} className="text-gray-500" />
                              )}
                            </button>
                            <button
                              onClick={() => setEditingMenuItem(item)}
                              className="text-gray-400 hover:text-white transition"
                            >
                              <FaEdit size={20} />
                            </button>
                            <button
                              onClick={() => handleDeleteMenuItem(item.id)}
                              className="text-gray-400 hover:text-red-500 transition"
                            >
                              <FaTrash size={20} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Нет блюд</p>
            )}
          </div>
        </>
      )}

      {/* Forms modals */}
      {showComboForm && selectedCafeId && (
        <ComboForm
          mode="create"
          cafeId={selectedCafeId}
          onSubmit={handleCreateCombo}
          onCancel={() => setShowComboForm(false)}
        />
      )}

      {editingCombo && selectedCafeId && (
        <ComboForm
          mode="edit"
          cafeId={selectedCafeId}
          initialData={editingCombo}
          onSubmit={handleUpdateCombo}
          onCancel={() => setEditingCombo(null)}
        />
      )}

      {showMenuItemForm && selectedCafeId && (
        <MenuItemForm
          mode="create"
          cafeId={selectedCafeId}
          onSubmit={handleCreateMenuItem}
          onCancel={() => setShowMenuItemForm(false)}
        />
      )}

      {editingMenuItem && selectedCafeId && (
        <MenuItemForm
          mode="edit"
          cafeId={selectedCafeId}
          initialData={editingMenuItem}
          onSubmit={handleUpdateMenuItem}
          onCancel={() => setEditingMenuItem(null)}
        />
      )}
    </div>
  );
}
