import React from "react";
import { Combo } from "@/lib/api/types";

interface ComboSelectorProps {
  combos: Combo[];
  selectedComboId: number | null;
  onComboSelect: (id: number) => void;
}

const ComboSelector: React.FC<ComboSelectorProps> = ({
  combos,
  selectedComboId,
  onComboSelect
}) => (
  <div className="flex gap-3 overflow-x-auto flex-nowrap pl-[17px] pr-6 scrollbar-hide">
    {combos.map((combo) => (
      <button
        key={combo.id}
        onClick={() => onComboSelect(combo.id)}
        className="relative px-6 py-4 transition-all duration-500 overflow-hidden flex-shrink-0 group min-w-[160px]"
        disabled={!combo.is_available}
      >
        <div
          className={`absolute inset-0 rounded-xl transition-all duration-500 ${
            selectedComboId === combo.id
              ? 'bg-gradient-to-r from-[#8B23CB] via-[#A020F0] to-[#7723B6]'
              : combo.is_available
                ? 'bg-[#7B6F9C] opacity-30'
                : 'bg-gray-600 opacity-20'
          }`}
        />
        <div className="absolute inset-0 overflow-hidden rounded-xl">
          <div
            className={`absolute inset-0 bg-gradient-to-r from-[#8B23CB] via-[#A020F0] to-[#8B23CB] \
                      bg-[length:200%_100%] rounded-xl transition-opacity duration-1000\
                      ${selectedComboId === combo.id ? 'opacity-100' : combo.is_available ? 'opacity-0 group-hover:opacity-100' : 'opacity-0'}`}
            style={{
              animation: selectedComboId === combo.id ? 'gradientShift 3s ease-in-out infinite' : 'none'
            }}
          />
        </div>
        <div className="relative flex flex-col items-start gap-1">
          <span
            className={`font-medium text-sm whitespace-nowrap transition-colors duration-300\
                      ${selectedComboId === combo.id
                        ? 'text-white font-semibold'
                        : combo.is_available
                          ? 'text-gray-300 group-hover:text-white'
                          : 'text-gray-500'
                      }`}
          >
            {combo.name}
          </span>
          <span
            className={`text-xs font-semibold transition-colors duration-300\
                      ${selectedComboId === combo.id
                        ? 'text-white'
                        : combo.is_available
                          ? 'text-[#A020F0] group-hover:text-white'
                          : 'text-gray-600'
                      }`}
          >
            {combo.price} ₽
          </span>
        </div>
      </button>
    ))}
  </div>
);

export default ComboSelector;
