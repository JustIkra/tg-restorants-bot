import React from "react";
import { FaClock } from "react-icons/fa";

interface DeliveryTimeSelectorProps {
  deliveryTime: string;
  setDeliveryTime: (value: string) => void;
  showTimeDropdown: boolean;
  setShowTimeDropdown: (value: boolean) => void;
  timeOptions: { value: string; label: string; icon: string }[];
  timeDropdownRef: React.RefObject<HTMLDivElement | null>;
}

const DeliveryTimeSelector: React.FC<DeliveryTimeSelectorProps> = ({
  deliveryTime,
  setDeliveryTime,
  showTimeDropdown,
  setShowTimeDropdown,
  timeOptions,
  timeDropdownRef
}) => (
  <div className="relative" ref={timeDropdownRef}>
    <button
      onClick={() => setShowTimeDropdown(!showTimeDropdown)}
      className="flex items-center justify-between w-full gap-3 p-4 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition cursor-pointer"
    >
      <div className="flex items-center gap-3">
        <FaClock className="text-white text-xl opacity-90 flex-shrink-0" />
        <span className="font-semibold text-white text-lg">
          {deliveryTime}
        </span>
      </div>
      <svg 
        className={`text-white/70 transition-transform duration-200 ${showTimeDropdown ? 'rotate-180' : ''}`} 
        width="20" 
        height="20" 
        viewBox="0 0 20 20" 
        fill="currentColor"
      >
        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    </button>
    {showTimeDropdown && (
      <div className="absolute z-20 w-full mt-2 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl overflow-hidden">
        <div className="p-2 bg-gradient-to-r from-[#8B23CB]/20 to-[#A020F0]/20 border-b border-white/10">
          <p className="text-white text-sm font-medium">Выберите время:</p>
        </div>
        <div className="max-h-48 overflow-y-auto">
          {timeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                setDeliveryTime(option.value);
                setShowTimeDropdown(false);
              }}
              className={`w-full p-3 text-left hover:bg-white/10 border-b border-white/5 last:border-b-0 transition duration-150 ${
                deliveryTime === option.value 
                  ? 'bg-gradient-to-r from-[#8B23CB]/20 to-[#A020F0]/20' 
                  : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="text-white/80 text-sm">{option.icon}</div>
                <div className="flex-1">
                  <span className={`font-medium text-sm ${
                    deliveryTime === option.value ? 'text-white' : 'text-white/90'
                  }`}>
                    {option.label}
                  </span>
                </div>
                {deliveryTime === option.value && (
                  <svg className="text-white w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    )}
  </div>
);

export default DeliveryTimeSelector;
