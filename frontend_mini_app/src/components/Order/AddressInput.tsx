import React from "react";
import { FaMapMarkerAlt, FaSearch } from "react-icons/fa";

interface AddressInputProps {
  address: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onManualSearch: () => void;
  addressInputRef: React.RefObject<HTMLInputElement>;
  isLoadingSuggestions: boolean;
  showSuggestions: boolean;
  addressSuggestions: {title: string, subtitle: string, fullAddress: string}[];
  onSelectSuggestion: (fullAddress: string) => void;
}

const AddressInput: React.FC<AddressInputProps> = ({
  address,
  onChange,
  onManualSearch,
  addressInputRef,
  isLoadingSuggestions,
  showSuggestions,
  addressSuggestions,
  onSelectSuggestion
}) => (
  <div className="relative">
    <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
      <FaMapMarkerAlt className="text-white text-xl opacity-90 flex-shrink-0" />
      <input
        ref={addressInputRef}
        type="text"
        value={address}
        onChange={onChange}
        onFocus={() => address.length >= 2 && showSuggestions}
        className="font-semibold text-white text-lg bg-transparent border-none w-full focus:outline-none focus:ring-0 placeholder-white/60"
        placeholder="Начните вводить адрес..."
      />
      <button
        onClick={onManualSearch}
        disabled={address.length < 2 || isLoadingSuggestions}
        className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition disabled:opacity-30"
        title="Поиск адреса"
      >
        <FaSearch className="text-white" />
      </button>
    </div>
    {isLoadingSuggestions && (
      <div className="absolute right-14 top-1/2 -translate-y-1/2">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
      </div>
    )}
    {showSuggestions && addressSuggestions.length > 0 && (
      <div className="absolute z-20 w-full mt-1 bg-[#1a153d] border border-white/20 rounded-lg shadow-2xl overflow-hidden">
        <div className="p-2 bg-gradient-to-r from-[#8B23CB]/20 to-[#A020F0]/20 border-b border-white/10">
          <p className="text-white text-sm font-medium">Выберите адрес:</p>
        </div>
        <div className="max-h-48 overflow-y-auto">
          {addressSuggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSelectSuggestion(suggestion.fullAddress)}
              className="w-full p-3 text-left hover:bg-white/10 border-b border-white/5 last:border-b-0 transition duration-150"
            >
              <div className="flex flex-col">
                <span className="text-white font-medium text-sm">{suggestion.title}</span>
                {suggestion.subtitle && (
                  <span className="text-white/70 text-xs mt-0.5">{suggestion.subtitle}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    )}
  </div>
);

export default AddressInput;
