import React from "react";
import { FaLocationArrow } from "react-icons/fa";

interface ActionButtonsProps {
  onGetLocation: () => void;
  isGettingLocation: boolean;
  onToggleSavedAddresses: () => void;
  showSavedAddresses: boolean;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  onGetLocation,
  isGettingLocation,
  onToggleSavedAddresses,
  showSavedAddresses
}) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
    <button
      onClick={onGetLocation}
      disabled={isGettingLocation}
      className="flex items-center justify-center gap-3 px-4 py-3 bg-gradient-to-r from-[#8B23CB]/40 to-[#A020F0]/40 border border-white/10 rounded-xl hover:opacity-90 transition disabled:opacity-50"
    >
      <FaLocationArrow className={`text-white ${isGettingLocation ? 'animate-pulse' : ''}`} />
      <span className="font-semibold text-white">
        {isGettingLocation ? "Определяем..." : "Моё местоположение"}
      </span>
    </button>
    <button
      onClick={onToggleSavedAddresses}
      className="flex items-center justify-center gap-3 px-4 py-3 bg-gradient-to-r from-[#786F9C]/40 to-[#7B6F9C]/40 border border-white/10 rounded-xl hover:opacity-90 transition"
    >
      <span className="font-semibold text-white">
        {showSavedAddresses ? "Скрыть" : "Сохранённые"}
      </span>
    </button>
  </div>
);

export default ActionButtons;
