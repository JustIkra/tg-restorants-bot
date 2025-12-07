"use client";

import { useState } from "react";
import { useCafes, useCombos, useMenu, useCreateCombo, useUpdateCombo, useDeleteCombo, useCreateMenuItem, useUpdateMenuItem, useDeleteMenuItem } from "@/lib/api/hooks";
import { Combo, MenuItem } from "@/lib/api/types";
import { FaPlus, FaSpinner } from "react-icons/fa";
import ComboForm from "./ComboForm";
import MenuItemForm from "./MenuItemForm";
import { useConfirm } from "@/hooks/useConfirm";
import { useAlert } from "@/components/UI/CustomAlert";

const CATEGORY_LABELS: Record<string, string> = {
  soup: "Первое",
  salad: "Салат",
  main: "Второе",
  extra: "Дополнительно",
};

export default function MenuManager() {
  const { confirm } = useConfirm();
  const { showAlert, AlertComponent } = useAlert();
  const [selectedCafeId, setSelectedCafeId] = useState<number | null>(null);
  const [showComboForm, setShowComboForm] = useState(false);
  const [showMenuItemForm, setShowMenuItemForm] = useState(false);
  const [editingCombo, setEditingCombo] = useState<Combo | null>(null);
  const [editingMenuItem, setEditingMenuItem] = useState<MenuItem | null>(null);

  const { data: cafes, isLoading: cafesLoading } = useCafes(true, false);
  const { data: combos, isLoading: combosLoading, mutate: mutateCombos } = useCombos(selectedCafeId, false);
  const { data: menuItems, isLoading: menuLoading, mutate: mutateMenu } = useMenu(selectedCafeId, undefined, false);

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
      showAlert("Ошибка при создании комбо", "error");
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
      showAlert("Ошибка при обновлении комбо", "error");
      console.error(error);
    }
  };

  const handleDeleteCombo = async (comboId: number) => {
    if (!selectedCafeId) return;

    const confirmed = await confirm({
      title: "Удаление комбо",
      message: "Вы уверены, что хотите удалить это комбо?",
      confirmText: "Удалить",
      cancelText: "Отмена",
    });

    if (!confirmed) return;

    try {
      await deleteCombo(selectedCafeId, comboId);
      mutateCombos();
    } catch (error) {
      showAlert("Ошибка при удалении комбо", "error");
      console.error(error);
    }
  };

  const handleToggleComboAvailability = async (combo: Combo) => {
    if (!selectedCafeId) return;
    try {
      await updateCombo(selectedCafeId, combo.id, { is_available: !combo.is_available });
      mutateCombos();
    } catch (error) {
      showAlert("Ошибка при изменении доступности", "error");
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
      showAlert("Ошибка при создании блюда", "error");
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
      showAlert("Ошибка при обновлении блюда", "error");
      console.error(error);
    }
  };

  const handleDeleteMenuItem = async (itemId: number) => {
    if (!selectedCafeId) return;

    const confirmed = await confirm({
      title: "Удаление блюда",
      message: "Вы уверены, что хотите удалить это блюдо?",
      confirmText: "Удалить",
      cancelText: "Отмена",
    });

    if (!confirmed) return;

    try {
      await deleteMenuItem(selectedCafeId, itemId);
      mutateMenu();
    } catch (error) {
      showAlert("Ошибка при удалении блюда", "error");
      console.error(error);
    }
  };

  const handleToggleMenuItemAvailability = async (item: MenuItem) => {
    if (!selectedCafeId) return;
    try {
      await updateMenuItem(selectedCafeId, item.id, { is_available: !item.is_available });
      mutateMenu();
    } catch (error) {
      showAlert("Ошибка при изменении доступности", "error");
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
    <>
      <AlertComponent />
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
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="text-white font-semibold">{combo.name}</h4>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            combo.is_available
                              ? "bg-green-500/20 text-green-400"
                              : "bg-red-500/20 text-red-400"
                          }`}
                        >
                          {combo.is_available ? "Доступно" : "Недоступно"}
                        </span>
                      </div>
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
                    <div className="flex flex-col gap-2 ml-4 flex-shrink-0">
                      <button
                        onClick={() => setEditingCombo(combo)}
                        className="px-3 py-1.5 text-sm rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 active:bg-blue-500/40 disabled:opacity-50"
                      >
                        Редактировать
                      </button>
                      <button
                        onClick={() => handleToggleComboAvailability(combo)}
                        className={`px-3 py-1.5 text-sm rounded-lg disabled:opacity-50 ${
                          combo.is_available
                            ? "bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 active:bg-yellow-500/40"
                            : "bg-green-500/20 text-green-400 hover:bg-green-500/30 active:bg-green-500/40"
                        }`}
                      >
                        {combo.is_available ? "Деактивировать" : "Активировать"}
                      </button>
                      <button
                        onClick={() => handleDeleteCombo(combo.id)}
                        className="px-3 py-1.5 text-sm rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 active:bg-red-500/40 disabled:opacity-50"
                      >
                        Удалить
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
                            <div className="flex items-center gap-3 mb-1">
                              <h5 className="text-white font-semibold">{item.name}</h5>
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium ${
                                  item.is_available
                                    ? "bg-green-500/20 text-green-400"
                                    : "bg-red-500/20 text-red-400"
                                }`}
                              >
                                {item.is_available ? "Доступно" : "Недоступно"}
                              </span>
                            </div>
                            {item.description && (
                              <p className="text-gray-400 text-sm mt-1">{item.description}</p>
                            )}
                            {item.price !== null && (
                              <p className="text-[#A020F0] font-semibold mt-2">{item.price} ₽</p>
                            )}
                          </div>
                          <div className="flex flex-col gap-2 ml-4 flex-shrink-0">
                            <button
                              onClick={() => setEditingMenuItem(item)}
                              className="px-3 py-1.5 text-sm rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 active:bg-blue-500/40 disabled:opacity-50"
                            >
                              Редактировать
                            </button>
                            <button
                              onClick={() => handleToggleMenuItemAvailability(item)}
                              className={`px-3 py-1.5 text-sm rounded-lg disabled:opacity-50 ${
                                item.is_available
                                  ? "bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 active:bg-yellow-500/40"
                                  : "bg-green-500/20 text-green-400 hover:bg-green-500/30 active:bg-green-500/40"
                              }`}
                            >
                              {item.is_available ? "Деактивировать" : "Активировать"}
                            </button>
                            <button
                              onClick={() => handleDeleteMenuItem(item.id)}
                              className="px-3 py-1.5 text-sm rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 active:bg-red-500/40 disabled:opacity-50"
                            >
                              Удалить
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
    </>
  );
}
